import logging
import os
import sys
import unicodedata
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from gettext import translation
from hashlib import sha1
from threading import local
from typing import Any, TypeVar, cast

from babel import Locale
from banal import ensure_list
from normality import predict_encoding, stringify
from normality.cleaning import remove_unsafe_chars
from rigour.env import ENCODING

MEGABYTE = 1024 * 1024
PROP_VALUE_MAX = 30 * MEGABYTE
ENTITY_VALUE_MAX = 50 * MEGABYTE
HASH_ENCODING = "utf-8"
DEFAULT_LOCALE = "en"
ENTITY_ID_LEN = 200

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

PathLike = str | os.PathLike[str]
i18n_path = os.path.join(os.path.dirname(__file__), "translations")
state = local()
log = logging.getLogger(__name__)


def gettext(*args: str | None, **kwargs: dict[str, str]) -> str:
    if not hasattr(state, "translation"):
        set_model_locale(Locale.parse(DEFAULT_LOCALE))
    return cast(str, state.translation.gettext(*args, **kwargs))


def defer(text: str) -> str:
    return text


def const(text: str) -> str:
    """Convert the given text to a runtime constant."""
    return sys.intern(text.strip())


def set_model_locale(locale: Locale) -> None:
    state.locale = locale
    state.translation = translation(
        "followthemoney", i18n_path, [str(locale)], fallback=True
    )


def get_locale() -> Locale:
    if not hasattr(state, "locale"):
        return Locale.parse(DEFAULT_LOCALE)
    return Locale.parse(state.locale)


def _clean_text(text: str) -> str | None:
    try:
        text = unicodedata.normalize("NFC", text)
    except Exception as ex:  # noqa: BLE001
        log.warning("Cannot NFC text: %s", ex)
        return None
    text = remove_unsafe_chars(text)
    text = text.strip()
    if len(text) == 0:
        # XXX: is this really a good idea?
        return None
    return text


def sanitize_text(value: Any, encoding: str | None = None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    elif isinstance(value, float):
        # Avoid trailing zeros and limit to 3 decimal places:
        return format(value, ".3f").rstrip("0").rstrip(".")
    elif isinstance(value, Decimal):
        return value.to_eng_string()
    elif isinstance(value, bytes):
        if encoding is None:
            encoding = predict_encoding(value, default=ENCODING)
        value = value.decode(encoding, "replace")
        return _clean_text(value)
    return _clean_text(str(value))


def key_bytes(key: Any) -> bytes:
    """Convert the given data to a value appropriate for hashing."""
    if isinstance(key, bytes):
        return key
    text = stringify(key)
    if text is None:
        return b""
    return text.encode(ENCODING)


def join_text(*parts: Any, sep: str = " ") -> str | None:
    """Join all the non-null arguments using sep."""
    texts: list[str] = []
    for part in parts:
        text = stringify(part)
        if text is not None:
            texts.append(text)
    if len(texts) == 0:
        return None
    return sep.join(texts)


def const_case(text: str) -> str:
    """Convert the given text to a constant case."""
    return text.upper().replace(" ", "_")


def get_entity_id(obj: Any) -> str | None:
    """Given an entity-ish object, try to get the ID."""
    if isinstance(obj, Mapping):
        obj = obj.get("id")
    else:
        try:
            obj = obj.id
        except AttributeError:
            pass
    return stringify(obj)


def make_entity_id(*parts: Any, key_prefix: str | None = None) -> str | None:
    digest = sha1()
    if key_prefix:
        digest.update(key_bytes(key_prefix))
    base = digest.digest()
    for part in parts:
        digest.update(key_bytes(part))
    if digest.digest() == base:
        return None
    return digest.hexdigest()


def merge_context(left: dict[K, V], right: dict[K, V]) -> dict[K, list[V]]:
    """When merging two entities, make lists of all the duplicate context
    keys."""
    combined = {}
    keys = [*left.keys(), *right.keys()]
    for key in set(keys):
        if key in ("caption",):
            continue
        lval: list[V] = [i for i in ensure_list(left.get(key)) if i is not None]
        rval: list[V] = [i for i in ensure_list(right.get(key)) if i is not None]
        combined[key] = list(dict.fromkeys([*lval, *rval]))
    return combined


def dampen(short: int, long: int, text: str) -> float:
    length = len(text) - short
    baseline = max(1.0, (long - short))
    return max(0, min(1.0, (length / baseline)))


def shortest(*texts: str) -> str:
    return min(texts, key=len)


def longest(*texts: str) -> str:
    return max(texts, key=len)

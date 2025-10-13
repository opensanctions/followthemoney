from typing import Any, Iterable, List, Mapping, Union
from datetime import datetime, date, timezone
import typing
from prefixdate import DatePrefix

from followthemoney.util import sanitize_text

if typing.TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy

Value = Union[str, int, float, bool, date, datetime, DatePrefix, None, "EntityProxy"]
Values = Union[Value, Iterable[Value]]


def string_list(value: Any, sanitize: bool = False) -> List[str]:
    """Convert a value - which may be a list or set - to a list of strings."""
    # This function is called in the inner loop of placing values into entities,
    # so it's unrolled to avoid the overhead of a comparatively heavy ops like
    # `isinstance`.
    if value is None:
        return []
    type_ = type(value)
    if type_ is str:
        if sanitize:
            value = sanitize_text(value)
            if value is None:
                return []
        return [value] if len(value) > 0 else []
    if type_ is int:
        return [str(value)]
    if type_ is float:
        return [f"{value:.2f}"]
    if type_ is bool:
        return ["true" if value else "false"]
    if type_ is date:
        return [value.isoformat()]
    if type_ is datetime:
        if value.tzinfo is not None:
            value = value.astimezone(tz=timezone.utc)
        return [value.isoformat()]
    if type_ is set or type_ is list or type_ is tuple:
        texts: List[str] = []
        for inner in value:
            texts.extend(string_list(inner, sanitize=sanitize))
        return texts
    if isinstance(value, DatePrefix):
        return [value.text] if value.text else []
    # EntityProxy
    try:
        return string_list(value.id, sanitize=sanitize)
    except AttributeError:
        pass
    # Entity dict
    if isinstance(value, Mapping):
        return string_list(value.get("id"), sanitize=sanitize)
    if isinstance(value, (str, bytes)):
        # Handle sub-classes of str, bytes - always sanitize
        text = sanitize_text(value)
        if text is None:
            return []
        return [text]
    if isinstance(value, Iterable):
        stexts: List[str] = []
        for inner in value:
            stexts.extend(string_list(inner, sanitize=sanitize))
        return stexts
    raise TypeError("Cannot convert %r to string list" % value)

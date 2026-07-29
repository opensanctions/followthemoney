from collections.abc import Generator
from typing import Any, TextIO

import yaml

Message = tuple[Any, Any, list[str], list[str]]


def extract_object(
    data: dict[str, Any], path: list[str]
) -> Generator[Message, None, None]:
    for key, value in data.items():
        subpath = path + [key]
        if isinstance(value, str):
            if key in ["label", "reverse", "description", "plural"]:
                comment = ".".join(subpath)
                yield (None, None, [value], [comment])
        if isinstance(value, dict):
            yield from extract_object(value, subpath)


def extract_yaml(
    fileobj: TextIO, keywords: Any, comment_tags: Any, options: Any
) -> Generator[Message, None, None]:
    data = yaml.safe_load(fileobj)
    return extract_object(data, [])

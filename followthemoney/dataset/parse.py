"""String query parser for the dataset filter DSL.

Parses compact string expressions like ``(#issuer.west|#list.sanction)-lt_fiu``
into a ``DatasetQuery`` that can be evaluated with ``evaluate_query``.

See https://followthemoney.tech/docs/metadata/#dataset-query-dsl for full
documentation and examples.
"""


from followthemoney.dataset.query import DatasetQuery
from followthemoney.exc import InvalidDatasetQuery

_LEAF_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.#"
)


class _Parser:
    """Recursive descent parser for the string query syntax."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def _skip_whitespace(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] == " ":
            self.pos += 1

    def _peek(self) -> str:
        self._skip_whitespace()
        if self.pos >= len(self.text):
            return ""
        return self.text[self.pos]

    def _consume(self, expected: str) -> None:
        self._skip_whitespace()
        if self.pos >= len(self.text) or self.text[self.pos] != expected:
            raise InvalidDatasetQuery(
                "Expected %r at position %d" % (expected, self.pos)
            )
        self.pos += 1

    def _parse_leaf(self) -> str:
        self._skip_whitespace()
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in _LEAF_CHARS:
            self.pos += 1
        if self.pos == start:
            raise InvalidDatasetQuery(
                "Expected identifier at position %d" % self.pos
            )
        return self.text[start : self.pos]

    def _parse_atom(self) -> DatasetQuery:
        if self._peek() == "(":
            self._consume("(")
            result = self._parse_or()
            self._consume(")")
            return result
        return self._parse_leaf()

    def _parse_and(self) -> DatasetQuery:
        items: list[DatasetQuery] = [self._parse_atom()]
        while self._peek() in ("&", "-"):
            op = self.text[self.pos]
            self.pos += 1
            atom = self._parse_atom()
            if op == "-":
                items.append({"not": atom})
            else:
                items.append(atom)
        if len(items) == 1:
            return items[0]
        return {"and": items}

    def _parse_or(self) -> DatasetQuery:
        items: list[DatasetQuery] = [self._parse_and()]
        while self._peek() == "|":
            self.pos += 1
            items.append(self._parse_and())
        if len(items) == 1:
            return items[0]
        return {"or": items}

    def parse(self) -> DatasetQuery:
        if len(self.text.strip()) == 0:
            raise InvalidDatasetQuery("Empty query string")
        result = self._parse_or()
        self._skip_whitespace()
        if self.pos < len(self.text):
            raise InvalidDatasetQuery(
                "Unexpected character %r at position %d"
                % (self.text[self.pos], self.pos)
            )
        return result


def parse_query(text: str) -> DatasetQuery:
    """Parse a string query into a DatasetQuery AST.

    Syntax: ``(#issuer.west|#list.sanction)-lt_fiu-#issuer.ru``

    Operators by precedence (high to low):
    - ``()`` grouping
    - ``&`` intersection, ``-`` subtraction (same precedence, left-to-right)
    - ``|`` union
    """
    return _Parser(text).parse()

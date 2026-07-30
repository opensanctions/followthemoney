import math
from collections.abc import Generator, Iterable
from itertools import islice, product

from normality import ascii_text
from rigour.names import (
    remove_person_prefixes,
    replace_org_types_compare,
    tokenize_name,
)
from rigour.territories import territories_intersect
from rigour.text.scripts import can_latinize

from followthemoney.exc import InvalidData
from followthemoney.proxy import EntityProxy
from followthemoney.schema import Schema
from followthemoney.types import registry
from followthemoney.types.common import PropertyType

# Compare weights come from the glm-bernouli model in followthemoney-predict
Weights = dict[PropertyType | None, float]
Scores = dict[PropertyType, float | None]
COMPARE_WEIGHTS: Weights = {
    registry.name: 12.275729155073371,
    registry.country: 1.0494517476987815,
    registry.date: 6.960245940274218,
    registry.identifier: 5.2209896558064175,
    registry.address: 6.456137299747168,
    registry.phone: 3.538892687331418,
    registry.email: 14.115925628770384,
    registry.url: 3.211995327345834,
    None: -11.91521189545115,
}


def compare_scores(left: EntityProxy, right: EntityProxy) -> Scores:
    """Compare two entities and return a match score for each property."""
    try:
        common = left.schema.model.common_schema(left.schema, right.schema)
    except InvalidData:
        return {}
    scores: Scores = {}
    left_inv = left.get_type_inverted(matchable=True)
    right_inv = right.get_type_inverted(matchable=True)
    left_groups = set(left_inv.keys())
    right_groups = set(right_inv.keys())
    for group_name in left_groups.intersection(right_groups):
        group = registry.groups[group_name]
        try:
            if group == registry.name:
                score = compare_names(common, left, right)
            elif group == registry.country:
                score = compare_countries(left, right)
            else:
                score = compare_group(
                    group, left_inv[group_name], right_inv[group_name]
                )
            scores[group] = score
        except ValueError:
            pass
    for group_name in left_groups.symmetric_difference(right_groups):
        group = registry.groups[group_name]
        scores[group] = None
    return scores


def _compare(scores: Scores, weights: Weights, n_std: int = 1) -> float:
    if len(scores) == 0 or not any(scores.values()):
        return 0.0
    prob = 0.0
    for field, weight in weights.items():
        if field:
            prob += weight * (scores.get(field) or 0.0)
        else:
            prob += weight
    return 1.0 / (1.0 + math.exp(-prob))


def compare(
    left: EntityProxy,
    right: EntityProxy,
    weights: Weights = COMPARE_WEIGHTS,
) -> float:
    """Compare two entities and return a match score."""
    if left.checksum == right.checksum:
        # Check if there is any data at all (ie any basis for making a decision),
        # if so, return a perfect match. This avoids marking two empty entities
        # as matching. Bit ambiguous, but practical.
        if len(left.properties) > 0 and len(right.properties) > 0:
            return 1.0
    scores = compare_scores(left, right)
    return _compare(scores, weights)


def _normalize_names(
    schema: Schema, names: Iterable[str]
) -> Generator[str, None, None]:
    """Generate a sequence of comparable names for an entity. This also
    generates a fingerprint, i.e. a version of the name where all tokens
    are sorted alphabetically, and some parts, such as company suffixes,
    have been removed."""
    seen = set()
    can_person = schema.is_a("LegalEntity") and not schema.is_a("Organization")
    can_org = schema.is_a("LegalEntity") and not schema.is_a("Person")
    for name in names:
        plain = name.lower().strip()
        if plain is not None and plain not in seen:
            seen.add(plain)
            yield plain
        if not can_org and not can_person:
            continue
        if can_person:
            name = remove_person_prefixes(name)
        if can_org:
            name = replace_org_types_compare(name)
        tokens = tokenize_name(name.lower())
        for token in tokens:
            if can_latinize(token):
                token = ascii_text(token) or token
        fp = " ".join(sorted(tokens))
        if fp is not None and len(fp) > 6 and fp not in seen:
            seen.add(fp)
            yield fp


def compare_group(
    group_type: PropertyType, left_values: list[str], right_values: list[str]
) -> float | None:
    if len(left_values) == 0 and len(right_values) == 0:
        raise ValueError("At least one proxy must have property type: %s", group_type)
    elif len(left_values) == 0 or len(right_values) == 0:
        return None
    return group_type.compare_sets(left_values, right_values)


def compare_names(
    common: Schema, left: EntityProxy, right: EntityProxy, max_names: int = 200
) -> float | None:
    result = 0.0
    left_list = list(islice(_normalize_names(common, left.names), max_names))
    right_list = list(islice(_normalize_names(common, right.names), max_names))
    if len(left_list) == 0 and len(right_list) == 0:
        raise ValueError("At least one proxy must have name properties")
    elif len(left_list) == 0 or len(right_list) == 0:
        return None
    for left_val, right_val in product(left_list, right_list):
        similarity = registry.name.compare(left_val, right_val)
        result = max(result, similarity)
        if result == 1.0:
            break
    result *= min(
        1.0, 2 ** (-len(left_list) * len(right_list) / (max_names * max_names))
    )
    return result


def compare_countries(left: EntityProxy, right: EntityProxy) -> float | None:
    left_countries = left.country_hints
    right_countries = right.country_hints
    if len(left_countries) == 0 and len(right_countries) == 0:
        raise ValueError("At least one proxy must have country properties")
    elif len(left_countries) == 0 or len(right_countries) == 0:
        return None
    intersection = territories_intersect(left_countries, right_countries)
    union = left_countries.union(right_countries)
    return len(intersection) / float(len(union))

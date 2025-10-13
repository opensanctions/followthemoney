# Entity matching

Much like collecting sports player cards, the great joy of well-defined entity data is to compare entities. Such comparisons can produce investigative leads when **cross-referencing a watchlist with a leaked dataset**, serve as a risk signal when screening customers against a sanctions list, or be part of a data factory that **deduplicates and integrates multiple instances** of the same logical entity.

Matching two entities is about managing a lack of information. Given that all decisions will be imperfect, matching is a matter of trade-offs: precision vs. recall, rule-based vs. statistical, etc. This is why FtM no longer attempts to define a universal method for entity matching. Instead, many systems exist within the ecosystem:

## Tools overview

* [followthemoney.compare.compare][]: a basic entity matching tool included in FollowTheMoney. It uses fixed weights to compute a score between two entities. Name comparison uses various normalisations before invoking [levenshtein_similarity][rigour.text.distance.levenshtein_similarity].
* [followthemoney-compare](https://github.com/alephdata/followthemoney-compare) is a standalone library using a compressed storage mechanism for name frequency analysis. 
* `nomenklatura.matching.RegressionV1` uses an array of features to train a logistic regression model using manually-made decisions from OpenSanctions' entity de-duplication.
* `nomenklatura.matching.LogicV1` uses a rule-based and fully deterministic scoring mechanism suitable for building a screening API.

Please contribute PRs to this page for any additional work done on FtM entity resolution.

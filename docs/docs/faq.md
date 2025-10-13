---
title: FAQ
---

# Frequently Asked Questions

## Is this data standard?

It's a *data vernacular*: a pragmatic convention used by data practitioners. The objective is to model the metaphors and concepts used in a conversation between three financial crime investigators at a hotel bar - 11pm, 3 beers. 

Data standards rely on formal governance to model a real-world domain with the ultimate goal of correctness. Given the breadth of the domain expressed in FtM schema (all of social and business relations on a global level), finding formal definitions for all of the domain's complexities would not be a realistic scope for a data standard.

## Why are all properties multi-valued?

First, multi-valued properties are a common thing in the FtM domain: companies have multiple official forms of their name, people can have multiple citizenships, names, and, more often than you'd think, ambiguous birth dates.

Recognizing this, FtM chooses the most consistent option of giving every property the option of being multi-valued. In practice, this has turned out to be convenient for data management and storage, while making the building of user interfaces a bit more challenging.

## Why not a property graph model?

Until Aleph 2.x, the FollowTheMoney system was based on edges and nodes, like you would expect if you're coming from a network analysis background. However, using that model forced us to make more and more random, opinionated, modelling decisions: what is the source of an ownership edge - the owner, or the asset? Is an email message a node or a hypergraph edge with many targets? What about a payment, or a customs declaration? Both often have more than two parties involved.

As soon as we started modelling FtM data as entities only, many of these semantics could actually be expressed, rather than implicitly fudged. There's still "funky" places, like familiar relations which would need to be modelled in much more detail to be unambiguous.

In general, property graphs are much more interpretative than we admit: they try to reduce the complexity of a domain into something targeted at answering a specific set of analytical queries. The entity-only model, on the other hand, remains a bit more descriptive.

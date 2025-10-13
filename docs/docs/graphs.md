---
title: Network Graphs
---

# Network Graphs

FollowTheMoney includes tooling to export data to a network graph. The FtM [command-line tool](cli.md) includes the following exporters:

* `ftm export-gexf` turns a stream of FtM entity into a GEXF (Graph EXchange Format) file suitable for import into NetworkX and Gephi.
* `ftm export-cypher` produces a stream of CYPHER commands that can be used to create a dataset in a Neo4J or Memgraph database.
* `ftm export-rdf` will produce a stream of RDF NTriples representing. FtM and RDF use the same fundamental graph model, so this representation is particularly faithful of the original semantics.

## How entities are translated to a graph

Below are some notes about the semantics of FtM as a graph, and how it might be converted to a (Neo4J-style) [property graph model](https://neo4j.com/blog/knowledge-graph/rdf-vs-property-graphs-knowledge-graphs/). This is how we’ve been thinking about it in the past, and we can change it, but it would almost certainly require adaptation of the FtM model and the complete re-generation of all Aleph data from scratch to do cleanly.

1. The normal case for what a link is in FtM is a property value (see [References](index.md#references)). When turning this into a property graph model, both the {{ schema_ref('Passport') }} and the {{ schema_ref('Person') }} become nodes, and the holder property becomes an edge with no attributes attached to it.

2. Sometimes we want to talk about the inverse of one of these edges. That’s why holder has an inverse, passports that is added to the {{ schema_ref('Person') }} schema. This is mostly used to store the labels that should be used to talk about the passports linked to a person. But it’s a stub that cannot be written.

3. The weakness of this model is that edges don’t have properties, whereas relationships in society always have metadata. Many of them are limited in time (hence {{ schema_ref('Interval') }}). So we added a work-around that allows some schema to sort of contract upon generating a property graph and turn into an edge, rather than a node. For example, {{ schema_ref('Membership') }}, {{ schema_ref('Ownership') }}. But it’s important to keep considering this a _special shortcut_, not the normal case for edges in FtM.

4. Because this is a work-around, it leaves the stub properties in a bit of an awkward place: it’s not clear conceptually if they refer to the original edge (e.g. a link between `Person.directorshipsDirector` → `Directorship.director`) or the contracted edge ({{ schema_ref('Person') }} → `directorOf` → {{ schema_ref('Organization') }}). It’s not been a problem in practice as we get the required metadata from the edge annotation of the contracted schema, but it’s a sort of weird “place”.

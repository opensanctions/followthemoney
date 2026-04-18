---
title: Namespacing
---

# Namespacing

Namespacing wraps every entity ID with a dataset-scoped HMAC signature, so that an ID generated in one dataset cannot be confused with — or used to fabricate a reference to — an entity in another.

The mechanism exists for systems that let clients supply their own entity IDs. Without namespacing, a user who can write to one dataset could produce an ID that collides with an entity in a second dataset and, depending on how the system resolves references, read or overwrite across that boundary. Systems like [OpenAleph](https://openaleph.org/) and [yente](https://yente.followthemoney.tech/) use it to isolate datasets from each other while still letting entities flow through a single shared index.

## The ID shape

A namespaced entity ID has two parts, joined by a dot:

```
entity_id.a40a29300ac6bb79dd2f911e77bbda7a3b502126
```

The first part is the bare ID the producer chose or generated (see [Generating unique keys](mappings.md#generating-unique-keys)). The second is a signature computed as `hmac_sha1(dataset_name, entity_id)`, where the HMAC key is the name or foreign ID of the dataset the entity belongs to.

## What the signature protects

The signature is a namespace discriminator applied by the host system at ingest. It works in concert with the host's authorization layer, not as a replacement for it.

- It prevents **accidental collision** in shared indexes. Two datasets that independently generate overlapping bare IDs can live in the same search index without their entities being mistaken for each other — the signed forms differ even when the bare IDs do not.
- It **re-anchors every reference to the current dataset at ingest**. [`apply()`][followthemoney.namespace.Namespace.apply] strips any existing signature before re-signing, so a client cannot submit an entity whose `owner` or `asset` property points across a dataset boundary. Whatever signature the client sends is discarded; the ingest pipeline re-signs every entity-typed property value with the receiving dataset's namespace. Cross-dataset references cannot be forged into the index this way.
- It acts as **defense in depth** alongside authorization. Even if a bare-ID lookup leaked across dataset boundaries — through a bug or a misconfigured query — the shared index uses the signed form as its key, so a record keyed under one namespace will not match a request keyed under another.

The signature is not a cryptographic secret. The HMAC key is the dataset name, which is knowable to anyone who has read the dataset, and a signature is therefore not a bearer capability. Access control is enforced at the authorization layer (collection-level permissions in OpenAleph; dataset visibility in yente), not by verifying signatures.

## Lifecycle of a signed ID

Signing happens at ingestion; verification and stripping happen when IDs cross a trust boundary.

- **At ingest.** When an entity enters a namespaced dataset — through a bulk upload, a mapping run, or a client-side edit — the host system calls [`Namespace.apply()`][followthemoney.namespace.Namespace.apply]. The entity's `id` gets signed, and every entity-typed property value on it gets signed with the same namespace.
- **At query time.** Clients may pass already-signed IDs back to the system (to reference entities they read earlier). The system calls [`Namespace.strip()`][followthemoney.namespace.Namespace.strip] to recover the bare ID for lookup, and optionally [`Namespace.verify()`][followthemoney.namespace.Namespace.verify] to check that the signature was produced by the claimed dataset.
- **At export.** Data leaving the system for downstream consumers can be published signed (preserving the namespace) or stripped (if the downstream context has no notion of datasets). Public data distributed outside a multi-tenant context is typically unsigned.

Because [`apply()`][followthemoney.namespace.Namespace.apply] rewrites references as well as the top-level ID, a signed entity stream is self-consistent: every `entity` property value inside it resolves within the same namespace.

## Example: signing an Ownership

Consider an `Ownership` entity that links a `Person` to a `Company`. Before signing, its property values are bare IDs:

```json
{
  "id": "owner-ship-1",
  "schema": "Ownership",
  "properties": {
    "owner": ["person-1"],
    "asset": ["company-1"]
  }
}
```

After `Namespace("md_companies").apply(proxy)`, every ID is suffixed with a signature specific to the `md_companies` dataset:

```json
{
  "id": "owner-ship-1.a40a29300ac6bb79dd2f911e77bbda7a3b502126",
  "schema": "Ownership",
  "properties": {
    "owner": ["person-1.c2c1…"],
    "asset": ["company-1.8b3f…"]
  }
}
```

If `person-1` also exists in a different dataset, its signature there is different, and the two variants do not collide in a shared index.

## Where it's used

**[OpenAleph](https://openaleph.org/)** uses namespacing on every collection. The collection's foreign ID is the HMAC key. Both entities and documents are signed; the UI signs IDs client-side when a user creates or edits entities in the browser, so the server and client agree on the signed form. Namespace signing is a load-bearing part of OpenAleph's data model — changing the signing algorithm invalidates every stored ID.

**[yente](https://yente.followthemoney.tech/)** supports namespacing as an opt-in per dataset. Setting `namespace: true` on a dataset manifest causes the indexer to apply the dataset's namespace to every entity at index time. This is useful when a yente deployment serves multiple datasets with potentially overlapping IDs. The tradeoff is that entities with the same bare ID in different datasets will no longer be treated as the same logical entity, so cross-dataset deduplication does not work through the search index while namespacing is active.

**Public OpenSanctions data** is published without namespace signatures. In a public, read-only distribution there is no multi-tenant concern, and consumers benefit from stable, shareable IDs.

## When not to use namespacing

Do not namespace data that:

- Is published to external consumers who need stable, portable IDs across environments. Signatures are specific to the emitting system's dataset names, and downstream tools rarely know how to strip them.
- Needs to be deduplicated across dataset boundaries by ID equality. Two crawlers that both produce `ofac-12345` as the canonical ID for the same sanctioned individual will stop matching once each gets namespaced.
- Lives in a single-tenant context with no authorization boundaries between producers. The overhead is not justified.

If you need dataset-level attribution without ID mangling, use the `dataset` field on each entity instead, and let downstream tools decide whether to merge by bare ID.

## API reference

::: followthemoney.namespace.Namespace
    options:
        show_source: false

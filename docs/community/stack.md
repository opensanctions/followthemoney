# Tools and applications

## Full stack applications

These applications are probably the reason why you ended up here. Most of the smaller packages below are part of their full stack.

- [OpenAleph](https://openaleph.org) – Search through large documents and structured data
- [Aleph](https://github.com/alephdata/aleph) – Original open-source core project, will no longer be maintained after October 2025
- [Aleph Pro](https://www.occrp.org/en/announcement/occrp-announces-a-new-chapter-for-its-investigative-data-platform-aleph-pro) – Closed-source SaaS version of original Aleph project, launching October 2025

## Build data and datasets

Tools and frameworks for _creating_ FollowTheMoney data with scrapers or custom applications.

- [followthemoney](https://github.com/opensanctions/followthemoney) – core ontology and data validation system, includes CSV/SQL to FtM mapper.
- [memorious](https://github.com/alephdata/memorious) – light-weight web scraping toolkit for scrapers that collect structured or un-structured data
    * A more recent [fork of memorious](https://docs.investigraph.dev/lib/memorious/)
- [zavod](https://zavod.opensanctions.org/) – Data processing framework as part of OpenSanctions
- [investigraph](https://docs.investigraph.dev/) – Framework to create FollowTheMoney data
- [ingest-file](https://github.com/openaleph/ingest-file) – Create document graphs out of source data for Aleph applications

Specialised data importers:

- [followthemoney-ocds](https://github.com/alephdata/followthemoney-ocds) - Convert open contracting data standard files to FtM
- [followthemoney-cellebrite](https://github.com/alephdata/followthemoney-cellebrite) - Import data forensics dumps from Cellebrite
- Importers for BODS (Beneficial Ownership Data) and GLEIF RR files are in OpenSanctions.

## Clean data

Tools and frameworks for _cleaning_ and _validating_ FollowTheMoney data.

- [rigour](https://opensanctions.github.io/rigour/) – Data cleaning and validation functions for processing various types of text emanating and describing the business world, base to `followthemoney`.
- [prefixdate](https://github.com/pudo/prefixdate) – a helper class to parse dates with varied degrees of precision
- [datapatch](https://github.com/opensanctions/datapatch) – A Python library for defining rule-based overrides on messy data
- [normality](https://github.com/pudo/normality/) – a Python micro-package that contains a small set of text normalization functions for easier re-use
- [countrytagger](https://github.com/alephdata/countrytagger) – extract country name references from text
- [followthemoney-typepredict](https://github.com/alephdata/followthemoney-typepredict) - guess the FtM type class of a piece of text, including distinguishing company and person names.

## Analyze data

Tools and frameworks for _analyzing_ FollowTheMoney data, for example transcribing [Audio](https://followthemoney.tech/explorer/schemata/Audio/) and [Video](https://followthemoney.tech/explorer/schemata/Audio/) entities, detecting languages or Named Entity Extraction (NER).

- [ftm-analyze](https://docs.investigraph.dev/lib/ftm-analyze/) – The standalone ftm analyzer formerly included in `ingest-file` for all kinds of processing
- [ftm-geocode](https://docs.investigraph.dev/lib/ftm-geocode/) – Batch parse and geocode addresses from FollowTheMoney entities
- [ftm-transcribe](https://github.com/openaleph/ftm-transcribe) – Extract text from Video and Audio
- [followthemoney-compare](https://github.com/alephdata/followthemoney-compare) – pre-process and train models to power a cross-reference system for FollowTheMoney data, includes a model based on regression and word frequency analysis in names.
- [juditha](https://github.com/dataresearchcenter/juditha) – Compare and resolve NER results to actual known FtM Entities
- [ingest-file.analysis](https://github.com/openaleph/ingest-file) – Part of the document ingestion is a comprehensive _analysis_ phase used for Aleph applications

## Store entity data

Tools and applications for _storing and retrieving_ FollowTheMoney data such as databases, key-value stores or document archives. Contains as well tools for storing related data (such as images for Entities).

- [followthemoney-store](https://github.com/alephdata/followthemoney-store) – Sql-backed store for [Entity fragments](https://followthemoney.tech/docs/fragments/)
- [nomenklatura](https://github.com/opensanctions/nomenklatura) – Store entity data as _statements_.
      * Implementations for different graph-traversable backends (memory, redis, kvrocks, sql).
      * Various entity matching algorithms (rule- and regression-based), and an in-memory cross-referencing index for data deduplication.
      * A Wikidata client with mappings from their data model onto FtM statements (wants to become `followthemoney-wikidata` at some point)
      * Data enrichment clients for building out investigative graphs pulling in remote info from Aleph, yente, Wikidata, OpenCorporates, PermID, OpenFIGI.
- [ftmq](https://docs.investigraph.dev/lib/ftmq/) – More advanced querying logic on top off the `nomenklatura` store implementations
- [bahamut](https://github.com/opensanctions/bahamut) – WIP FollowTheMoney statement data server with built-in entity resolution support. Written in Java.
- [FollowTheMoney Data Lake](https://openaleph.org/docs/lib/ftm-datalake/rfc/) – Scalable storage for structured data and document archives (upcoming)
- [ftm-columnstore](https://github.com/dataresearchcenter/ftm-columnstore) – [Clickhouse](https://clickhouse.com/)-backed implementation of a `nomenklatura` statement store
- [servicelayer](https://github.com/alephdata/servicelayer/) – Document archive for _legacy Aleph_ and [OpenAleph](https://openaleph.org)
- [leakrfc](https://docs.investigraph.dev/lib/leakrfc/) – data standard and archive storage for leaked data, private and public document collections, will become `ftm-datalake` (see above)
- [ftm-assets](https://github.com/dataresearchcenter/ftm-assets/) – Assets (image) resolver and storage for FollowTheMoney data

## IO / Streaming

Tools and helpers for streaming FollowTheMoney data between stores and systems.

- [alephclient](https://docs.aleph.occrp.org/developers/how-to/data/install-alephclient/) – Getting data in and out of Aleph with its API
- [openaleph-client](https://openaleph.org/docs/user-guide/104/) – `alephclient` fork for OpenAleph, adds more pre-processing capabilities.
- [ftmq.io](https://docs.investigraph.dev/lib/ftmq/reference/io/) – Generic helpers for read and write FollowTheMoney data from and to various local and remote locations

## API / Search

Building blocks for serving and searching FollowTheMoney datasets for web applications.

- [yente](https://www.opensanctions.org/docs/yente/) – API for OpenSanctions with support for entity search and bulk matching of data collections. Supports Reconciliation API specification.
- [ftmq-api](https://docs.investigraph.dev/lib/ftmq-api/) – Expose statement stores (by `ftmq` / `nomenklatura`) to a read-only [FastAPI](https://fastapi.tiangolo.com/)
- [ftmq-search](https://github.com/dataresearchcenter/ftmq-search) – Search experiments for FollowTheMoney data with different backends (Sqlite FTS, tantivy, elasticsearch)

## Discontinued / legacy tools

These libraries have been discontinued or merged with others:

- [Aleph Data Desktop](https://github.com/alephdata/datadesktop) – desktop application for drawing investigative network diagrams.
- [pantomime](https://github.com/alephdata/pantomime) – parsing and normalisation of internet MIME types in Python (discontinued, now in [rigour.mime][])
- [fingerprints](https://github.com/opensanctions/fingerprints) – Name handling utilities for person and organisation names (discontinued, now in [rigour.names][])
- [languagecodes](https://github.com/alephdata/languagecodes) – normalise the ISO 639 codes used to describe languages from two-letter codes to three letters, and vice versa (discontinued, now in [rigour.langs][])
- [countrynames](https://github.com/opensanctions/countrynames/) – This library helps with the mapping of country names to their respective two or three letter codes (now in [rigour.territories][])
- [addressformatting](https://github.com/pudo-attic/addressformatting) – address formatter that can format addresses in multiple formats that are common in different countries (discontinued, now in [rigour.addresses][])
- [followthemoney-predict](https://github.com/alephdata/followthemoney-predict) - previous entity comparison/linkage codebase.

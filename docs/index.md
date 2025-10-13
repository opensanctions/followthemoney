# Follow the Money

FollowTheMoney (FtM) is a data model for financial crime investigations and document forensics.

It contains definitions of the [entities](docs/index.md) relevant in such research (like [people](explorer/schemata/Person.md) or [companies](explorer/schemata/Company.md)) and tools that let you generate, validate, and export such data easily. Entities can reference each other, creating a graph of relevant relationships. The [ontology defined by FtM](explorer/schemata/index.md) also includes a model for various types of [documents](explorer/schemata/Document.md) that might be used as evidence in investigations.

## What is FtM used for?

FtM has multiple use cases in investigative data analysis:

* It's used as a **core data model** by software like [OpenAleph](https://openaleph.org/docs/), a data platform that securely stores large amounts of data and makes them searchable for easily collaboration, and [yente](https://www.opensanctions.org/docs/yente/), a screening engine for sanctions compliance.
* As a **data exchange format**, it is used to transfer structured datasets between different systems in a semantically well-defined manner.
* As a **part of an ETL pipeline**, FtM provides extensive tooling for data cleaning and normalisation for field types from person names, phone numbers, tax or company identifiers, and so on.
* As an SDK, it can be used to quickly draw up **small scripts and applications** that analyse data in the context of an investigation.

To learn more, explore the [projects using FtM](community/projects.md) and the [FtM-based libraries and tools](community/stack.md).

!["You follow drugs, you get drug addicts and drug dealers. But you start to follow the money, and you don't know where the fuck it's gonna take you."](/public/images/lester.png)
/// caption
*"You start to [follow the money](https://www.youtube.com/watch?v=ShWe-4mtV8w), and you don't know where the fuck it's gonna take you."* Image: [HBO](https://www.hbo.com/the-wire/cast-and-crew/lester-freamon).
///

# Follow the Money

[![ftm-build](https://github.com/opensanctions/followthemoney/actions/workflows/build.yml/badge.svg)](https://github.com/opensanctions/followthemoney/actions/workflows/build.yml)

This repository contains a pragmatic data model for the entities most commonly used in investigative reporting and financial crime investigations: people, companies, assets, payments, ownership relations, court cases, etc.

The purpose of this is not to model reality in an ideal data model, but rather to have a working data structure for researchers. Complex legal considerations are simplified to allow for efficient data processing.

`followthemoney` also contains code used to validate and normalize many of the elements of data, and to map tabular data into the model.

## Documentation

For a general introduction to `followthemoney`, check the high-level introduction:

* https://followthemoney.tech

Part of this package is a command-line tool that can be used to process and
transform data in various ways. You can find a tutorial here:

* https://followthemoney.tech/docs/cli/

Besides the introductions, there is also a full reference documentation for the
library and the contained ontology: 

* https://followthemoney.tech/explorer/schemata/

There's also a number of viewers for the RDF schema definitions generated from FollowTheMoney, eg:

* [LODE documentation](http://150.146.207.114/lode/extract?url=https%3A%2F%2Ffollowthemoney.tech%2Fns%2Fftm.xml&owlapi=true&imported=true&lang=en)
* [WebVOWL](https://service.tib.eu/webvowl/#iri=https://followthemoney.tech/ns/ftm.xml)
* RDF/OWL specification in [XML](https://followthemoney.tech/ns/ftm.xml).

## Installation

You can install `followthemomey` via PyPI like this:

```bash
pip install followthemoney
```

The most tricky dependency of `followthemoney` is `pyicu`, which helps us to perform certain text operations. Please [review their documentation](https://gitlab.pyicu.org/main/pyicu#installing-pyicu) if you run into any issues with ICU.

## Development environment

For local development with a virtualenv:

```bash
python3 -mvenv .env
source .env/bin/activate
pip install -e ".[dev]"
```

Now you can run the tests with

```bash
make test
```

## Releasing

We release a lot of version of `followthemoney` because even small changes to the code base require a pypi release to begin being used in downstream applications. To this end, here's the steps for making a release:

```bash
git pull --rebase
make build
make test
git add . && git commit -m "Updating translation files"
bumpversion patch
git push --atomic origin main $(git describe --tags --abbrev=0)
```

This will create a new patch release and upload a distribution of it. If the changes are more significant, you can run `bumpversion` with the `minor` or `major` arguments.

When the schema is updated, please update the docs, ideally including the diagrams. For the RDF namespace and JavaScript version of the model, run `make generate`.

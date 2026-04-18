# Property type registry

Every property on every schema has a `type` attribute pointing to a [`PropertyType`][followthemoney.types.common.PropertyType] instance — the object responsible for cleaning, validating, comparing, and rendering values of that property. Concrete types (`NameType`, `DateType`, `CountryType`, `PhoneType`, etc.) are instantiated once at module load and exposed through the `registry` singleton.

Access types by name rather than by importing the concrete classes directly:

```python
from followthemoney.types import registry

# Clean a value
phone = registry.phone.clean("+1 (415) 555-0100")

# Compare two values
score = registry.name.compare("Jane Doe", "J. Doe")

# Iterate all types that support comparison
for t in registry.matchable:
    print(t.name, t.label)
```

See [Property and PropertyType](property.md) for the rendered `PropertyType` base class and its methods.

## Registry

::: followthemoney.types.Registry
    options:
        heading_level: 3
        show_source: false

## Available types

The singleton `registry` exposes the following types as attributes. Each implements the `PropertyType` interface, typically with a specialized `clean_text()`, `compare()`, and `pick()` behavior appropriate for its domain.

| Attribute | Class | Purpose |
|---|---|---|
| `registry.name` | `NameType` | Names of persons, companies, other entities |
| `registry.date` | `DateType` | ISO-8601 dates and timestamps with variable precision |
| `registry.country` | `CountryType` | Country and territory codes |
| `registry.language` | `LanguageType` | ISO-639 language codes |
| `registry.phone` | `PhoneType` | E.164 phone numbers |
| `registry.email` | `EmailType` | Email addresses |
| `registry.url` | `UrlType` | URLs |
| `registry.address` | `AddressType` | Postal addresses |
| `registry.ip` | `IpType` | IPv4 / IPv6 addresses |
| `registry.identifier` | `IdentifierType` | Generic identifiers (tax IDs, registration numbers, etc.) |
| `registry.checksum` | `ChecksumType` | SHA-1 hex digests |
| `registry.mimetype` | `MimeType` | MIME types |
| `registry.entity` | `EntityType` | Entity ID references (links between entities) |
| `registry.topic` | `TopicType` | Controlled-vocabulary topic tags |
| `registry.gender` | `GenderType` | Gender codes |
| `registry.json` | `JsonType` | Opaque JSON blobs |
| `registry.text` | `TextType` | Long-form text (descriptions, notes) |
| `registry.html` | `HTMLType` | HTML fragments |
| `registry.string` | `StringType` | Short unstructured strings |
| `registry.number` | `NumberType` | Numeric values |

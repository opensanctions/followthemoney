{% set type = select_type('phone') %}
# {{ type.plural }}

Phone numbers are normalised to the international E.164 format (think `+442083661177`). Source datasets often give numbers in national format, without the country prefix. Such values cannot be interpreted on their own and are rejected, unless you name the country the number is dialed in via the `format` argument:

```python
from followthemoney import model
from followthemoney.types import registry

registry.phone.clean("020 8366 1177")               # None
registry.phone.clean("020 8366 1177", format="gb")  # '+442083661177'

entity = model.make_entity("Company")
entity.add("phone", "020 8366 1177", format="gb")
```

The hint accepts any country code `rigour` recognises, including three-letter codes and subdivisions such as `gb-eng`, which resolve to the country they dial through. Territories without a dialing plan of their own (`eu`, historical states) raise an error, as does a code that cannot be resolved at all.

!!! warning "Upgrading from 4.10 and earlier"

    Earlier versions parsed national-format numbers using the country properties of the [proxy][followthemoney.proxy.EntityProxy] they were added to, which made the result depend on the order in which properties were added. The entity is not consulted: pass `format`, or such numbers are rejected.

{% include 'templates/type.md' %}

## Python API

FtM uses Google's [phonenumbers library](https://pypi.org/project/phonenumbers/) to validate and normalise phone numbers.

::: followthemoney.types.PhoneType
    options:
        heading_level: 3
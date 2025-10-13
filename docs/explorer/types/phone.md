{% set type = select_type('phone') %}
# {{ type.plural }}

Phone numbers are normalised to the international E.164 format (think `+442083661177`). Since phone numbers are often provided by a source dataset without their country prefix, it is very helpful to supply the type validation functions (`phone.validate(value)` and `phone.clean(value)`) with an [proxy][followthemoney.proxy.EntityProxy] argument of the entity they will be assigned to, and from which country context can be inferred.

{% include 'templates/type.md' %}

## Python API

FtM uses Google's [phonenumbers library](https://pypi.org/project/phonenumbers/) to validate and normalise phone numbers.

::: followthemoney.types.PhoneType
    options:
        heading_level: 3
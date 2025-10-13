# Python Entity and Schema API

The core interfaces of `followthemoney` are simple: each running instance of the library has a [Model][followthemoney.model.Model] singleton, which holds a set of [Schema][followthemoney.schema.Schema] definitions (e.g. {{ schema_ref('Person') }}). Each schema defines a set of `properties` (e.g. `name`, `birthDate`) which give meaning to how values can be associated with entities of a given schema.

The `model` is also used to instantiate [entity proxies][followthemoney.proxy.EntityProxy] – objects that allow the creation and use of entity data, based on the rules defined by an associated schema.

## Installation

To install `followthemoney` from the Python package index, you need to have Python 3 installed and working on your computer. You may also want to create a virtual environment using virtualenv or pyenv. With that done, type:

```bash
pip install followthemoney
ftm --help
```

!!! info
    `followthemoney` transliterates text from various scripts to support the comparison of names and other data. For this reason, the projects depends on `pyicu`, a Python binding for the International Components for Unicode tool.

    On a Debian-based Linux system, installing ICU is relatively simple:

    ```bash
    apt install libicu-dev
    pip install pyicu
    ```

    For other platforms, please [refer to the pyciu documentation](https://gitlab.pyicu.org/main/pyicu#installing-pyicu) to get help with the required steps.


## Using the interfaces

For an illustration of how the schema and entity classes interact, imagine the following script:

```python
# Load the standard instance of the model
from followthemoney import model

## Schema metadata
# Access a schema metadata object
schema = model.get('Person')

# Access a property metadata object
prop = schema.get('birthDate')

## Working with entities and entity proxies
# Next, let's instantiate a proxy object for a new Person entity:
entity = model.make_entity(schema)

# First, you'll want to assign an ID to the entity. You can do this directly:
entity.id = 'john-smith'

# Or you can use a hashing function to make a safe ID:
entity.make_id('John Smith', '1979')

# Now, let's assign this entity a birthDate property (see above):
entity.add(prop, '1979-08-23')

# You can also assign properties by name:
entity.add('firstName', 'John')
entity.add('lastName', 'Smith')
entity.add('name', 'John Smith')

# Adding a property value will perform some data normalisation and validation:
entity.add('nationality', 'Atlantis')
assert not entity.has('nationality')
entity.add('nationality', 'Germani', fuzzy=True)
assert 'de' == entity.first('nationality')
enttiy.add('nationality', '阿拉伯聯合大公國')
assert 'ae' in entity.get('nationality')

# Lets make a second entity, this time for a passport:
passport_entity = model.make_entity('Passport')
passport_entity.make_id(entity.id, 'C716818')
passport_entity.add('number', 'C716818')

# Entities can link to other entities like this:
passport_entity.add('holder', entity)
# Which is the same as:
passport_entity.add('holder', entity.id)

# Finally, you can turn the contents of the entity proxy into a plain dictionary
# that is suitable for JSON serialization or storage in a database:
data = entity.to_dict()
assert data.get('id') == entity.id

# If you want to turn this back into an entity proxy:
entity2 = model.get_proxy(data)
assert entity2 == entity
```

Besides the contstruction of entities, you can also use the underlying type system used to validate property values (in this case {{ type_ref('date') }}) directly:

```python
# You can also import the type registry that lets you access type info easily:
from followthemoney import registry
assert prop.type == registry.date

assert not registry.date.validate('BANANA')
assert registry.date.validate('2025')
```

The library offers a much more complex set of operations - but entity proxies, schemata, properties, and the model are the key elements to understand.

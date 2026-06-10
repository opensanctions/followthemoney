from followthemoney.entity import ValueEntity, VE
from followthemoney.model import Model
from followthemoney.schema import Schema
from followthemoney.property import Property
from followthemoney.types import registry, PropertyType
from followthemoney.value import Value, Values
from followthemoney.proxy import EntityProxy, E
from followthemoney.statement import Statement, StatementEntity, SE
from followthemoney.dataset import Dataset, UndefinedDataset, DS
from followthemoney.util import set_model_locale

__version__ = "4.9.1"

# Data model singleton
model = Model.instance()

__all__ = [
    "model",
    "set_model_locale",
    "Model",
    "Schema",
    "Property",
    "PropertyType",
    "Value",
    "Values",
    "EntityProxy",
    "E",
    "registry",
    "Dataset",
    "UndefinedDataset",
    "DS",
    "Statement",
    "StatementEntity",
    "SE",
    "ValueEntity",
    "VE",
]

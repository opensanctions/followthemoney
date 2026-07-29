from followthemoney.dataset import DS, Dataset, UndefinedDataset
from followthemoney.entity import VE, ValueEntity
from followthemoney.model import Model
from followthemoney.property import Property
from followthemoney.proxy import E, EntityProxy
from followthemoney.schema import Schema
from followthemoney.statement import SE, Statement, StatementEntity
from followthemoney.types import PropertyType, registry
from followthemoney.util import set_model_locale
from followthemoney.value import Value, Values

__version__ = "4.10.0"

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

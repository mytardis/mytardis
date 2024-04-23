from dataclasses import fields, is_dataclass
from typing import Any, Type

from yaml import MappingNode, YAMLObject
from yaml.loader import Loader


class YAMLDataclass(YAMLObject):
    """A metaclass for dataclass objects to be serialised and deserialised by pyyaml."""

    @classmethod
    def from_yaml(cls: Type["YAMLDataclass"], loader: Loader, node: MappingNode) -> Any:
        """
        Convert a representation node to a Python object,
        calling __init__ to create a new object.

        We're using dataclasses to create an __init__ method
        which sets default values for fields not present in YAML document.
        By default, YAMLObject does not call __init__, so yaml.safe_load throws an exception
        on documents that don't have all required fields. (see https://github.com/yaml/pyyaml/issues/510,
        https://stackoverflow.com/questions/13331222/yaml-does-not-call-the-constructor)
        So we override the from_yaml method here to call __init__ (see
        https://stackoverflow.com/questions/7224033/default-constructor-parameters-in-pyyaml)
        """
        fields = loader.construct_mapping(node)
        return cls(**fields)

    def __getstate__(self) -> dict[str, Any]:
        """Override method for pyyaml. Returns a dictionary of key and value
        that should be serialised by yaml. Fields which have repr=False will not
        be included.
        See https://github.com/yaml/pyyaml/issues/612 for explanation on __getstate__.

        Returns:
            dict[str, Any]: A dictionary of key and values to be serialised in this class.
        """
        assert is_dataclass(self)  # tidy this up with an appropriate exception
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.repr is True  # Only include repr=True fields
        }

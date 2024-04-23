# pylint: disable=consider-using-f-string
""" This module defines custom data types for use in the MyTardis ingestion scripts.
 These data types include validators and custom exceptions for accurate logging and error
handling.
This is a fork of the ingestion script module: https://github.com/UoA-eResearch/mytardis_ingestion/blob/master/src/blueprints/custom_data_types.py
When merged into the same repository, we will depend on that module directly.
"""

import re
from typing import Generator, Type

from yaml import Dumper, FullLoader, Loader, Node, ScalarNode, UnsafeLoader

user_regex = re.compile(
    r"^[a-z]{2,4}[0-9]{3}$"  # Define as a constant in case of future change
)


class Username(str):
    """Defines a validated username, in other words, ensure that the username meets a standardised
    format appropriate to the institution.

    Note this is a user class defined for the University of Auckland UPI format. For
    other username formats please update the user_regex pattern.
    """

    @classmethod
    def __get_validators__(cls: Type["Username"]) -> Generator:
        """One or more validators may be yielded which will be called in order to validate the
        input. Each validator will receive as an input the value returned from the previous
        validator. (As per the Pydantic help manual).
        """
        yield cls.validate

    @classmethod
    def validate(cls: Type["Username"], value: str) -> "Username":
        """Custom validator to ensure that the value is a string object and that it matches
        the regex defined for users"""
        if not isinstance(value, str):
            raise TypeError(f'Unexpected type for Username: "{type(value)}"')
        if match := user_regex.fullmatch(value.lower()):
            return cls(f"{match.group(0)}")
        else:
            raise ValueError(
                f'Passed string value "{value}" is not a well formatted Username'
            )

    def __repr__(self) -> str:
        """Indicate that the username object is a username"""
        return f"Username({super().__repr__()})"


def Username_yaml_representer(dumper: Dumper, data: "Username") -> ScalarNode:
    """Function for representing this Username in YAML.
    When serialising to YAML that contains Username instances, you'll
    need to add this function as a representer.

    `yaml.add_representer(Username, Username.yaml_representer)`_

    Args:
        dumper (Dumper): The pyyaml dumper.
        data (Username): The Username to dump.

    Returns:
        ScalarNode: A serialised yaml Node.
    """
    return dumper.represent_scalar("!Username", str(data))


def Username_yaml_constructor(
    loader: Loader | FullLoader | UnsafeLoader, node: Node
) -> "Username":
    """Function for deserialising a node from YAML.
    When parsing YAML that contains Username instances, you'll
    need to add this function as a constructor.

    `yaml.add_constructor('!Username', Username.yaml_constructor)`_

    Args:
        loader (Loader): The pyyaml loader.
        node (ScalarNode): The node representing a Username.

    Returns:
        Username: A constructed username.
    """
    assert isinstance(node, ScalarNode)
    value = loader.construct_scalar(node)
    return Username(value)

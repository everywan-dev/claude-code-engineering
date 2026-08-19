"""The declared extension: adopter-owned fields on top of the base contract.

An adopter extends the contract without forking it. A configuration file at the
project root names a versioned schema, and the schema declares the fields the
adopter's units may carry. The plugin owns the base contract; the adopter owns
the extension.
"""

from pathlib import Path

from .contract import BASE_FIELDS
from .frontmatter import FrontmatterError, parse

CONFIG_FILENAME = "validated-memory.md"

CONFIG_FIELDS = ("extension", "id_prefix", "probes")
EXTENSION_FIELDS = ("schema", "version")
FIELD_KEYS = ("name", "type", "values")
FIELD_TYPES = ("string", "enum")


class ExtensionError(Exception):
    """Raised when the adopter's configuration cannot be applied.

    Loading is fail-loud: nothing here degrades to base-contract-only
    validation, because a silently ignored extension validates nothing while
    appearing to pass.
    """

    def __init__(self, location, field, message, line=None):
        super().__init__(message)
        self.location = location
        self.field = field
        self.message = message
        self.line = line


class Extension:
    """The fields an adopter declared, ready to be applied to a unit."""

    __slots__ = ("fields",)

    def __init__(self, fields):
        self.fields = fields

    @property
    def names(self):
        return tuple(self.fields)

    def violation(self, name, value):
        """Say why `value` fails the declaration of `name`, or None if it holds.

        The reason completes a sentence about the value, which the caller
        describes: the schema's shape is known here, not by the contract.
        """
        declaration = self.fields[name]
        if not _is_non_empty_string(value):
            return "is not a non-empty scalar"
        if declaration["type"] == "enum" and value not in declaration["values"]:
            return "is not one of " + ", ".join(declaration["values"])
        return None


def load(root):
    """Load the adopter's declared extension, or None when none is configured."""
    config_path = Path(root) / CONFIG_FILENAME
    if not config_path.exists():
        return None

    declared = _declaration(config_path)
    if declared is None:
        return None
    return Extension(_fields(config_path.parent / declared["schema"]))


def probes(root):
    """The adopter's probe registry: `kind` -> command, or `{}` when unconfigured.

    Consumed by the `probe` subcommand. Reuses the same whole-configuration
    validation as `load`, so a malformed `validated-memory.md` raises
    `ExtensionError` the same way regardless of which subcommand reads it
    first.
    """
    config_path = Path(root) / CONFIG_FILENAME
    if not config_path.exists():
        return {}
    return _config(config_path).get("probes") or {}


def _fields(schema_path):
    """Read the field declarations of the adopter's schema."""
    location = schema_path.as_posix()
    schema = _read(schema_path)
    if "fields" not in schema:
        raise ExtensionError(location, "fields", "required field is missing")
    declarations = schema["fields"]
    if not isinstance(declarations, list):
        raise ExtensionError(
            location, "fields", "is not a list of field declarations"
        )

    fields = {}
    for position, declaration in enumerate(declarations):
        field = f"fields[{position}]"
        if not isinstance(declaration, dict):
            raise ExtensionError(location, field, "is not a mapping")
        for key in declaration:
            if key not in FIELD_KEYS:
                raise ExtensionError(
                    location,
                    field,
                    f"unknown key '{key}'; a field declares "
                    + ", ".join(FIELD_KEYS),
                )

        name = declaration.get("name")
        if not _is_non_empty_string(name):
            raise ExtensionError(location, field, "'name' is missing or is not a name")
        if name in BASE_FIELDS:
            raise ExtensionError(
                location,
                field,
                f"'{name}' belongs to the base contract; an extension adds "
                "fields, it does not redeclare them",
            )
        if name in fields:
            raise ExtensionError(location, field, f"duplicate field '{name}'")

        _check_domain(location, field, declaration)
        fields[name] = declaration
    return fields


def _check_domain(location, field, declaration):
    kind = declaration.get("type")
    if kind not in FIELD_TYPES:
        raise ExtensionError(
            location,
            field,
            "'type' is missing or is not one of " + ", ".join(FIELD_TYPES),
        )
    values = declaration.get("values")
    if kind != "enum":
        if values is not None:
            raise ExtensionError(
                location,
                field,
                "'values' declares a closed domain and only applies to type 'enum'",
            )
        return
    if not isinstance(values, list) or not values:
        raise ExtensionError(
            location,
            field,
            "an enum declares its closed domain in a non-empty 'values' list",
        )
    for value in values:
        if not _is_non_empty_string(value):
            raise ExtensionError(
                location, field, "every value of a closed domain is a non-empty string"
            )


def _config(config_path):
    """Read and validate the adopter's whole configuration document.

    Every adopter surface is checked here, not only the one the caller
    consumes: a configuration with a malformed key stops every run, even a
    run of a subcommand that key does not concern. Returns the validated
    mapping.
    """
    location = config_path.as_posix()
    config = _read(config_path)

    for key in config:
        if key not in CONFIG_FIELDS:
            raise ExtensionError(
                location,
                key,
                "unknown configuration field; this version declares "
                + ", ".join(CONFIG_FIELDS),
            )

    if "id_prefix" in config and not _is_non_empty_string(config["id_prefix"]):
        raise ExtensionError(location, "id_prefix", "is not a non-empty string")

    if "probes" in config:
        probes = config["probes"]
        if not isinstance(probes, dict):
            raise ExtensionError(
                location, "probes", "is not a mapping of probe kind to command"
            )
        for kind, command in probes.items():
            if not _is_non_empty_string(command):
                raise ExtensionError(
                    location, f"probes.{kind}", "is not a non-empty command"
                )

    if "extension" in config and not isinstance(config["extension"], dict):
        raise ExtensionError(location, "extension", "is not a mapping")

    return config


def _declaration(config_path):
    """Read the adopter's configuration and return its `extension` block.

    Returns None when the configuration declares no extension: `extension` is
    one adopter surface among several, not a required one.
    """
    location = config_path.as_posix()
    config = _config(config_path)

    if "extension" not in config:
        return None

    declared = config["extension"]
    for key in declared:
        if key not in EXTENSION_FIELDS:
            raise ExtensionError(
                location,
                f"extension.{key}",
                "unknown field; an extension declares "
                + ", ".join(EXTENSION_FIELDS),
            )
    for key in EXTENSION_FIELDS:
        if key not in declared:
            raise ExtensionError(
                location, f"extension.{key}", "required field is missing"
            )
        if not _is_non_empty_string(declared[key]):
            raise ExtensionError(
                location, f"extension.{key}", "is not a non-empty string"
            )
    return declared


def _is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _read(path):
    """Read and parse a configuration document, or raise `ExtensionError`."""
    location = path.as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ExtensionError(location, "file", f"cannot be read: {error}") from error
    try:
        return parse(text)
    except FrontmatterError as error:
        raise ExtensionError(
            location, "frontmatter", error.message, line=error.lineno
        ) from error

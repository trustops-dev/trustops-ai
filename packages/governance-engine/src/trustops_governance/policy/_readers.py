"""Small readers for configuration values. Each one fails closed with ``PolicyConfigError``.

Used only by ``loader``. A path is a dotted location such as ``policies.PROC-APPROVAL-01``;
the configuration root has the empty path.
"""

import re
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from .policy_schema import ConfigErrorCode, PolicyConfigError

# Plain digits with an optional fraction: no sign, whitespace, exponent, NaN or infinity.
_DECIMAL_TEXT = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")


def missing(path: str, detail: str) -> PolicyConfigError:
    return PolicyConfigError(ConfigErrorCode.POLICY_CONFIG_MISSING, path, detail)


def invalid(path: str, detail: str) -> PolicyConfigError:
    return PolicyConfigError(ConfigErrorCode.POLICY_CONFIG_INVALID, path, detail)


def join_path(parent: str, key: str) -> str:
    return key if parent == "" else f"{parent}.{key}"


def require_block(value: object, path: str) -> Mapping[str, Any]:
    """A configuration block: absent or empty is missing, a non-mapping is invalid."""
    if value is None:
        raise missing(path, "the block is absent")
    if not isinstance(value, Mapping):
        raise invalid(path, "the block must be a mapping")
    if not value:
        raise missing(path, "the block is empty")
    return value


def child_block(parent: Mapping[str, Any], key: str, parent_path: str) -> Mapping[str, Any]:
    return require_block(parent.get(key), join_path(parent_path, key))


def text(parent: Mapping[str, Any], key: str, path: str) -> str:
    """A required text field: absent, null, blank or not text is invalid."""
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise invalid(join_path(path, key), "must be a non-empty string")
    return value


def optional_text(parent: Mapping[str, Any], key: str, path: str) -> str | None:
    """Text that may be absent or null, but is never blank or of another type."""
    if parent.get(key) is None:
        return None
    return text(parent, key, path)


def decimal_text(parent: Mapping[str, Any], key: str, path: str) -> Decimal:
    """A positive decimal written as text. Numbers are refused so no float ever gets in."""
    raw = text(parent, key, path)
    if _DECIMAL_TEXT.fullmatch(raw) is None or Decimal(raw) <= 0:
        raise invalid(join_path(path, key), "must be a positive decimal string such as 1000.00")
    return Decimal(raw)


def non_negative_int(parent: Mapping[str, Any], key: str, path: str) -> int:
    value = parent.get(key)
    if type(value) is not int or value < 0:
        raise invalid(join_path(path, key), "must be a whole number, zero or more")
    return value


def flag(parent: Mapping[str, Any], key: str, path: str) -> bool:
    """A switch that is off when absent. A value that is present must be a real boolean."""
    value = parent.get(key, False)
    if not isinstance(value, bool):
        raise invalid(join_path(path, key), "must be true or false")
    return value

"""Load the packaged canonical taxonomy without adding a YAML runtime dependency.

`failure_taxonomy.yaml` uses the JSON syntax subset of YAML 1.2. JSON is valid
YAML 1.2, so the stdlib parser is deterministic and the existing locked dependency
set remains unchanged. Keep the file interoperable with standard YAML readers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from trustops_reliability.taxonomy.validation import TaxonomyValidationError, validate_taxonomy


def load_taxonomy(path: str | Path | None = None) -> dict[str, object]:
    """Load and validate the bundled taxonomy, or a supplied path for validation/tests."""
    source = Path(path) if path is not None else Path(__file__).with_name("failure_taxonomy.yaml")
    try:
        parsed: object = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TaxonomyValidationError(f"cannot read failure taxonomy at {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise TaxonomyValidationError(
            "failure taxonomy must be valid JSON-compatible YAML 1.2: "
            f"{exc.msg} at line {exc.lineno}"
        ) from exc
    if not isinstance(parsed, dict) or any(not isinstance(key, str) for key in parsed):
        raise TaxonomyValidationError("taxonomy root must be an object with string keys")
    taxonomy = cast(dict[str, object], parsed)
    validate_taxonomy(taxonomy)
    return taxonomy

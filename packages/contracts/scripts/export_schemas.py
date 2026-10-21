"""Export JSON Schema wire contracts from the canonical Pydantic v2 models.

Run from the repository root with:

    PYTHONPATH=packages/contracts/src python packages/contracts/scripts/export_schemas.py

Cross-field and recursive semantic constraints are supplemented here because they cannot
all be represented as generic constraints in Pydantic-generated JSON Schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from trustops_contracts.evaluations import EvaluationRequestV1, EvaluationResultV1
from trustops_contracts.failures import PRIMARY_FAILURE_LABELS, FailureLabelV1

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
DRAFT = "https://json-schema.org/draft/2020-12/schema"


def _remove_null_defaults(value: Any) -> None:
    if isinstance(value, dict):
        if value.get("default", object()) is None:
            value.pop("default")
        for child in value.values():
            _remove_null_defaults(child)
    elif isinstance(value, list):
        for child in value:
            _remove_null_defaults(child)


def _evidence_target_rule() -> dict[str, object]:
    return {
        "anyOf": [
            {
                "required": [target],
                "properties": {target: {"type": "string", "minLength": 1, "pattern": r"\S"}},
            }
            for target in (
                "event_id",
                "span_id",
                "document_id",
                "source_id",
                "field_path",
                "claim_id",
            )
        ]
    }


def _schema(model: type[BaseModel], schema_id: str, title: str, comment: str) -> dict[str, Any]:
    document = model.model_json_schema(mode="validation")
    _remove_null_defaults(document)
    document.update({"$schema": DRAFT, "$id": schema_id, "title": title, "$comment": comment})
    evidence = document.get("$defs", {}).get("EvidenceReferenceV1")
    if isinstance(evidence, dict):
        evidence.update(_evidence_target_rule())
    return document


def _failure_label_schema() -> dict[str, Any]:
    document = _schema(
        FailureLabelV1,
        "urn:trustops-ai:schema:failure-label-v1",
        "TrustOps Adjudicated Failure Label v1",
        (
            "Observed/adjudicated truth is separate from intended injection metadata and all "
            "evaluator predictions. JSON Schema does not resolve evidence IDs "
            "against stored traces."
        ),
    )
    document["properties"]["secondary_findings"]["uniqueItems"] = True
    document["allOf"] = [
        {
            "if": {
                "properties": {"annotation_status": {"const": "adjudicated"}},
                "required": ["annotation_status"],
            },
            "then": {
                "required": ["label_source"],
                "properties": {
                    "label_source": {
                        "enum": ["human_adjudication", "controlled_scenario_confirmed"]
                    },
                    "primary_label": {"enum": list(PRIMARY_FAILURE_LABELS)},
                    "evidence_refs": {"minItems": 1},
                },
            },
        },
        {
            "if": {
                "properties": {
                    "annotation_status": {
                        "enum": ["pending", "insufficient_evidence", "needs_adjudication"]
                    }
                },
                "required": ["annotation_status"],
            },
            "then": {"properties": {"primary_label": {"type": "null"}}},
        },
        {
            "if": {
                "properties": {"label_source": {"const": "controlled_scenario_confirmed"}},
                "required": ["label_source"],
            },
            "then": {
                "required": ["intended_failure_class"],
                "oneOf": [
                    {
                        "properties": {
                            "primary_label": {"const": label},
                            "intended_failure_class": {"const": label},
                        },
                        "required": ["primary_label", "intended_failure_class"],
                    }
                    for label in PRIMARY_FAILURE_LABELS
                ],
            },
        },
    ]
    return document


def _evaluation_input_schema() -> dict[str, Any]:
    document = _schema(
        EvaluationRequestV1,
        "urn:trustops-ai:schema:evaluator-input-v1",
        "TrustOps Evaluator Input v1",
        (
            "The opaque trace_payload is validated only for nested ground-truth leakage by the "
            "Python model; canonical trace-shape and cross-envelope ID/version checks require "
            "the frozen Mohab Trace Schema v1."
        ),
    )
    document["properties"]["trace_payload"].setdefault(
        "description", "Observed canonical trace payload only."
    )
    reference_schema = document.get("$defs", {}).get("EvaluationReferenceDataV1", {})
    reference_properties = (
        reference_schema.get("properties", {}) if isinstance(reference_schema, dict) else {}
    )
    for field in ("expected_relevant_document_ids", "expected_citation_document_ids"):
        if field in reference_properties:
            reference_properties[field]["uniqueItems"] = True
    return document


def _evaluation_output_schema() -> dict[str, Any]:
    document = _schema(
        EvaluationResultV1,
        "urn:trustops-ai:schema:evaluator-output-v1",
        "TrustOps Evaluator Output v1",
        (
            "Evidence trace-ID equality and fail/findings cross-field semantics are validated by "
            "the Python model. JSON Schema does not prove that referenced events exist in storage."
        ),
    )
    document["properties"]["metrics"]["propertyNames"] = {"pattern": r"\S"}
    document["allOf"] = [
        {
            "if": {"properties": {"status": {"const": "fail"}}, "required": ["status"]},
            "then": {"properties": {"findings": {"minItems": 1}}},
        }
    ]
    return document


def main() -> None:
    outputs = {
        "failure-label-v1.schema.json": _failure_label_schema(),
        "evaluator-input-v1.schema.json": _evaluation_input_schema(),
        "evaluator-output-v1.schema.json": _evaluation_output_schema(),
    }
    for filename, document in outputs.items():
        path = SCHEMA_DIR / filename
        path.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

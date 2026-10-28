"""Dependency-free loading and typed access for Failure Taxonomy v1.

The parser intentionally supports the structured YAML subset used by the
versioned taxonomy file: indentation-based mappings/lists, quoted strings,
inline lists, booleans, nulls, integers, and finite decimals. Unsupported YAML
features fail with a line-numbered error instead of being guessed.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from importlib.resources import files as resource_files
from pathlib import Path
from typing import Any, TypeVar, cast


class TaxonomyLoadError(ValueError):
    """Raised when the YAML text cannot be parsed or typed taxonomy is invalid."""


class ApplicationScope(StrEnum):
    RAG = "rag"
    AGENT = "agent"


class FailureClass(StrEnum):
    NORMAL = "NORMAL"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    HALLUCINATION = "HALLUCINATION"
    TOOL_SELECTION_ERROR = "TOOL_SELECTION_ERROR"
    INVALID_TOOL_ARGUMENTS = "INVALID_TOOL_ARGUMENTS"
    WORKFLOW_VIOLATION = "WORKFLOW_VIOLATION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    UNSUPPORTED_COMPLETION = "UNSUPPORTED_COMPLETION"


class GroundTruthSource(StrEnum):
    INJECTED_SCENARIO_METADATA = "INJECTED_SCENARIO_METADATA"
    HUMAN_ADJUDICATED_LABEL = "HUMAN_ADJUDICATED_LABEL"
    EXPECTED_SCENARIO_EVIDENCE = "EXPECTED_SCENARIO_EVIDENCE"
    EVALUATOR_PREDICTION = "EVALUATOR_PREDICTION"


class ViolationDisposition(StrEnum):
    ATTEMPTED = "ATTEMPTED"
    PREVENTED = "PREVENTED"
    REALIZED = "REALIZED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RootCauseCandidateId(StrEnum):
    PROMPT = "prompt"
    RETRIEVER = "retriever"
    RETRIEVED_CONTEXT = "retrieved_context"
    MODEL_GENERATION = "model_generation"
    TOOL_SELECTION = "tool_selection"
    TOOL_ARGUMENTS = "tool_arguments"
    AGENT_WORKFLOW = "agent_workflow"
    POLICY_CONFIGURATION = "policy_configuration"
    MALICIOUS_INPUT = "malicious_input"


class EvaluatorFamily(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    RAG = "RAG"
    RAG_SEMANTIC = "RAG_SEMANTIC"
    SEMANTIC_LLM = "SEMANTIC_LLM"
    SECURITY = "SECURITY"
    AGENT_WORKFLOW = "AGENT_WORKFLOW"
    POLICY = "POLICY"


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"


@dataclass(frozen=True, slots=True)
class GroundTruthSourceSpec:
    rank: int
    source_id: GroundTruthSource
    description: str
    allowed_as_ground_truth: bool


@dataclass(frozen=True, slots=True)
class ViolationDispositionSpec:
    disposition_id: ViolationDisposition
    description: str


@dataclass(frozen=True, slots=True)
class PrimaryLabelPrecedence:
    rank: int
    class_id: FailureClass
    rationale: str


@dataclass(frozen=True, slots=True)
class FailureClassSpec:
    class_id: FailureClass
    is_failure: bool
    applicable_apps: tuple[ApplicationScope, ...]
    precedence_rank: int
    definition: str
    inclusion_criteria: tuple[str, ...]
    exclusion_criteria: tuple[str, ...]
    controlled_generation: str
    primary_metrics: tuple[str, ...]
    expected_evaluator_signals: tuple[str, ...]
    required_evidence_ids: tuple[str, ...]
    allowed_secondary_findings: tuple[FailureClass, ...]
    default_rca_candidates: tuple[RootCauseCandidateId, ...]


@dataclass(frozen=True, slots=True)
class RootCauseCandidateSpec:
    candidate_id: RootCauseCandidateId
    description: str
    typical_evidence_signals: tuple[str, ...]
    required_evidence_ids: tuple[str, ...]
    disambiguation_note: str


@dataclass(frozen=True, slots=True)
class MetricValueSpec:
    metric_name: str
    unit: str
    direction: MetricDirection


@dataclass(frozen=True, slots=True)
class EvaluatorSpec:
    evaluator_id: str
    family: EvaluatorFamily
    default_version: str
    applicable_apps: tuple[ApplicationScope, ...]
    is_fallible_judge: bool
    can_be_ground_truth: bool
    required_evidence_ids: tuple[str, ...]
    output_metrics: tuple[MetricValueSpec, ...]
    dashboard_field_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResearchQuestionSpec:
    rq_id: str
    question: str
    compared_methods: tuple[str, ...]
    primary_metrics: tuple[str, ...]
    falsifiable_null_policy: str


@dataclass(frozen=True, slots=True)
class DatasetLeakageSafeguards:
    train_ratio: float
    validation_ratio: float
    test_ratio: float
    required_split_group_components: tuple[str, ...]
    forbidden_inference_feature_keys: tuple[str, ...]
    paraphrase_grouping_rule: str
    test_freeze_rule: str


@dataclass(frozen=True, slots=True)
class FailureTaxonomyV1:
    schema_version: str
    taxonomy_version: str
    status: str
    owner: str
    subsystem: str
    single_primary_label_invariant: bool
    allow_secondary_findings: bool
    forbid_evaluator_as_ground_truth: bool
    rca_scores_are_calibrated_probabilities: bool
    ground_truth_hierarchy: tuple[GroundTruthSourceSpec, ...]
    violation_dispositions: tuple[ViolationDispositionSpec, ...]
    primary_label_precedence: tuple[PrimaryLabelPrecedence, ...]
    classes: tuple[FailureClassSpec, ...]
    root_cause_candidates: tuple[RootCauseCandidateSpec, ...]
    evaluators: tuple[EvaluatorSpec, ...]
    research_questions: tuple[ResearchQuestionSpec, ...]
    dataset_leakage_safeguards: DatasetLeakageSafeguards

    def class_by_id(self, class_id: FailureClass | str) -> FailureClassSpec:
        target = _enum_value(FailureClass, class_id, "class_id")
        for spec in self.classes:
            if spec.class_id == target:
                return spec
        raise KeyError(f"Unknown failure class: {target}")

    def evaluator_by_id(self, evaluator_id: str) -> EvaluatorSpec:
        for spec in self.evaluators:
            if spec.evaluator_id == evaluator_id:
                return spec
        raise KeyError(f"Unknown evaluator ID: {evaluator_id}")


TEnum = TypeVar("TEnum", bound=StrEnum)


def _enum_value[TEnum: StrEnum](
    enum_type: type[TEnum], value: object, context: str
) -> TEnum:
    if not isinstance(value, str):
        raise TaxonomyLoadError(f"Invalid {context}: {value!r}")

    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise TaxonomyLoadError(f"Invalid {context}: {value!r}") from exc


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise TaxonomyLoadError(f"{context} must be a mapping with string keys")
    return cast(dict[str, Any], value)


def _list(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise TaxonomyLoadError(f"{context} must be a list")
    return value


def _string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaxonomyLoadError(f"{context} must be a non-empty string")
    return value


def _bool(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        raise TaxonomyLoadError(f"{context} must be a boolean")
    return value


def _int(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TaxonomyLoadError(f"{context} must be an integer")
    return value


def _str_tuple(value: object, context: str) -> tuple[str, ...]:
    return tuple(
        _string(item, f"{context}[{index}]") for index, item in enumerate(_list(value, context))
    )


def _enum_tuple[TEnum: StrEnum](
    value: object, enum_type: type[TEnum], context: str
) -> tuple[TEnum, ...]:
    return tuple(
        _enum_value(enum_type, item, f"{context}[{index}]")
        for index, item in enumerate(_list(value, context))
    )


def _strip_comment(line: str) -> str:
    """Strip a YAML comment outside quotes (only unquoted whitespace-# comments)."""
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if quote and char == quote:
            quote = None
        elif not quote and char in {'"', "'"}:
            quote = char
        elif not quote and char == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
    return line.rstrip()


def _split_mapping_entry(text: str, line_no: int) -> tuple[str, str]:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if quote and char == quote:
            quote = None
        elif not quote and char in {'"', "'"}:
            quote = char
        elif not quote and char == ":" and (index + 1 == len(text) or text[index + 1].isspace()):
            key = text[:index].strip()
            if not key:
                break
            return key, text[index + 1 :].strip()
    raise TaxonomyLoadError(f"Expected 'key: value' at YAML line {line_no}")


def _parse_scalar(text: str, line_no: int) -> object:
    value = text.strip()
    if not value:
        return None
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise TaxonomyLoadError(
                f"Invalid double-quoted scalar at YAML line {line_no}: {exc.msg}"
            ) from exc
        if not isinstance(parsed, str):
            raise TaxonomyLoadError(f"Expected a quoted string at YAML line {line_no}")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise TaxonomyLoadError(f"Unterminated single-quoted scalar at YAML line {line_no}")
        return value[1:-1].replace("''", "'")
    if value.startswith("["):
        try:
            parsed_list = json.loads(value)
        except json.JSONDecodeError as exc:
            raise TaxonomyLoadError(
                f"Unsupported inline list at YAML line {line_no}: {exc.msg}"
            ) from exc
        if not isinstance(parsed_list, list):
            raise TaxonomyLoadError(f"Expected inline list at YAML line {line_no}")
        return parsed_list
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"[-+]?(?:0|[1-9][0-9]*)", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:[0-9]+\.[0-9]+|[0-9]+\.)", value):
        number = float(value)
        if not math.isfinite(number):
            raise TaxonomyLoadError(f"Non-finite number at YAML line {line_no}")
        return number
    if value in {"|", ">", "|-", ">-", "|+", ">+"}:
        raise TaxonomyLoadError(f"Block scalar YAML is not supported at line {line_no}")
    # The source schema intentionally quotes all text; accept remaining plain scalars as text.
    return value


@dataclass(frozen=True, slots=True)
class _YamlLine:
    indent: int
    content: str
    line_no: int


class _StructuredYamlParser:
    """Parser for the deliberately restricted YAML subset used by the taxonomy file."""

    def __init__(self, text: str) -> None:
        self.lines: list[_YamlLine] = []
        for line_no, raw in enumerate(text.splitlines(), 1):
            if "\t" in raw[: len(raw) - len(raw.lstrip())]:
                raise TaxonomyLoadError(f"Tabs are not allowed for indentation at line {line_no}")
            cleaned = _strip_comment(raw)
            if (
                not cleaned.strip()
                or cleaned.lstrip().startswith("---")
                or cleaned.lstrip() == "..."
            ):
                continue
            indent = len(cleaned) - len(cleaned.lstrip(" "))
            content = cleaned[indent:]
            if content.startswith("%"):
                raise TaxonomyLoadError(f"YAML directives are not supported at line {line_no}")
            self.lines.append(_YamlLine(indent, content, line_no))
        self.index = 0

    def parse(self) -> object:
        if not self.lines:
            return None
        if self.lines[0].indent != 0:
            raise TaxonomyLoadError(
                f"Top-level content must start at column 1 (line {self.lines[0].line_no})"
            )
        result = self._parse_block(self.lines[0].indent)
        if self.index != len(self.lines):
            line = self.lines[self.index]
            raise TaxonomyLoadError(f"Unexpected indentation/content at YAML line {line.line_no}")
        return result

    def _parse_block(self, indent: int) -> object:
        if self.index >= len(self.lines):
            return None
        line = self.lines[self.index]
        if line.indent != indent:
            raise TaxonomyLoadError(f"Unexpected indentation at YAML line {line.line_no}")
        if line.content == "-" or line.content.startswith("- "):
            return self._parse_sequence(indent)
        return self._parse_mapping(indent)

    def _parse_mapping(self, indent: int) -> dict[str, object]:
        result: dict[str, object] = {}
        while self.index < len(self.lines):
            line = self.lines[self.index]
            if line.indent < indent:
                break
            if line.indent > indent:
                raise TaxonomyLoadError(f"Unexpected indentation at YAML line {line.line_no}")
            if line.content == "-" or line.content.startswith("- "):
                break
            key, raw_value = _split_mapping_entry(line.content, line.line_no)
            key = _parse_key(key, line.line_no)
            if key in result:
                raise TaxonomyLoadError(f"Duplicate key {key!r} at YAML line {line.line_no}")
            self.index += 1
            result[key] = self._parse_value(raw_value, indent, line.line_no)
        return result

    def _parse_sequence(self, indent: int) -> list[object]:
        result: list[object] = []
        while self.index < len(self.lines):
            line = self.lines[self.index]
            if line.indent < indent:
                break
            if line.indent != indent or not (line.content == "-" or line.content.startswith("- ")):
                break
            rest = line.content[1:].strip()
            self.index += 1
            if not rest:
                if self.index < len(self.lines) and self.lines[self.index].indent > indent:
                    result.append(self._parse_block(self.lines[self.index].indent))
                else:
                    result.append(None)
                continue
            # A list item may begin a mapping whose remaining keys follow at indent + 2.
            try:
                _split_mapping_entry(rest, line.line_no)
                is_mapping = True
            except TaxonomyLoadError:
                is_mapping = False
            if is_mapping:
                key_raw, value_raw = _split_mapping_entry(rest, line.line_no)
                key = _parse_key(key_raw, line.line_no)
                item: dict[str, object] = {}
                item[key] = self._parse_value(value_raw, indent + 2, line.line_no)
                if self.index < len(self.lines) and self.lines[self.index].indent > indent:
                    tail_indent = self.lines[self.index].indent
                    if tail_indent <= indent:
                        raise TaxonomyLoadError(
                            f"Invalid mapping indentation at line {self.lines[self.index].line_no}"
                        )
                    tail = self._parse_mapping(tail_indent)
                    overlap = item.keys() & tail.keys()
                    if overlap:
                        raise TaxonomyLoadError(
                            f"Duplicate mapping key(s) {sorted(overlap)} "
                            f"after YAML line {line.line_no}"
                        )
                    item.update(tail)
                result.append(item)
            else:
                result.append(_parse_scalar(rest, line.line_no))
                if self.index < len(self.lines) and self.lines[self.index].indent > indent:
                    raise TaxonomyLoadError(
                        "Scalar list item cannot contain nested block "
                        f"(line {self.lines[self.index].line_no})"
                    )
        return result

    def _parse_value(self, raw_value: str, parent_indent: int, line_no: int) -> object:
        if raw_value:
            return _parse_scalar(raw_value, line_no)
        if self.index < len(self.lines) and self.lines[self.index].indent > parent_indent:
            return self._parse_block(self.lines[self.index].indent)
        return None


def _parse_key(text: str, line_no: int) -> str:
    if text.startswith('"'):
        value = _parse_scalar(text, line_no)
        if not isinstance(value, str):
            raise TaxonomyLoadError(f"Invalid mapping key at line {line_no}")
        return value
    if text.startswith("'") and text.endswith("'"):
        return text[1:-1].replace("''", "'")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", text):
        raise TaxonomyLoadError(f"Unsupported mapping key {text!r} at YAML line {line_no}")
    return text


def parse_structured_yaml(source: str | Path) -> object:
    """Parse taxonomy YAML using only the standard library.

    `source` may be a filesystem path or YAML text. If a string matches an
    existing file, it is treated as a path; otherwise it is parsed as text.
    """
    if isinstance(source, Path):
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as exc:
            raise TaxonomyLoadError(f"Cannot read YAML file {source}: {exc}") from exc
    elif isinstance(source, str):
        candidate = Path(source)
        try:
            is_file = "\n" not in source and candidate.is_file()
        except OSError:
            is_file = False
        if is_file:
            try:
                text = candidate.read_text(encoding="utf-8")
            except OSError as exc:
                raise TaxonomyLoadError(f"Cannot read YAML file {candidate}: {exc}") from exc
        else:
            text = source
    else:
        raise TypeError("source must be a str or pathlib.Path")
    return _StructuredYamlParser(text).parse()


def _build_failure_taxonomy(root: object) -> FailureTaxonomyV1:
    data = _mapping(root, "taxonomy")
    expected_keys = {
        "schema_version",
        "taxonomy_version",
        "status",
        "owner",
        "subsystem",
        "single_primary_label_invariant",
        "allow_secondary_findings",
        "forbid_evaluator_as_ground_truth",
        "rca_scores_are_calibrated_probabilities",
        "ground_truth_hierarchy",
        "violation_dispositions",
        "primary_label_precedence",
        "classes",
        "root_cause_candidates",
        "evaluators",
        "research_questions",
        "dataset_leakage_safeguards",
    }
    missing = expected_keys - data.keys()
    extra = data.keys() - expected_keys
    if missing or extra:
        raise TaxonomyLoadError(
            f"Taxonomy root keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    ground_truth: list[GroundTruthSourceSpec] = []
    for i, raw in enumerate(_list(data["ground_truth_hierarchy"], "ground_truth_hierarchy")):
        item = _mapping(raw, f"ground_truth_hierarchy[{i}]")
        ground_truth.append(
            GroundTruthSourceSpec(
                rank=_int(item.get("rank"), f"ground_truth_hierarchy[{i}].rank"),
                source_id=_enum_value(
                    GroundTruthSource,
                    item.get("source_id"),
                    f"ground_truth_hierarchy[{i}].source_id",
                ),
                description=_string(
                    item.get("description"), f"ground_truth_hierarchy[{i}].description"
                ),
                allowed_as_ground_truth=_bool(
                    item.get("allowed_as_ground_truth"),
                    f"ground_truth_hierarchy[{i}].allowed_as_ground_truth",
                ),
            )
        )

    dispositions: list[ViolationDispositionSpec] = []
    for i, raw in enumerate(_list(data["violation_dispositions"], "violation_dispositions")):
        item = _mapping(raw, f"violation_dispositions[{i}]")
        dispositions.append(
            ViolationDispositionSpec(
                disposition_id=_enum_value(
                    ViolationDisposition,
                    item.get("disposition_id"),
                    f"violation_dispositions[{i}].disposition_id",
                ),
                description=_string(
                    item.get("description"), f"violation_dispositions[{i}].description"
                ),
            )
        )

    precedence: list[PrimaryLabelPrecedence] = []
    for i, raw in enumerate(_list(data["primary_label_precedence"], "primary_label_precedence")):
        item = _mapping(raw, f"primary_label_precedence[{i}]")
        precedence.append(
            PrimaryLabelPrecedence(
                rank=_int(item.get("rank"), f"primary_label_precedence[{i}].rank"),
                class_id=_enum_value(
                    FailureClass, item.get("class_id"), f"primary_label_precedence[{i}].class_id"
                ),
                rationale=_string(
                    item.get("rationale"), f"primary_label_precedence[{i}].rationale"
                ),
            )
        )

    classes: list[FailureClassSpec] = []
    for i, raw in enumerate(_list(data["classes"], "classes")):
        item = _mapping(raw, f"classes[{i}]")
        classes.append(
            FailureClassSpec(
                class_id=_enum_value(FailureClass, item.get("class_id"), f"classes[{i}].class_id"),
                is_failure=_bool(item.get("is_failure"), f"classes[{i}].is_failure"),
                applicable_apps=_enum_tuple(
                    item.get("applicable_apps"), ApplicationScope, f"classes[{i}].applicable_apps"
                ),
                precedence_rank=_int(item.get("precedence_rank"), f"classes[{i}].precedence_rank"),
                definition=_string(item.get("definition"), f"classes[{i}].definition"),
                inclusion_criteria=_str_tuple(
                    item.get("inclusion_criteria"), f"classes[{i}].inclusion_criteria"
                ),
                exclusion_criteria=_str_tuple(
                    item.get("exclusion_criteria"), f"classes[{i}].exclusion_criteria"
                ),
                controlled_generation=_string(
                    item.get("controlled_generation"), f"classes[{i}].controlled_generation"
                ),
                primary_metrics=_str_tuple(
                    item.get("primary_metrics"), f"classes[{i}].primary_metrics"
                ),
                expected_evaluator_signals=_str_tuple(
                    item.get("expected_evaluator_signals"),
                    f"classes[{i}].expected_evaluator_signals",
                ),
                required_evidence_ids=_str_tuple(
                    item.get("required_evidence_ids"), f"classes[{i}].required_evidence_ids"
                ),
                allowed_secondary_findings=_enum_tuple(
                    item.get("allowed_secondary_findings"),
                    FailureClass,
                    f"classes[{i}].allowed_secondary_findings",
                ),
                default_rca_candidates=_enum_tuple(
                    item.get("default_rca_candidates"),
                    RootCauseCandidateId,
                    f"classes[{i}].default_rca_candidates",
                ),
            )
        )

    causes: list[RootCauseCandidateSpec] = []
    for i, raw in enumerate(_list(data["root_cause_candidates"], "root_cause_candidates")):
        item = _mapping(raw, f"root_cause_candidates[{i}]")
        causes.append(
            RootCauseCandidateSpec(
                candidate_id=_enum_value(
                    RootCauseCandidateId,
                    item.get("candidate_id"),
                    f"root_cause_candidates[{i}].candidate_id",
                ),
                description=_string(
                    item.get("description"), f"root_cause_candidates[{i}].description"
                ),
                typical_evidence_signals=_str_tuple(
                    item.get("typical_evidence_signals"),
                    f"root_cause_candidates[{i}].typical_evidence_signals",
                ),
                required_evidence_ids=_str_tuple(
                    item.get("required_evidence_ids"),
                    f"root_cause_candidates[{i}].required_evidence_ids",
                ),
                disambiguation_note=_string(
                    item.get("disambiguation_note"),
                    f"root_cause_candidates[{i}].disambiguation_note",
                ),
            )
        )

    evaluators: list[EvaluatorSpec] = []
    for i, raw in enumerate(_list(data["evaluators"], "evaluators")):
        item = _mapping(raw, f"evaluators[{i}]")
        raw_metrics = _list(item.get("output_metrics"), f"evaluators[{i}].output_metrics")
        metrics: list[MetricValueSpec] = []
        for j, raw_metric in enumerate(raw_metrics):
            metric = _mapping(raw_metric, f"evaluators[{i}].output_metrics[{j}]")
            metrics.append(
                MetricValueSpec(
                    metric_name=_string(
                        metric.get("metric_name"),
                        f"evaluators[{i}].output_metrics[{j}].metric_name",
                    ),
                    unit=_string(metric.get("unit"), f"evaluators[{i}].output_metrics[{j}].unit"),
                    direction=_enum_value(
                        MetricDirection,
                        metric.get("direction"),
                        f"evaluators[{i}].output_metrics[{j}].direction",
                    ),
                )
            )
        evaluators.append(
            EvaluatorSpec(
                evaluator_id=_string(item.get("evaluator_id"), f"evaluators[{i}].evaluator_id"),
                family=_enum_value(EvaluatorFamily, item.get("family"), f"evaluators[{i}].family"),
                default_version=_string(
                    item.get("default_version"), f"evaluators[{i}].default_version"
                ),
                applicable_apps=_enum_tuple(
                    item.get("applicable_apps"),
                    ApplicationScope,
                    f"evaluators[{i}].applicable_apps",
                ),
                is_fallible_judge=_bool(
                    item.get("is_fallible_judge"), f"evaluators[{i}].is_fallible_judge"
                ),
                can_be_ground_truth=_bool(
                    item.get("can_be_ground_truth"), f"evaluators[{i}].can_be_ground_truth"
                ),
                required_evidence_ids=_str_tuple(
                    item.get("required_evidence_ids"), f"evaluators[{i}].required_evidence_ids"
                ),
                output_metrics=tuple(metrics),
                dashboard_field_ids=_str_tuple(
                    item.get("dashboard_field_ids"), f"evaluators[{i}].dashboard_field_ids"
                ),
            )
        )

    questions: list[ResearchQuestionSpec] = []
    for i, raw in enumerate(_list(data["research_questions"], "research_questions")):
        item = _mapping(raw, f"research_questions[{i}]")
        questions.append(
            ResearchQuestionSpec(
                rq_id=_string(item.get("rq_id"), f"research_questions[{i}].rq_id"),
                question=_string(item.get("question"), f"research_questions[{i}].question"),
                compared_methods=_str_tuple(
                    item.get("compared_methods"), f"research_questions[{i}].compared_methods"
                ),
                primary_metrics=_str_tuple(
                    item.get("primary_metrics"), f"research_questions[{i}].primary_metrics"
                ),
                falsifiable_null_policy=_string(
                    item.get("falsifiable_null_policy"),
                    f"research_questions[{i}].falsifiable_null_policy",
                ),
            )
        )

    safeguard_data = _mapping(data["dataset_leakage_safeguards"], "dataset_leakage_safeguards")
    ratios = _mapping(
        safeguard_data.get("default_split_ratios"),
        "dataset_leakage_safeguards.default_split_ratios",
    )
    safeguards = DatasetLeakageSafeguards(
        train_ratio=_finite_ratio(ratios.get("train"), "train ratio"),
        validation_ratio=_finite_ratio(ratios.get("validation"), "validation ratio"),
        test_ratio=_finite_ratio(ratios.get("test"), "test ratio"),
        required_split_group_components=_str_tuple(
            safeguard_data.get("required_split_group_components"),
            "required_split_group_components",
        ),
        forbidden_inference_feature_keys=_str_tuple(
            safeguard_data.get("forbidden_inference_feature_keys"),
            "forbidden_inference_feature_keys",
        ),
        paraphrase_grouping_rule=_string(
            safeguard_data.get("paraphrase_grouping_rule"), "paraphrase_grouping_rule"
        ),
        test_freeze_rule=_string(safeguard_data.get("test_freeze_rule"), "test_freeze_rule"),
    )

    taxonomy = FailureTaxonomyV1(
        schema_version=_string(data["schema_version"], "schema_version"),
        taxonomy_version=_string(data["taxonomy_version"], "taxonomy_version"),
        status=_string(data["status"], "status"),
        owner=_string(data["owner"], "owner"),
        subsystem=_string(data["subsystem"], "subsystem"),
        single_primary_label_invariant=_bool(
            data["single_primary_label_invariant"], "single_primary_label_invariant"
        ),
        allow_secondary_findings=_bool(
            data["allow_secondary_findings"], "allow_secondary_findings"
        ),
        forbid_evaluator_as_ground_truth=_bool(
            data["forbid_evaluator_as_ground_truth"], "forbid_evaluator_as_ground_truth"
        ),
        rca_scores_are_calibrated_probabilities=_bool(
            data["rca_scores_are_calibrated_probabilities"],
            "rca_scores_are_calibrated_probabilities",
        ),
        ground_truth_hierarchy=tuple(ground_truth),
        violation_dispositions=tuple(dispositions),
        primary_label_precedence=tuple(precedence),
        classes=tuple(classes),
        root_cause_candidates=tuple(causes),
        evaluators=tuple(evaluators),
        research_questions=tuple(questions),
        dataset_leakage_safeguards=safeguards,
    )
    return taxonomy


def _finite_ratio(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TaxonomyLoadError(f"{context} must be numeric")
    ratio = float(value)
    if not math.isfinite(ratio) or not 0.0 <= ratio <= 1.0:
        raise TaxonomyLoadError(f"{context} must be finite and in [0, 1]")
    return ratio


def load_failure_taxonomy(path: str | Path | None = None) -> FailureTaxonomyV1:
    """Load the canonical taxonomy from an explicit path or package resource."""
    if path is None:
        path = Path(str(resource_files(__package__).joinpath("failure_taxonomy.yaml")))
    raw = parse_structured_yaml(Path(path))
    taxonomy = _build_failure_taxonomy(raw)
    if len(taxonomy.classes) != 9:
        raise TaxonomyLoadError(f"Expected 9 taxonomy classes, got {len(taxonomy.classes)}")
    if len(taxonomy.root_cause_candidates) != 9:
        raise TaxonomyLoadError(
            f"Expected 9 RCA candidates, got {len(taxonomy.root_cause_candidates)}"
        )
    if len(taxonomy.primary_label_precedence) != 9:
        raise TaxonomyLoadError("Expected 9 primary-label precedence entries")
    return taxonomy

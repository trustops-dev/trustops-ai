"""Executable policy matrices for the governance engine (roadmap Week 2).

``tests/fixtures/governance/policy-matrices.json`` is the unit-test form of sections 2 to 5.1 of
``docs/architecture/governance/policy-truth-tables.md``: the three policy truth tables
(``PROC-APPROVAL-01``, ``PROC-TOOL-STAGE-01``, ``PROC-SUPPLIER-01``), the aggregation into the
pre-tool verdict and the combined and conflicting cases. It is written before the engine exists.

Two groups of tests live here.

* Matrix checks run today. They keep the fixture and the spec from drifting apart: every spec row
  is covered or explicitly deferred, every expected result and reason code equals the spec's own
  cell, and the symbolic inputs mean what they say.
* Engine checks run the same matrices through the engine. They are skipped, with the reason shown
  in the pytest summary, until ``ENGINE_MODULE`` exists. The module must expose three functions,
  each taking and returning plain dictionaries: ``evaluate_policy``, ``aggregate`` and ``check``
  (see ``PolicyEngine``). The module path and these signatures are a proposal for the Sprint 2
  engine, not a frozen contract. If the real API differs, adapt it here, not in the matrices.

Scope: spec sections 6 (SC-03 scenarios), 7 (Layer 2 decisions) and 8 (currentness and the OD04
cases) are not policy unit cases and are not covered. Nothing here is runtime validation.
"""

import copy
import importlib
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MATRIX_FILE = REPO_ROOT / "tests" / "fixtures" / "governance" / "policy-matrices.json"
SPEC_FILE = REPO_ROOT / "docs" / "architecture" / "governance" / "policy-truth-tables.md"
ENGINE_MODULE = "trustops_governance.policy.engine"

Json = dict[str, Any]

RESULTS = {"PASS", "FAIL", "NOT_APPLICABLE", "ERROR"}
VERDICTS = {"ALLOW", "BLOCK"}
VERDICT_BASES = {"ALL_APPLICABLE_PASSED", "MANDATORY_POLICY_FAILED", "FAIL_CLOSED_ON_POLICY_ERROR"}
POLICY_IDS = ("PROC-APPROVAL-01", "PROC-TOOL-STAGE-01", "PROC-SUPPLIER-01")
SPEC_PREFIX = {"PROC-APPROVAL-01": "AP", "PROC-TOOL-STAGE-01": "TS", "PROC-SUPPLIER-01": "SU"}
CONFIGURATION_KEYS = ("configuration_present", "configuration_edits")
# The combined-case table of the spec still words its basis column in older terms.
SPEC_BASIS_WORDS = (
    ("satisfied", "ALL_APPLICABLE_PASSED"),
    ("violation", "MANDATORY_POLICY_FAILED"),
    ("evaluation error", "FAIL_CLOSED_ON_POLICY_ERROR"),
)

SPEC_ROW = re.compile(r"^\|\s*((?:AP|TS|SU|AG|CB)-\d+)\s*\|(.*)\|\s*$")
TICKED = re.compile(r"`([^`]+)`")
POLICY_REF = re.compile(r"^((?:AP|TS|SU)-\d+)\s+`(\w+)`")


def _load_matrix() -> Json:
    with MATRIX_FILE.open(encoding="utf-8") as handle:
        matrix: Json = json.load(handle)
    return matrix


MATRIX = _load_matrix()
POLICY_CASES: list[Json] = MATRIX["policy_cases"]
AGGREGATION_CASES: list[Json] = MATRIX["aggregation_cases"]
COMBINED_CASES: list[Json] = MATRIX["combined_cases"]
DEFERRED: list[Json] = MATRIX["deferred"]
CHECK_CASES = POLICY_CASES + COMBINED_CASES


def ids(cases: list[Json]) -> list[str]:
    return [case["id"] for case in cases]


def base_id(case_id: str) -> str:
    """AP-08.a is a variant of the spec row AP-08."""
    return case_id.split(".", 1)[0]


# --- building inputs ----------------------------------------------------------------------


def merge(base: Json, overrides: Json) -> Json:
    """Dicts merge key by key. Everything else, including null and lists, replaces."""
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        current = merged.get(key)
        if isinstance(value, dict) and isinstance(current, dict):
            merged[key] = merge(current, value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def build_input(case: Json) -> Json:
    return merge(MATRIX["baseline"], case["input_overrides"])


def build_aggregation_input(case: Json) -> Json:
    return merge(MATRIX["aggregation_baseline"], case["input_overrides"])


def apply_edit(configuration: Json, edit: Json) -> None:
    """Apply one set or remove edit on a dotted path. The path must already exist."""
    *parents, last = str(edit["path"]).split(".")
    node: Any = configuration
    for part in parents:
        node = node[int(part)] if isinstance(node, list) else node[part]
    key: Any = int(last) if isinstance(node, list) else last
    exists = key in node if isinstance(node, dict) else 0 <= key < len(node)
    if not exists:
        raise KeyError(edit["path"])
    if edit["op"] == "set":
        node[key] = copy.deepcopy(edit["value"])
    elif edit["op"] == "remove":
        del node[key]
    else:
        raise ValueError(f"unknown edit operation {edit['op']!r}")


def build_configuration(check_input: Json) -> Json | None:
    if not check_input["configuration_present"]:
        return None
    configuration: Json = copy.deepcopy(MATRIX["test_configuration"])
    for edit in check_input["configuration_edits"]:
        apply_edit(configuration, edit)
    return configuration


def engine_input(check_input: Json) -> Json:
    return {key: value for key, value in check_input.items() if key not in CONFIGURATION_KEYS}


# --- reading the spec ---------------------------------------------------------------------


def spec_rows() -> dict[str, list[str]]:
    """Cells of every AP, TS, SU, AG and CB table row, keyed by case id, id column removed."""
    rows: dict[str, list[str]] = {}
    for line in SPEC_FILE.read_text(encoding="utf-8").splitlines():
        match = SPEC_ROW.match(line)
        if match:
            rows[match.group(1)] = [cell.strip() for cell in match.group(2).split("|")]
    return rows


def first_ticked(cell: str) -> str | None:
    found = TICKED.search(cell)
    return found.group(1) if found else None


def spec_basis(cell: str) -> str | None:
    tail = cell.partition("/")[2].strip().lower()
    for word, basis in SPEC_BASIS_WORDS:
        if tail.startswith(word):
            return basis
    return None


SPEC_ROWS = spec_rows()


# --- matrix checks: run today -------------------------------------------------------------


def test_spec_tables_were_found() -> None:
    """Guards the parser: a changed table layout must fail here, not pass by matching nothing."""
    assert len(SPEC_ROWS) >= 60
    assert {"AP-19", "TS-09", "SU-08", "AG-13", "CB-11"} <= set(SPEC_ROWS)


def test_case_ids_are_unique() -> None:
    all_ids = ids(POLICY_CASES) + ids(AGGREGATION_CASES) + ids(COMBINED_CASES)
    assert len(all_ids) == len(set(all_ids))


def test_every_spec_row_is_covered_or_deferred_exactly_once() -> None:
    covered = {base_id(case_id) for case_id in ids(CHECK_CASES) + ids(AGGREGATION_CASES)}
    deferred = {item["id"] for item in DEFERRED}
    assert not covered & deferred, "a deferred row must not also have cases"
    assert all(item["reason"] for item in DEFERRED)
    spec = set(SPEC_ROWS)
    assert spec - covered - deferred == set(), "spec rows with no matrix case"
    assert (covered | deferred) - spec == set(), "matrix cases for ids the spec does not have"


@pytest.mark.parametrize("case", POLICY_CASES, ids=ids(POLICY_CASES))
def test_policy_case_agrees_with_its_spec_row(case: Json) -> None:
    row = SPEC_ROWS[base_id(case["id"])]
    expected = case["expected"]
    assert base_id(case["id"]).startswith(SPEC_PREFIX[case["policy"]])
    assert expected["result"] in RESULTS
    assert expected["result"] == first_ticked(row[1])
    assert expected["reason_code"] == first_ticked(row[2])
    if "basis" in expected:
        assert f"basis `{expected['basis']}`" in row[1]


@pytest.mark.parametrize("case", AGGREGATION_CASES, ids=ids(AGGREGATION_CASES))
def test_aggregation_case_agrees_with_its_spec_row(case: Json) -> None:
    row = SPEC_ROWS[base_id(case["id"])]
    expected = case["expected"]
    aggregation_input = build_aggregation_input(case)
    assert set(aggregation_input["policy_results"]) == set(POLICY_IDS)
    assert set(aggregation_input["policy_results"].values()) <= RESULTS
    assert expected["verdict"] in VERDICTS
    assert expected["verdict_basis"] in VERDICT_BASES
    assert expected["verdict"] == first_ticked(row[1])
    assert expected["verdict_basis"] == first_ticked(row[2])


@pytest.mark.parametrize("case", COMBINED_CASES, ids=ids(COMBINED_CASES))
def test_combined_case_agrees_with_its_spec_row(case: Json) -> None:
    row = SPEC_ROWS[base_id(case["id"])]
    expected = case["expected"]
    assert set(expected["policy_results"]) == set(POLICY_IDS)
    assert expected["verdict"] in VERDICTS
    assert expected["verdict_basis"] in VERDICT_BASES
    for policy_id, cell in zip(POLICY_IDS, row[1:4], strict=True):
        expected_policy = expected["policy_results"][policy_id]
        assert expected_policy["result"] in RESULTS
        referenced = POLICY_REF.match(cell)
        if referenced is None:  # the spec cell says "per evidence"
            continue
        assert referenced.group(1).startswith(SPEC_PREFIX[policy_id])
        assert expected_policy["result"] == referenced.group(2)
        assert expected_policy["reason_code"] == first_ticked(SPEC_ROWS[referenced.group(1)][2])
    assert expected["verdict"] == first_ticked(row[4])
    if "basis_differs_from_spec_row" not in case:
        assert expected["verdict_basis"] == spec_basis(row[4])


def test_every_expected_reason_code_is_in_the_spec() -> None:
    spec_text = SPEC_FILE.read_text(encoding="utf-8")
    codes = {case["expected"]["reason_code"] for case in POLICY_CASES}
    for case in COMBINED_CASES:
        codes |= {item["reason_code"] for item in case["expected"]["policy_results"].values()}
    assert {code for code in codes if f"`{code}`" not in spec_text} == set()


@pytest.mark.parametrize("case", CHECK_CASES, ids=ids(CHECK_CASES))
def test_overrides_only_touch_keys_the_baseline_has(case: Json) -> None:
    """A mistyped override key would silently add an unused input and weaken the case."""

    def unknown(base: Json, overrides: Json, path: str) -> list[str]:
        found: list[str] = []
        for key, value in overrides.items():
            if key not in base:
                found.append(f"{path}{key}")
            elif isinstance(value, dict) and isinstance(base[key], dict):
                found += unknown(base[key], value, f"{path}{key}.")
        return found

    assert unknown(MATRIX["baseline"], case["input_overrides"], "") == []


@pytest.mark.parametrize("case", CHECK_CASES, ids=ids(CHECK_CASES))
def test_configuration_edits_apply_to_the_test_configuration(case: Json) -> None:
    check_input = build_input(case)
    configuration = build_configuration(check_input)
    if not check_input["configuration_present"]:
        assert configuration is None
    elif check_input["configuration_edits"]:
        assert configuration != MATRIX["test_configuration"]
    else:
        assert configuration == MATRIX["test_configuration"]


@pytest.mark.parametrize(
    "case",
    [case for case in CHECK_CASES if "amount_relation" in case],
    ids=[case["id"] for case in CHECK_CASES if "amount_relation" in case],
)
def test_amount_relation_matches_the_decimals(case: Json) -> None:
    rule = MATRIX["test_configuration"]["policies"]["PROC-APPROVAL-01"]["currency_rules"][0]
    amount = Decimal(build_input(case)["proposal"]["total_amount"])
    threshold = Decimal(rule["threshold"])
    relation = "ABOVE" if amount > threshold else "EQUAL" if amount == threshold else "BELOW"
    assert relation == case["amount_relation"]


# --- engine checks: skipped until the engine exists ---------------------------------------


class PolicyEngine(Protocol):
    def evaluate_policy(
        self, policy_id: str, check_input: Json, configuration: Json | None
    ) -> Json: ...

    def aggregate(self, aggregation_input: Json) -> Json: ...

    def check(self, check_input: Json, configuration: Json | None) -> Json: ...


def load_engine() -> PolicyEngine | None:
    try:
        module = importlib.import_module(ENGINE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name is not None and ENGINE_MODULE.startswith(exc.name):
            return None
        raise  # the engine exists but one of its own imports is broken
    return cast(PolicyEngine, module)


ENGINE = load_engine()
NO_ENGINE_REASON = f"governance policy engine not implemented yet ({ENGINE_MODULE} not found)"


def engine() -> PolicyEngine:
    if ENGINE is None:
        pytest.skip(NO_ENGINE_REASON)
    return ENGINE


@pytest.mark.parametrize("case", POLICY_CASES, ids=ids(POLICY_CASES))
def test_engine_policy_matrix(case: Json) -> None:
    check_input = build_input(case)
    outcome = engine().evaluate_policy(
        case["policy"], engine_input(check_input), build_configuration(check_input)
    )
    expected = case["expected"]
    assert outcome["result"] == expected["result"]
    assert outcome["reason_code"] == expected["reason_code"]
    if "basis" in expected:
        assert outcome.get("basis") == expected["basis"]


@pytest.mark.parametrize("case", AGGREGATION_CASES, ids=ids(AGGREGATION_CASES))
def test_engine_aggregation_matrix(case: Json) -> None:
    outcome = engine().aggregate(build_aggregation_input(case))
    assert outcome["verdict"] == case["expected"]["verdict"]
    assert outcome["verdict_basis"] == case["expected"]["verdict_basis"]


@pytest.mark.parametrize("case", COMBINED_CASES, ids=ids(COMBINED_CASES))
def test_engine_combined_matrix(case: Json) -> None:
    check_input = build_input(case)
    outcome = engine().check(engine_input(check_input), build_configuration(check_input))
    expected = case["expected"]
    # Every policy is evaluated and recorded, even after the first FAIL (spec section 5).
    assert set(outcome["policy_results"]) == set(expected["policy_results"])
    for policy_id, expected_policy in expected["policy_results"].items():
        assert outcome["policy_results"][policy_id]["result"] == expected_policy["result"]
        assert outcome["policy_results"][policy_id]["reason_code"] == expected_policy["reason_code"]
    assert outcome["verdict"] == expected["verdict"]
    assert outcome["verdict_basis"] == expected["verdict_basis"]

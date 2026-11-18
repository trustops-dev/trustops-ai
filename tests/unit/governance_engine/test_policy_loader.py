"""The policy configuration loader refuses every unusable configuration and accepts the rest.

Each test states one situation the loader can face. A broken configuration must raise a
``PolicyConfigError`` with the right code and path. It must never load with a default that
weakens a policy.
"""

import copy
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

from trustops_governance.policy.loader import (
    load_approval_policy,
    load_policy_set,
    load_policy_set_info,
    load_supplier_policy,
    load_tool_stage_policy,
)
from trustops_governance.policy.policy_schema import (
    POLICY_APPROVAL,
    POLICY_SUPPLIER,
    POLICY_TOOL_STAGE,
    ApprovalRule,
    ConfigErrorCode,
    PolicyConfigError,
    PolicySet,
    PolicyStage,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DRAFT_POLICY_SET = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "governance"
    / "policy-configuration"
    / "procurement-policy-set-v0.1.yaml"
)

MISSING = ConfigErrorCode.POLICY_CONFIG_MISSING
INVALID = ConfigErrorCode.POLICY_CONFIG_INVALID
NOT_ENABLED = ConfigErrorCode.POLICY_CONFIG_NOT_ENABLED

APPROVAL = f"policies.{POLICY_APPROVAL}"
TOOL_STAGE = f"policies.{POLICY_TOOL_STAGE}"
SUPPLIER = f"policies.{POLICY_SUPPLIER}"
RULE_EDIT = f"{APPROVAL}.currency_rules.0"  # dotted form used to edit the configuration
RULE_PATH = f"{APPROVAL}.currency_rules[0]"  # form the loader reports

REMOVE = object()
Loader = Callable[[Any], object]


# --- building configurations --------------------------------------------------------------


def approval_block() -> dict[str, Any]:
    """Every block has at least two keys, so removing one key never empties the block."""
    return {
        "criticality": "critical",
        "comparator": "GT",
        "currency_rules": [
            {
                "currency": "USD",
                "threshold": "1000.00",
                "approval_level": "manager",
                "fraction_digits": 2,
            }
        ],
        "amount_input": {
            "pattern": r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?",
            "positive_only": True,
        },
        "validity": {"time_expiry": "NONE", "ordering": "RECORD_SEQUENCE"},
    }


def tool_stage_block() -> dict[str, Any]:
    return {
        "match": "EXACT_CASE_SENSITIVE",
        "stage_allowlist": {
            "PRE_APPROVAL": ["search_policy", "get_supplier", "request_approval"],
            "APPROVED": ["create_purchase_order"],
            "PO_CREATION": [],
            "COMPLETED": [],
        },
    }


def supplier_block() -> dict[str, Any]:
    return {"criticality": "critical", "eligible_status": "APPROVED"}


def valid_configuration() -> dict[str, Any]:
    """A usable configuration of test values. The policy set is not runtime-enabled."""
    return {
        "policy_set": {"id": "test-policy-set", "version": "test"},
        "policies": {
            POLICY_APPROVAL: approval_block(),
            POLICY_TOOL_STAGE: tool_stage_block(),
            POLICY_SUPPLIER: supplier_block(),
        },
    }


def apply_edit(configuration: dict[str, Any], path: str, value: object) -> dict[str, Any]:
    """Set or REMOVE one value on a dotted path. List positions are written as numbers."""
    *parents, last = path.split(".")
    node: Any = configuration
    for part in parents:
        node = node[int(part)] if isinstance(node, list) else node[part]
    key: Any = int(last) if isinstance(node, list) else last
    if value is REMOVE:
        del node[key]
    else:
        node[key] = value
    return configuration


def edited(path: str, value: object = REMOVE) -> dict[str, Any]:
    return apply_edit(valid_configuration(), path, value)


def runtime_ready_configuration() -> dict[str, Any]:
    configuration = valid_configuration()
    configuration["policy_set"].update(
        runtime_enabled=True,
        accepted_by="reviewer",
        accepted_at="2026-01-01T00:00:00Z",
        acceptance_evidence="record-1",
    )
    return configuration


def refusal(label: str, path: str, value: object, code: ConfigErrorCode, error_path: str) -> Any:
    """One refusal case: the configuration after one edit, the code and the path reported."""
    return pytest.param(edited(path, value), code, error_path, id=label)


def assert_refused(loader: Loader, configuration: Any, code: ConfigErrorCode, path: str) -> None:
    with pytest.raises(PolicyConfigError) as caught:
        loader(configuration)
    assert caught.value.code is code
    assert caught.value.path == path


# --- every policy: the shape of the configuration -----------------------------------------

POLICY_LOADERS = [
    pytest.param(load_approval_policy, POLICY_APPROVAL, id="approval"),
    pytest.param(load_tool_stage_policy, POLICY_TOOL_STAGE, id="tool-stage"),
    pytest.param(load_supplier_policy, POLICY_SUPPLIER, id="supplier"),
]


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        pytest.param(None, MISSING, "configuration", id="no-configuration"),
        pytest.param({}, MISSING, "configuration", id="empty-configuration"),
        pytest.param([], INVALID, "configuration", id="configuration-is-a-list"),
        refusal("policies-absent", "policies", REMOVE, MISSING, "policies"),
        refusal("policies-null", "policies", None, MISSING, "policies"),
        refusal("policies-empty", "policies", {}, MISSING, "policies"),
        refusal("policies-is-a-list", "policies", [], INVALID, "policies"),
    ],
)
@pytest.mark.parametrize(("loader", "policy_id"), POLICY_LOADERS)
def test_every_policy_loader_refuses_a_broken_root(
    loader: Loader, policy_id: str, configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(loader, configuration, code, path)


@pytest.mark.parametrize(
    ("value", "code"),
    [(REMOVE, MISSING), (None, MISSING), ({}, MISSING), ("text", INVALID), ([], INVALID)],
    ids=["absent", "null", "empty", "text", "list"],
)
@pytest.mark.parametrize(("loader", "policy_id"), POLICY_LOADERS)
def test_every_policy_loader_refuses_a_broken_policy_block(
    loader: Loader, policy_id: str, value: object, code: ConfigErrorCode
) -> None:
    configuration = edited(f"policies.{policy_id}", value)
    assert_refused(loader, configuration, code, f"policies.{policy_id}")


# --- PROC-APPROVAL-01 ---------------------------------------------------------------------


def test_approval_policy_loads_exact_decimal_thresholds() -> None:
    policy = load_approval_policy(valid_configuration())
    assert policy.rules == (ApprovalRule("USD", Decimal("1000.00"), "manager", 2),)
    assert str(policy.rules[0].threshold) == "1000.00"
    assert policy.amount_pattern == r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?"


def test_approval_policy_keeps_one_rule_per_currency_in_order() -> None:
    eur = {
        "currency": "EUR",
        "threshold": "900.50",
        "approval_level": "director",
        "fraction_digits": 2,
    }
    configuration = valid_configuration()
    configuration["policies"][POLICY_APPROVAL]["currency_rules"].append(eur)
    rules = load_approval_policy(configuration).rules
    assert [rule.currency for rule in rules] == ["USD", "EUR"]
    assert rules[1].threshold == Decimal("900.50")


def test_approval_policy_ignores_keys_it_does_not_use() -> None:
    configuration = edited(f"{APPROVAL}.unused_setting", "anything")
    assert load_approval_policy(configuration) == load_approval_policy(valid_configuration())


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        refusal(
            "comparator-gte", f"{APPROVAL}.comparator", "GTE", INVALID, f"{APPROVAL}.comparator"
        ),
        refusal(
            "comparator-lowercase",
            f"{APPROVAL}.comparator",
            "gt",
            INVALID,
            f"{APPROVAL}.comparator",
        ),
        refusal(
            "comparator-absent", f"{APPROVAL}.comparator", REMOVE, INVALID, f"{APPROVAL}.comparator"
        ),
        refusal(
            "comparator-null", f"{APPROVAL}.comparator", None, INVALID, f"{APPROVAL}.comparator"
        ),
    ],
)
def test_approval_policy_accepts_only_a_strict_greater_than_comparator(
    configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(load_approval_policy, configuration, code, path)


RULES = f"{APPROVAL}.currency_rules"


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        refusal("rules-absent", RULES, REMOVE, MISSING, RULES),
        refusal("rules-null", RULES, None, MISSING, RULES),
        refusal("rules-empty", RULES, [], MISSING, RULES),
        refusal("rules-is-text", RULES, "USD", INVALID, RULES),
        refusal("rules-is-a-mapping", RULES, {}, INVALID, RULES),
        refusal("rule-is-text", RULE_EDIT, "USD", INVALID, RULE_PATH),
        refusal("rule-is-null", RULE_EDIT, None, INVALID, RULE_PATH),
    ],
)
def test_approval_policy_refuses_missing_or_malformed_currency_rules(
    configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(load_approval_policy, configuration, code, path)


RULE_FIELDS = ["currency", "threshold", "approval_level", "fraction_digits"]


@pytest.mark.parametrize("value", [REMOVE, None], ids=["absent", "null"])
@pytest.mark.parametrize("field", RULE_FIELDS)
def test_approval_rule_refuses_an_absent_or_null_field(field: str, value: object) -> None:
    configuration = edited(f"{RULE_EDIT}.{field}", value)
    assert_refused(load_approval_policy, configuration, INVALID, f"{RULE_PATH}.{field}")


@pytest.mark.parametrize(
    "threshold",
    [
        "",
        " ",
        "abc",
        "1e3",
        " 1000.00",
        "1000.00 ",
        "-5",
        "+5",
        "0",
        "0.00",
        "NaN",
        "1,000",
        1000.0,
        1000,
        True,
    ],
    ids=lambda value: f"threshold-{value!r}",
)
def test_approval_rule_refuses_a_threshold_that_is_not_a_positive_decimal_string(
    threshold: object,
) -> None:
    configuration = edited(f"{RULE_EDIT}.threshold", threshold)
    assert_refused(load_approval_policy, configuration, INVALID, f"{RULE_PATH}.threshold")


@pytest.mark.parametrize("field", ["currency", "approval_level"])
@pytest.mark.parametrize("value", ["", "  ", 5], ids=["empty", "blank", "number"])
def test_approval_rule_refuses_blank_or_non_text_labels(field: str, value: object) -> None:
    configuration = edited(f"{RULE_EDIT}.{field}", value)
    assert_refused(load_approval_policy, configuration, INVALID, f"{RULE_PATH}.{field}")


@pytest.mark.parametrize("digits", [-1, True, "2", 2.0], ids=lambda value: f"digits-{value!r}")
def test_approval_rule_refuses_fraction_digits_that_are_not_a_whole_number(digits: object) -> None:
    configuration = edited(f"{RULE_EDIT}.fraction_digits", digits)
    assert_refused(load_approval_policy, configuration, INVALID, f"{RULE_PATH}.fraction_digits")


def test_approval_policy_refuses_two_rules_for_one_currency() -> None:
    configuration = valid_configuration()
    rules = configuration["policies"][POLICY_APPROVAL]["currency_rules"]
    rules.append(copy.deepcopy(rules[0]))
    assert_refused(load_approval_policy, configuration, INVALID, RULES)


VALIDITY = f"{APPROVAL}.validity"


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        refusal("validity-absent", VALIDITY, REMOVE, MISSING, VALIDITY),
        refusal("validity-null", VALIDITY, None, MISSING, VALIDITY),
        refusal("validity-empty", VALIDITY, {}, MISSING, VALIDITY),
        refusal("validity-is-text", VALIDITY, "NONE", INVALID, VALIDITY),
        refusal(
            "expiry-absent", f"{VALIDITY}.time_expiry", REMOVE, INVALID, f"{VALIDITY}.time_expiry"
        ),
        refusal("expiry-null", f"{VALIDITY}.time_expiry", None, INVALID, f"{VALIDITY}.time_expiry"),
        refusal(
            "expiry-by-time", f"{VALIDITY}.time_expiry", "24h", INVALID, f"{VALIDITY}.time_expiry"
        ),
        refusal(
            "expiry-lowercase",
            f"{VALIDITY}.time_expiry",
            "none",
            INVALID,
            f"{VALIDITY}.time_expiry",
        ),
    ],
)
def test_approval_policy_requires_an_explicit_no_expiry_validity_rule(
    configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(load_approval_policy, configuration, code, path)


AMOUNT_INPUT = f"{APPROVAL}.amount_input"


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        refusal("amount-input-absent", AMOUNT_INPUT, REMOVE, MISSING, AMOUNT_INPUT),
        refusal("amount-input-empty", AMOUNT_INPUT, {}, MISSING, AMOUNT_INPUT),
        refusal("amount-input-is-text", AMOUNT_INPUT, "x", INVALID, AMOUNT_INPUT),
        refusal(
            "pattern-absent", f"{AMOUNT_INPUT}.pattern", REMOVE, INVALID, f"{AMOUNT_INPUT}.pattern"
        ),
        refusal("pattern-empty", f"{AMOUNT_INPUT}.pattern", "", INVALID, f"{AMOUNT_INPUT}.pattern"),
        refusal(
            "pattern-not-a-regex",
            f"{AMOUNT_INPUT}.pattern",
            "([",
            INVALID,
            f"{AMOUNT_INPUT}.pattern",
        ),
        refusal(
            "pattern-is-a-number", f"{AMOUNT_INPUT}.pattern", 5, INVALID, f"{AMOUNT_INPUT}.pattern"
        ),
    ],
)
def test_approval_policy_requires_a_usable_amount_pattern(
    configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(load_approval_policy, configuration, code, path)


def test_the_comparator_is_checked_before_the_currency_rules() -> None:
    configuration = edited(f"{APPROVAL}.comparator", "GTE")
    apply_edit(configuration, RULES, REMOVE)
    assert_refused(load_approval_policy, configuration, INVALID, f"{APPROVAL}.comparator")


def test_the_currency_rules_are_checked_before_the_validity_block() -> None:
    configuration = edited(RULES)
    apply_edit(configuration, VALIDITY, REMOVE)
    assert_refused(load_approval_policy, configuration, MISSING, RULES)


# --- PROC-TOOL-STAGE-01 -------------------------------------------------------------------

ALLOWLIST = f"{TOOL_STAGE}.stage_allowlist"


def test_tool_stage_policy_loads_one_allowlist_per_stage() -> None:
    allowlist = load_tool_stage_policy(valid_configuration()).stage_allowlist
    assert set(allowlist) == set(PolicyStage)
    assert allowlist[PolicyStage.PRE_APPROVAL] == {
        "search_policy",
        "get_supplier",
        "request_approval",
    }
    assert allowlist[PolicyStage.APPROVED] == {"create_purchase_order"}
    assert allowlist[PolicyStage.PO_CREATION] == frozenset()
    assert allowlist[PolicyStage.COMPLETED] == frozenset()


def test_tool_stage_policy_allows_a_stage_with_no_tools() -> None:
    configuration = edited(f"{ALLOWLIST}.PRE_APPROVAL", [])
    allowlist = load_tool_stage_policy(configuration).stage_allowlist
    assert allowlist[PolicyStage.PRE_APPROVAL] == frozenset()


def test_tool_stage_policy_keeps_tool_names_exactly_as_written() -> None:
    configuration = edited(f"{ALLOWLIST}.APPROVED", ["Create_Purchase_Order"])
    approved = load_tool_stage_policy(configuration).stage_allowlist[PolicyStage.APPROVED]
    assert "Create_Purchase_Order" in approved
    assert "create_purchase_order" not in approved


def test_tool_stage_allowlist_cannot_be_changed_after_loading() -> None:
    allowlist: Any = load_tool_stage_policy(valid_configuration()).stage_allowlist
    with pytest.raises(TypeError):
        allowlist[PolicyStage.APPROVED] = frozenset({"anything"})


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        refusal("allowlist-absent", ALLOWLIST, REMOVE, MISSING, ALLOWLIST),
        refusal("allowlist-null", ALLOWLIST, None, MISSING, ALLOWLIST),
        refusal("allowlist-empty", ALLOWLIST, {}, MISSING, ALLOWLIST),
        refusal("allowlist-is-a-list", ALLOWLIST, ["APPROVED"], INVALID, ALLOWLIST),
        refusal("unknown-stage", f"{ALLOWLIST}.SHIPPED", ["x"], INVALID, ALLOWLIST),
        refusal("stage-in-lowercase", f"{ALLOWLIST}.approved", ["x"], INVALID, ALLOWLIST),
    ],
)
def test_tool_stage_policy_refuses_a_missing_or_malformed_allowlist(
    configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(load_tool_stage_policy, configuration, code, path)


@pytest.mark.parametrize("stage", [stage.value for stage in PolicyStage])
def test_tool_stage_policy_refuses_a_stage_without_an_allowlist(stage: str) -> None:
    configuration = edited(f"{ALLOWLIST}.{stage}")
    assert_refused(load_tool_stage_policy, configuration, MISSING, f"{ALLOWLIST}.{stage}")


@pytest.mark.parametrize(
    "tools",
    [None, "create_purchase_order", {"a": 1}, [""], ["  "], [1], [None], ["ok", None]],
    ids=lambda value: f"tools-{value!r}",
)
def test_tool_stage_policy_refuses_a_stage_that_is_not_a_list_of_tool_names(tools: object) -> None:
    configuration = edited(f"{ALLOWLIST}.APPROVED", tools)
    assert_refused(load_tool_stage_policy, configuration, INVALID, f"{ALLOWLIST}.APPROVED")


# --- PROC-SUPPLIER-01 ---------------------------------------------------------------------


def test_supplier_policy_loads_the_eligible_status_exactly() -> None:
    assert load_supplier_policy(valid_configuration()).eligible_status == "APPROVED"
    configuration = edited(f"{SUPPLIER}.eligible_status", "approved")
    assert load_supplier_policy(configuration).eligible_status == "approved"


@pytest.mark.parametrize(
    "value",
    [REMOVE, None, "", "  ", 5, True],
    ids=["absent", "null", "empty", "blank", "number", "boolean"],
)
def test_supplier_policy_refuses_an_unusable_eligible_status(value: object) -> None:
    configuration = edited(f"{SUPPLIER}.eligible_status", value)
    assert_refused(load_supplier_policy, configuration, INVALID, f"{SUPPLIER}.eligible_status")


# --- the policy set and its runtime gate --------------------------------------------------


def test_policy_set_info_defaults_to_not_enabled_and_not_accepted() -> None:
    info = load_policy_set_info(valid_configuration())
    assert (info.id, info.version) == ("test-policy-set", "test")
    assert info.runtime_enabled is False
    assert (info.accepted_by, info.accepted_at, info.acceptance_evidence) == (None, None, None)


@pytest.mark.parametrize(
    ("configuration", "code", "path"),
    [
        refusal("set-absent", "policy_set", REMOVE, MISSING, "policy_set"),
        refusal("set-empty", "policy_set", {}, MISSING, "policy_set"),
        refusal("set-is-a-list", "policy_set", [], INVALID, "policy_set"),
        refusal("id-absent", "policy_set.id", REMOVE, INVALID, "policy_set.id"),
        refusal("id-blank", "policy_set.id", " ", INVALID, "policy_set.id"),
        refusal("version-absent", "policy_set.version", REMOVE, INVALID, "policy_set.version"),
        refusal("version-number", "policy_set.version", 1, INVALID, "policy_set.version"),
        refusal(
            "enabled-as-text",
            "policy_set.runtime_enabled",
            "true",
            INVALID,
            "policy_set.runtime_enabled",
        ),
        refusal(
            "enabled-as-number",
            "policy_set.runtime_enabled",
            1,
            INVALID,
            "policy_set.runtime_enabled",
        ),
        refusal(
            "enabled-null",
            "policy_set.runtime_enabled",
            None,
            INVALID,
            "policy_set.runtime_enabled",
        ),
        refusal(
            "accepted-by-blank", "policy_set.accepted_by", "", INVALID, "policy_set.accepted_by"
        ),
        refusal(
            "accepted-at-number", "policy_set.accepted_at", 5, INVALID, "policy_set.accepted_at"
        ),
    ],
)
def test_policy_set_info_refuses_a_broken_policy_set_block(
    configuration: Any, code: ConfigErrorCode, path: str
) -> None:
    assert_refused(load_policy_set_info, configuration, code, path)


def test_a_set_that_is_not_runtime_enabled_is_refused_without_the_opt_in() -> None:
    assert_refused(
        load_policy_set, valid_configuration(), NOT_ENABLED, "policy_set.runtime_enabled"
    )


def test_the_opt_in_loads_a_set_that_is_not_runtime_enabled() -> None:
    policy_set = load_policy_set(valid_configuration(), allow_disabled=True)
    assert isinstance(policy_set, PolicySet)
    assert policy_set.info.runtime_enabled is False
    assert policy_set.approval == load_approval_policy(valid_configuration())
    assert policy_set.tool_stage == load_tool_stage_policy(valid_configuration())
    assert policy_set.supplier == load_supplier_policy(valid_configuration())


def test_an_enabled_and_accepted_set_loads_without_the_opt_in() -> None:
    policy_set = load_policy_set(runtime_ready_configuration())
    assert policy_set.info.runtime_enabled is True
    assert policy_set.info.accepted_by == "reviewer"
    assert policy_set.info.acceptance_evidence == "record-1"


@pytest.mark.parametrize("value", [REMOVE, None], ids=["absent", "null"])
@pytest.mark.parametrize("field", ["accepted_by", "accepted_at", "acceptance_evidence"])
def test_an_enabled_set_with_an_incomplete_acceptance_record_is_refused(
    field: str, value: object
) -> None:
    configuration = apply_edit(runtime_ready_configuration(), f"policy_set.{field}", value)
    with pytest.raises(PolicyConfigError) as caught:
        load_policy_set(configuration)
    assert caught.value.code is NOT_ENABLED
    assert field in caught.value.detail


def test_the_opt_in_does_not_excuse_an_invalid_policy() -> None:
    configuration = edited(f"{APPROVAL}.comparator", "GTE")
    assert_refused(
        lambda raw: load_policy_set(raw, allow_disabled=True),
        configuration,
        INVALID,
        f"{APPROVAL}.comparator",
    )


def test_a_set_that_is_not_enabled_is_reported_before_its_policy_faults() -> None:
    configuration = edited(f"{APPROVAL}.comparator", "GTE")
    assert_refused(load_policy_set, configuration, NOT_ENABLED, "policy_set.runtime_enabled")


def test_a_missing_configuration_is_missing_for_the_whole_set() -> None:
    assert_refused(load_policy_set, None, MISSING, "configuration")


@pytest.mark.parametrize(
    "loader", [load_tool_stage_policy, load_supplier_policy], ids=["tool-stage", "supplier"]
)
def test_a_fault_in_one_policy_does_not_stop_the_other_policies_loading(loader: Loader) -> None:
    configuration = edited(f"{APPROVAL}.comparator", "GTE")
    assert loader(configuration) is not None


# --- results are safe to share ------------------------------------------------------------


def test_loading_does_not_change_the_configuration_it_was_given() -> None:
    configuration = runtime_ready_configuration()
    before = copy.deepcopy(configuration)
    load_policy_set(configuration)
    assert configuration == before


def test_loaded_models_cannot_be_reassigned() -> None:
    policy = load_approval_policy(valid_configuration())
    with pytest.raises(FrozenInstanceError):
        policy.__setattr__("amount_pattern", "x")


def test_a_configuration_error_names_its_code_and_location() -> None:
    with pytest.raises(PolicyConfigError) as caught:
        load_approval_policy(edited(f"{APPROVAL}.comparator", "GTE"))
    error = caught.value
    assert str(error).startswith("POLICY_CONFIG_INVALID at ")
    assert error.path in str(error)
    assert error.detail in str(error)


# --- the draft policy set in the repository -----------------------------------------------


def load_draft() -> dict[str, Any]:
    raw: dict[str, Any] = yaml.safe_load(DRAFT_POLICY_SET.read_text(encoding="utf-8"))
    return raw


def test_the_draft_policy_set_is_refused_for_runtime_use() -> None:
    assert_refused(load_policy_set, load_draft(), NOT_ENABLED, "policy_set.runtime_enabled")


def test_the_draft_policy_set_loads_with_the_offline_opt_in() -> None:
    raw = load_draft()
    policy_set = load_policy_set(raw, allow_disabled=True)
    configured = raw["policies"][POLICY_APPROVAL]["currency_rules"][0]
    assert policy_set.approval.rules[0].threshold == Decimal(configured["threshold"])
    assert policy_set.approval.rules[0].approval_level == configured["approval_level"]
    assert set(policy_set.tool_stage.stage_allowlist) == set(PolicyStage)
    assert policy_set.supplier.eligible_status == "APPROVED"

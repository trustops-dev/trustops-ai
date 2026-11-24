"""Fail-closed loader for the procurement policy configuration.

The loader takes an already-parsed mapping, so it needs no YAML library and no file access.
It either returns validated models or raises ``PolicyConfigError``. It never fills a gap with a
default that could weaken a policy: an unknown value must not become "approval not required".

Reading a value follows one rule:

* a block that is absent, null or empty is **missing**;
* a block or field of the wrong shape, or a field that is absent, null, blank or of the wrong
  type, is **invalid**;
* a set that is not runtime-enabled and accepted is **not enabled**.

Each policy has its own loader, so a fault in one policy block does not hide the others.
"""

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from ._readers import (
    child_block,
    decimal_text,
    flag,
    invalid,
    missing,
    non_negative_int,
    optional_text,
    require_block,
    text,
)
from .policy_schema import (
    POLICY_APPROVAL,
    POLICY_SUPPLIER,
    POLICY_TOOL_STAGE,
    ApprovalPolicy,
    ApprovalRule,
    ConfigErrorCode,
    PolicyConfigError,
    PolicySet,
    PolicySetInfo,
    PolicyStage,
    SupplierPolicy,
    ToolStagePolicy,
)

Configuration = Mapping[str, Any] | None


def load_policy_set(configuration: Configuration, *, allow_disabled: bool = False) -> PolicySet:
    """Load the whole policy set. A set that is not enabled and accepted is refused.

    ``allow_disabled=True`` is the explicit opt-in for offline and test use.
    """
    info = load_policy_set_info(configuration)
    if not allow_disabled:
        _require_runtime_ready(info)
    return PolicySet(
        info=info,
        approval=load_approval_policy(configuration),
        tool_stage=load_tool_stage_policy(configuration),
        supplier=load_supplier_policy(configuration),
    )


def load_policy_set_info(configuration: Configuration) -> PolicySetInfo:
    root = require_block(configuration, "configuration")
    block = child_block(root, "policy_set", "")
    return PolicySetInfo(
        id=text(block, "id", "policy_set"),
        version=text(block, "version", "policy_set"),
        runtime_enabled=flag(block, "runtime_enabled", "policy_set"),
        accepted_by=optional_text(block, "accepted_by", "policy_set"),
        accepted_at=optional_text(block, "accepted_at", "policy_set"),
        acceptance_evidence=optional_text(block, "acceptance_evidence", "policy_set"),
    )


def _require_runtime_ready(info: PolicySetInfo) -> None:
    if not info.runtime_enabled:
        raise _not_enabled("policy_set.runtime_enabled", "the policy set is not runtime-enabled")
    unrecorded = _unrecorded_acceptance_fields(info)
    if unrecorded:
        detail = f"the acceptance record is incomplete: {', '.join(unrecorded)}"
        raise _not_enabled("policy_set", detail)


def _unrecorded_acceptance_fields(info: PolicySetInfo) -> list[str]:
    recorded = {
        "accepted_by": info.accepted_by,
        "accepted_at": info.accepted_at,
        "acceptance_evidence": info.acceptance_evidence,
    }
    return [name for name, value in recorded.items() if value is None]


def _not_enabled(path: str, detail: str) -> PolicyConfigError:
    return PolicyConfigError(ConfigErrorCode.POLICY_CONFIG_NOT_ENABLED, path, detail)


# --- PROC-APPROVAL-01 ---------------------------------------------------------------------


def load_approval_policy(configuration: Configuration) -> ApprovalPolicy:
    block = _policy_block(configuration, POLICY_APPROVAL)
    path = f"policies.{POLICY_APPROVAL}"
    _require_strict_comparator(block, path)
    rules = _load_rules(block, path)
    _require_no_time_expiry(block, path)
    pattern = _load_amount_pattern(block, path)
    return ApprovalPolicy(version=text(block, "version", path), rules=rules, amount_pattern=pattern)


def _require_strict_comparator(block: Mapping[str, Any], path: str) -> None:
    """Exceeding the threshold is strictly greater-than; no other comparator is accepted."""
    if block.get("comparator") != "GT":
        raise invalid(f"{path}.comparator", "must be GT (strictly greater than)")


def _load_rules(block: Mapping[str, Any], path: str) -> tuple[ApprovalRule, ...]:
    rules_path = f"{path}.currency_rules"
    raw = block.get("currency_rules")
    if raw is None or raw == []:
        raise missing(rules_path, "no currency rules are configured")
    if not isinstance(raw, list):
        raise invalid(rules_path, "must be a list")
    rules = tuple(_load_rule(item, f"{rules_path}[{index}]") for index, item in enumerate(raw))
    _require_unique_currencies(rules, rules_path)
    return rules


def _load_rule(item: object, path: str) -> ApprovalRule:
    if not isinstance(item, Mapping):
        raise invalid(path, "a currency rule must be a mapping")
    return ApprovalRule(
        currency=text(item, "currency", path),
        threshold=decimal_text(item, "threshold", path),
        approval_level=text(item, "approval_level", path),
        fraction_digits=non_negative_int(item, "fraction_digits", path),
    )


def _require_unique_currencies(rules: tuple[ApprovalRule, ...], path: str) -> None:
    currencies = [rule.currency for rule in rules]
    if len(currencies) != len(set(currencies)):
        raise invalid(path, "a currency has more than one rule")


def _require_no_time_expiry(block: Mapping[str, Any], path: str) -> None:
    """The MVP approval never expires by time. The validity block must say so explicitly."""
    validity = child_block(block, "validity", path)
    if validity.get("time_expiry") != "NONE":
        raise invalid(f"{path}.validity.time_expiry", "must be NONE; time expiry is not supported")


def _load_amount_pattern(block: Mapping[str, Any], path: str) -> str:
    amount_input = child_block(block, "amount_input", path)
    pattern_path = f"{path}.amount_input"
    pattern = text(amount_input, "pattern", pattern_path)
    try:
        re.compile(pattern)
    except re.error:
        raise invalid(f"{pattern_path}.pattern", "is not a valid regular expression") from None
    return pattern


# --- PROC-TOOL-STAGE-01 -------------------------------------------------------------------


def load_tool_stage_policy(configuration: Configuration) -> ToolStagePolicy:
    block = _policy_block(configuration, POLICY_TOOL_STAGE)
    path = f"policies.{POLICY_TOOL_STAGE}.stage_allowlist"
    allowlist = child_block(block, "stage_allowlist", f"policies.{POLICY_TOOL_STAGE}")
    _require_known_stages(allowlist, path)
    loaded = {stage: _load_stage_tools(allowlist, stage, path) for stage in PolicyStage}
    version = text(block, "version", f"policies.{POLICY_TOOL_STAGE}")
    return ToolStagePolicy(version=version, stage_allowlist=MappingProxyType(loaded))


def _require_known_stages(allowlist: Mapping[str, Any], path: str) -> None:
    known = {stage.value for stage in PolicyStage}
    unknown = sorted(str(key) for key in allowlist if key not in known)
    if unknown:
        raise invalid(path, f"unknown stage: {', '.join(unknown)}")


def _load_stage_tools(
    allowlist: Mapping[str, Any], stage: PolicyStage, path: str
) -> frozenset[str]:
    stage_path = f"{path}.{stage.value}"
    if stage.value not in allowlist:
        raise missing(stage_path, "no allowlist is configured for this stage")
    tools = allowlist[stage.value]
    if not isinstance(tools, list) or not all(_is_tool_name(tool) for tool in tools):
        raise invalid(stage_path, "must be a list of non-empty tool names")
    return frozenset(tools)


def _is_tool_name(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


# --- PROC-SUPPLIER-01 ---------------------------------------------------------------------


def load_supplier_policy(configuration: Configuration) -> SupplierPolicy:
    block = _policy_block(configuration, POLICY_SUPPLIER)
    path = f"policies.{POLICY_SUPPLIER}"
    eligible_status = text(block, "eligible_status", path)
    return SupplierPolicy(version=text(block, "version", path), eligible_status=eligible_status)


# --- shared -------------------------------------------------------------------------------


def _policy_block(configuration: Configuration, policy_id: str) -> Mapping[str, Any]:
    root = require_block(configuration, "configuration")
    policies = child_block(root, "policies", "")
    return child_block(policies, policy_id, "policies")

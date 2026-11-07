"""Offline workload arithmetic; no API access, quota admission or spend authorization."""

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

FIELDS = (
    "generation_attempts",
    "generation_input_tokens",
    "generation_billable_output_tokens",
    "token_preflight_requests",
    "query_embedding_attempts",
    "query_embedding_input_tokens",
    "index_embedding_attempts",
    "index_embedding_input_tokens",
)


def retries(count, percent):
    return (count * percent + 99) // 100


def cost(row, rates, future=False):
    input_rate = rates[
        "generation_input_from_2027_01_01_usd" if future else "generation_input_per_million_usd"
    ]
    output_rate = rates[
        "generation_output_from_2027_01_01_usd"
        if future
        else "generation_output_including_thinking_per_million_usd"
    ]
    value = (
        Decimal(row["generation_input_tokens"]) * Decimal(input_rate)
        + Decimal(row["generation_billable_output_tokens"]) * Decimal(output_rate)
        + Decimal(row["embedding_input_tokens"]) * Decimal(rates["embedding_input_per_million_usd"])
    ) / Decimal(1_000_000)
    return format(value, "f")


def calculate(cfg, scenario, cap=False):
    p, r, idx = cfg["procurement"], cfg["rag"], cfg["index_build"]
    percent = cfg["retry_reserve_percent"]
    n_p, n_r = scenario["procurement_roots_per_day"], scenario["rag_queries_per_day"]
    days = scenario["days"]
    if cap:
        p_logical, r_logical = n_p * p["logical_generation_cap"], n_r
        p_attempts = n_p * p["generation_attempt_cap"]
        r_attempts = n_r * r["generation_attempt_cap"]
        p_in, r_in = p["input_tokens_per_attempt_cap"], r["input_tokens_per_attempt_cap"]
        p_out = p["largest_profile_output_tokens_cap"]
        r_out = r["largest_profile_output_tokens_cap"]
        query_attempts = n_r * r["query_embedding_attempt_cap"]
        query_tokens = r["query_embedding_native_tokens_cap"]
        index_attempts = (
            idx["prepared_chunk_items_planning_ceiling"] * idx["attempts_per_item_proposed_cap"]
        )
        index_tokens = idx["native_embedding_tokens_per_item_cap"]
    else:
        p_logical = n_p * p["logical_generation_calls_per_root_estimate"]
        r_logical = n_r * r["logical_generation_calls_per_query_estimate"]
        p_attempts, r_attempts = (
            p_logical + retries(p_logical, percent),
            r_logical + retries(r_logical, percent),
        )
        p_in, r_in = p["input_tokens_per_attempt_estimate"], r["input_tokens_per_attempt_estimate"]
        p_out = p["billable_output_tokens_per_attempt_estimate"]
        r_out = r["billable_output_tokens_per_attempt_estimate"]
        query_attempts = n_r + retries(n_r, percent)
        query_tokens = r["query_embedding_native_tokens_estimate"]
        items = idx["prepared_chunk_items_planning_ceiling"]
        index_attempts = items + retries(items, percent)
        index_tokens = idx["native_embedding_tokens_per_item_estimate"]
    row = {
        "scenario": scenario["id"],
        "case": "CONDITIONAL_CAP_EXPOSURE" if cap else "PLANNING_ESTIMATE_WITH_RETRY_RESERVE",
        "days": days,
        "procurement_roots": n_p * days,
        "rag_queries": n_r * days,
        "logical_generation_operations": (p_logical + r_logical) * days,
        "generation_attempts": (p_attempts + r_attempts) * days,
        "generation_input_tokens": (p_attempts * p_in + r_attempts * r_in) * days,
        "generation_billable_output_tokens": (p_attempts * p_out + r_attempts * r_out) * days,
        "token_preflight_requests": (p_logical + r_logical) * days,
        "query_embedding_attempts": query_attempts * days,
        "query_embedding_input_tokens": query_attempts * query_tokens * days,
        "index_builds": scenario["index_builds"],
        "index_prepared_items": idx["prepared_chunk_items_planning_ceiling"]
        * scenario["index_builds"],
        "index_embedding_attempts": index_attempts * scenario["index_builds"],
        "index_embedding_input_tokens": index_attempts * index_tokens * scenario["index_builds"],
        "daily_generation_attempts": p_attempts + r_attempts,
        "daily_query_embedding_attempts": query_attempts,
        "daily_preflight_requests": p_logical + r_logical,
        "daily_procurement_generation_attempts": p_attempts,
        "daily_rag_generation_attempts": r_attempts,
        "runtime_executed": False,
    }
    row["embedding_input_tokens"] = (
        row["query_embedding_input_tokens"] + row["index_embedding_input_tokens"]
    )
    row["modeled_provider_http_attempts"] = (
        row["generation_attempts"]
        + row["token_preflight_requests"]
        + row["query_embedding_attempts"]
        + row["index_embedding_attempts"]
    )
    row["provider_request_count_scope"] = (
        "Modeled generation/preflight/query-embedding/index attempts only; embedding admission overhead unresolved."
    )
    row["paid_token_subtotal_usd_2026"] = cost(row, cfg["rates"])
    row["generation_price_change_sensitivity_usd_2027"] = cost(row, cfg["rates"], future=True)
    row["future_sensitivity_note"] = (
        "Applies published generation change only; holds current embedding rate as an assumption; reverify all rates."
    )
    return row


def validate(cfg):
    assert cfg["live_execution_enabled"] is False
    assert cfg["measurement_status"] == "NO_LIVE_MEASUREMENTS"
    assert type(cfg["retry_reserve_percent"]) is int
    assert 0 <= cfg["retry_reserve_percent"] <= 100
    for group in ("procurement", "rag", "index_build"):
        for key, value in cfg[group].items():
            if type(value) is int:
                assert value >= 0, f"Negative workload value: {group}.{key}"
    for key, value in cfg["rates"].items():
        if key.endswith("_usd"):
            rate = Decimal(value)
            assert rate.is_finite() and rate > 0, f"Invalid listed rate: {key}"
    for name in ("procurement", "rag"):
        c = cfg[name]
        assert c["input_tokens_per_attempt_estimate"] <= c["input_tokens_per_attempt_cap"]
        assert (
            c["billable_output_tokens_per_attempt_estimate"]
            <= c["largest_profile_output_tokens_cap"]
        )
    assert cfg["procurement"]["billable_output_tokens_per_attempt_estimate"] <= 4096
    assert cfg["procurement"]["logical_generation_calls_per_root_estimate"] == 6
    assert cfg["procurement"]["generation_attempt_cap"] == 12
    assert cfg["rag"]["generation_attempt_cap"] == 2
    assert cfg["concurrency"]["provider_attempts_in_flight_across_nour_pilot"] == 1
    assert cfg["index_build"]["actual_prepared_chunk_count"] is None
    for s in cfg["scenarios"]:
        assert all(
            type(s[k]) is int and s[k] >= 0
            for k in ("days", "procurement_roots_per_day", "rag_queries_per_day", "index_builds")
        )
        assert s["days"] > 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path(__file__).with_name("workload-candidate.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    validate(cfg)
    results = [calculate(cfg, s, cap) for s in cfg["scenarios"] for cap in (False, True)]
    for i in range(0, len(results), 2):
        estimate, cap = results[i : i + 2]
        assert all(estimate[k] <= cap[k] for k in FIELDS)
    output = {
        "status": "PASS_OFFLINE_ARITHMETIC_ONLY",
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "runtime_executed": False,
        "account_quota_verified": False,
        "actual_cost_confirmed": False,
        "rounding": "Retry reserves ceil per category per day; USD subtotals use Decimal without intermediate rounding.",
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

"""Offline proposal arithmetic; no provider imports, credentials or network."""

import json
from pathlib import Path


def debit(profile, *, accounting_verified=False):
    total = profile["generation_attempts"] + profile["shared_reserve"]
    if not (accounting_verified and profile["accounting"] == "GENERATION_ONLY_VERIFIED_REQUIRED"):
        total += profile["preflight_attempts"]
    return total


def main():
    config = json.loads(Path(__file__).with_name("workload-candidate.json").read_text())
    checks = []

    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append(name)

    check(
        "free only",
        config["authorized_paid_spend_usd"] == 0 and not config["paid_usage_authorized"],
    )
    check("no automatic fallback", config["fallback_model"] is None)
    check("not live enabled", not config["live_execution_enabled"])
    check(
        "keep selected generation model",
        config["generation_model"] == "gemini-3.8-flash",
    )
    profiles = {p["id"]: p for p in config["profiles"]}
    for name, expected in [
        ("compatibility_day", 10),
        ("procurement_only_day", 20),
        ("rag_only_day", 17),
    ]:
        p = profiles[name]
        check(name + " debit", debit(p) == expected)
        check(name + " daily envelope", debit(p) + p["unallocated"] == 20)
    mixed = profiles["mixed_day_after_accounting_verification"]
    check("mixed blocked before verification", debit(mixed) == 31 and debit(mixed) > 20)
    check("mixed conditional fits", debit(mixed, accounting_verified=True) == 20)
    check("prior smoke does not fit worst case", 2 * 12 + 5 * 2 > 20)
    check("prior daily estimate does not fit", 10 * 6 + 20 > 20)
    check(
        "index worst case",
        config["index_day"]["embedding_attempt_reservation"] == 64 * 2,
    )
    check(
        "index fits proposed daily embedding cap",
        128 <= config["proposed_pilot_limits"]["embedding_daily_attempt_ceiling"] <= 1000,
    )
    check(
        "generation pacing token envelope",
        2 * 32768
        <= config["proposed_pilot_limits"]["generation_input_tokens_per_rolling_minute"]
        <= config["observed_generation_limits"]["input_tpm"],
    )
    check(
        "embedding pacing token envelope",
        2 * 2048
        <= config["proposed_pilot_limits"]["embedding_input_tokens_per_rolling_minute"]
        <= config["observed_embedding_limits"]["input_tpm"],
    )
    check(
        "boundary 21 rejects",
        21 > config["proposed_pilot_limits"]["generation_daily_ceiling"],
    )
    check(
        "boundary 20 fits",
        20 <= config["proposed_pilot_limits"]["generation_daily_ceiling"],
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "checks": checks,
                "check_count": len(checks),
                "runtime_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

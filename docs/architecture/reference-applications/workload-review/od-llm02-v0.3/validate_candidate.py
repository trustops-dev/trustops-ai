"""Validate a proposed workload offline; never execute a model or tool."""

import json
from pathlib import Path


def reservation(config, profile):
    roots = config["root_reservations"]
    generation = (
        profile["procurement_roots"] * roots["procurement"]["generation"]
        + profile["rag_roots"] * roots["rag"]["generation"]
        + profile["extra_generation_attempts"]
    )
    preflight = (
        profile["procurement_roots"] * roots["procurement"]["preflight"]
        + profile["rag_roots"] * roots["rag"]["preflight"]
        + profile["extra_preflights"]
    )
    return generation, preflight, generation + preflight + profile["generation_reserve"]


def admissible(total, quota, occupied):
    if occupied is None or any(type(x) is not int or x < 0 for x in (total, quota, occupied)):
        return False
    return total + occupied <= quota


def main():
    root = Path(__file__).parent
    c = json.loads((root / "candidate.json").read_text())
    results = json.loads((root / "results.json").read_text())
    cases = json.loads((root / "review-cases.json").read_text())
    checked = []

    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checked.append(name)

    check("baseline retained", c["current_proposed_primary"] == "gemini-3.8-flash")
    check("candidate explicit", c["candidate_primary"] == "gemini-3.5-flash-lite")
    check("no live activation", not c["candidate_live_execution_enabled"])
    check(
        "no routing or fallback",
        not c["automatic_routing"] and not c["automatic_fallback"],
    )
    check("zero paid allowance", c["authorized_paid_spend_usd"] == 0)
    check(
        "embedding unchanged",
        c["embedding_candidate"] == "gemini-embedding-001" and c["embedding_dimensions"] == 768,
    )
    expected = [(5, 3, 10), (168, 108, 296), (160, 100, 280)]
    rows = []
    for p, target in zip(c["profiles"], expected, strict=True):
        actual = reservation(c, p)
        check(p["id"] + " arithmetic", actual == target)
        check(
            p["id"] + " fits if exclusive unused quota",
            admissible(actual[2], c["observed_candidate_limits"]["rpd"], 0),
        )
        check(
            p["id"] + " embedding cap",
            p["embedding_attempts"] <= c["pilot_limits"]["embedding_daily_attempts"],
        )
        rows.append(
            {
                "profile": p["id"],
                "generation_attempts": actual[0],
                "preflights": actual[1],
                "reserved_total": actual[2],
            }
        )
    check("unknown occupied quota blocks", not admissible(280, 500, None))
    check("exact boundary accepted", admissible(280, 500, 220))
    check("over boundary rejected", not admissible(280, 500, 221))
    check("negative counts rejected", not admissible(-1, 500, 0))
    check(
        "same workload fails baseline quota",
        not admissible(280, c["observed_baseline_limits"]["rpd"], 0),
    )
    check("regression fixtures distinct", len({x["id"] for x in cases["cases"]}) == 12)
    check("regression repeats explicit", cases["repetitions"] == 2)
    check(
        "results not fabricated",
        results["provider_requests_sent"] == 0
        and not results["primary_model_switched"]
        and all(t["status"] == "NOT_RUN" for t in results["tests"]),
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "check_count": len(checked),
                "checks": checked,
                "profiles": rows,
                "runtime_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

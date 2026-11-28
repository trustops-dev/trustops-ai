"""Offline authored-example checks. Not a runtime or general entailment validator."""

import hashlib
import json
import re
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Literal, Union

import pydantic
from pydantic import ConfigDict, Field, create_model

BASE = Path(__file__).resolve().parent
checks = []
node_count = 0


def unique_members(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member: " + key)
        result[key] = value
    return result


def parse_json(text):
    return json.loads(
        text,
        object_pairs_hook=unique_members,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )


def load(path):
    return parse_json(path.read_text(encoding="utf-8"))


def require(value, message):
    if not value:
        raise ValueError(message)


def check(name, function):
    function()
    checks.append({"name": name, "result": "PASS"})


def rejected(name, function):
    try:
        function()
    except (ValueError, TypeError, KeyError, IndexError):
        checks.append({"name": name, "result": "PASS"})
        return
    raise AssertionError("Negative mutation was accepted: " + name)


def schema_type(schema):
    global node_count
    if "enum" in schema:
        return Literal.__getitem__(tuple(schema["enum"]))
    if "anyOf" in schema:
        return Union[tuple(schema_type(s) for s in schema["anyOf"])]  # noqa: UP007 - dynamic runtime union
    t = schema["type"]
    if t == "object":
        node_count += 1
        fields = {}
        required = schema.get("required", [])
        for name, value in schema["properties"].items():
            constraints = {}
            for source, target in [
                ("minimum", "ge"),
                ("minLength", "min_length"),
                ("pattern", "pattern"),
            ]:
                if source in value:
                    constraints[target] = value[source]
            fields[name] = (
                schema_type(value),
                Field(default=... if name in required else None, **constraints),
            )
        return create_model(
            f"OfflineSchema{node_count}",
            __config__=ConfigDict(extra="forbid", strict=True),
            **fields,
        )
    if t == "array":
        return list[schema_type(schema["items"])]
    return {"string": str, "integer": int, "boolean": bool, "number": float, "null": type(None)}[t]


schema_json = {
    k: load(BASE / "schemas" / f"{k}.schema.json")
    for k in ["procurement-extraction", "procurement-final", "rag-candidate"]
}
models = {k: schema_type(v) for k, v in schema_json.items()}
tool_schemas = load(BASE / "schemas/procurement-tool-arguments.json")
tool_models = {k: schema_type(v) for k, v in tool_schemas.items()}


def typed(name, value):
    models[name].model_validate(value)


def money(value):
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is not None,
        "plain decimal string required",
    )
    require(Decimal(value).is_finite() and Decimal(value) > 0, "positive finite amount required")


def extraction(value):
    typed("procurement-extraction", value)
    keys = ["item_description", "quantity", "total_amount", "currency", "supplier_id"]
    missing = [k for k in keys if value[k] is None]
    require(
        len(value["missing_fields"]) == len(set(value["missing_fields"])),
        "duplicate missing fields",
    )
    require(set(missing) == set(value["missing_fields"]), "null/missing mismatch")
    require((value["status"] == "COMPLETE") == (not missing), "completion/missing mismatch")
    for key in ["item_description", "supplier_id"]:
        if value[key] is not None:
            require(bool(value[key].strip()), "blank field")
    if value["quantity"] is not None:
        require(
            type(value["quantity"]) is int and value["quantity"] > 0, "positive integer quantity"
        )
    if value["total_amount"] is not None:
        money(value["total_amount"])
    if value["currency"] is not None:
        require(re.fullmatch("[A-Z]{3}", value["currency"]) is not None, "currency shape")


def approval_binding(record, context):
    req = context["request"]
    cal = context["observations"]["calculation"]["data"]
    for key, expected in [
        ("request_revision", req["request_revision"]),
        ("supplier_id", req["supplier_id"]),
        ("amount", req["total_amount"]),
        ("currency", req["currency"]),
        ("approval_level", cal["approval_level"]),
        ("policy_version", cal["policy_version"]),
    ]:
        require(record[key] == expected, "approval binding " + key)
    for key in [
        "approval_id",
        "approval_request_id",
        "approving_actor_ref",
        "decision_timestamp",
        "source_ref",
    ]:
        require(
            isinstance(record[key], str) and bool(record[key].strip()),
            "missing authority reference",
        )
    prior = context["observations"].get("prior_approval_result")
    if prior is not None:
        require(
            record["approval_request_id"] == prior["data"]["approval_request_id"],
            "approval belongs to another existing request",
        )
    # Fixture shape/binding only. Authenticity, expiry and revocation require the accepted runtime contract.


def tool(name, args, context, conditional_contracts_accepted=False):
    require(name in tool_models, "unknown tool")
    tool_models[name].model_validate(args)
    for value in args.values():
        if isinstance(value, str):
            require(bool(value.strip()), "blank argument")
    req = context["request"]
    state = context["state"]
    obs = context["observations"]
    allowed = {
        "search_policy": {"REQUEST_CAPTURED"},
        "get_supplier": {"POLICY_CHECKED"},
        "calculate_approval_level": {"SUPPLIER_CHECKED"},
        "request_approval": {"APPROVAL_CALCULATED", "APPROVAL_PENDING"},
        "create_purchase_order": {"APPROVED"},
    }
    require(state in allowed[name], "invalid fine state")
    for key in set(args) & set(req):
        require(
            type(args[key]) is type(req[key]) and args[key] == req[key], "request mismatch " + key
        )
    if "total_amount" in args:
        money(args["total_amount"])
    if name == "calculate_approval_level":
        require(conditional_contracts_accepted, "D3 permission unaccepted")
    if name == "get_supplier":
        require(
            obs["policy"]["status"] == "MATCHED"
            and obs["policy"]["data"]["applicability"] == "APPLICABLE",
            "policy not usable",
        )
    if name == "request_approval":
        require(conditional_contracts_accepted, "approval boundary unaccepted")
        require(
            obs["calculation"]["status"] == "CALCULATED"
            and obs["calculation"]["data"]["approval_required"] is True,
            "requirement not true",
        )
        if state == "APPROVAL_PENDING":
            require(bool(obs.get("trusted_resume_ref")), "no trusted continuation")
            require(
                args.get("approval_request_id")
                == obs["prior_approval_result"]["data"]["approval_request_id"],
                "wrong observation ID",
            )
        else:
            require("approval_request_id" not in args, "ID supplied for initial request")
    if name == "create_purchase_order":
        require(conditional_contracts_accepted, "authorization contracts unaccepted")
        require(
            obs["supplier"]["status"] == "FOUND"
            and obs["supplier"]["data"]["supplier"]["status"] == "APPROVED",
            "supplier ineligible",
        )
        require(
            obs["supplier"]["data"]["requested_supplier_id"]
            == req["supplier_id"]
            == obs["supplier"]["data"]["supplier"]["supplier_id"],
            "supplier observation belongs to another supplier",
        )
        cal = obs["calculation"]
        require(cal["status"] == "CALCULATED", "requirement unknown")
        require(
            type(cal["data"]["approval_required"]) is bool, "approval requirement must be a boolean"
        )
        require(
            cal["data"]["request_revision"] == req["request_revision"],
            "calculation belongs to another revision",
        )
        require(
            cal["data"]["basis"]["amount"] == req["total_amount"]
            and cal["data"]["basis"]["currency"] == req["currency"],
            "calculation basis does not match request",
        )
        if cal["data"]["approval_required"]:
            require(obs["approval_result"]["status"] == "APPROVED", "approval not observed")
            approved = obs["approval_result"]["data"]
            require(
                approved["decision_status"] == "APPROVED"
                and approved["request_revision"] == req["request_revision"],
                "approval envelope mismatch",
            )
            require(
                approved["calculation_ref"] == cal["data"]["calculation_ref"],
                "approval references another calculation",
            )
            require(
                approved["approval_evidence"]["approval_request_id"]
                == approved["approval_request_id"],
                "approval request identity mismatch",
            )
            approval_binding(obs["approval_result"]["data"]["approval_evidence"], context)
        else:
            require(cal["data"]["approval_required"] is False, "unknown requirement")
    # A passing proposal is still not an ALLOW, dispatch claim or effect.


def rag(value, context):
    typed("rag-candidate", value)
    if value["outcome"] == "ABSTENTION":
        require(value["answer"] == "" and value["claims"] == [], "abstention contains answer")
        require(
            value["abstention_reason"] != "NONE" and bool(value["missing_information"].strip()),
            "missing abstention explanation",
        )
        return
    require(bool(value["answer"]) and bool(value["claims"]), "answer/claims required")
    require(
        value["abstention_reason"] == "NONE" and value["missing_information"] == "",
        "answer discriminant",
    )
    sources = {}
    for s in context["selected_evidence"]:
        key = (s["source_id"], s["chunk_id"], s["source_version"])
        require(key not in sources, "ambiguous source identity")
        require(
            hashlib.sha256(s["text"].encode("utf-8")).hexdigest() == s["content_hash"],
            "source hash mismatch",
        )
        sources[key] = s
    ids = set()
    bindings = {}
    answer = value["answer"]
    for index, claim in enumerate(value["claims"]):
        require(claim["claim_id"] not in ids, "duplicate claim")
        ids.add(claim["claim_id"])
        a, b = claim["answer_start"], claim["answer_end"]
        require(0 <= a < b <= len(answer) and answer[a:b] == claim["text"], "claim span mismatch")
        require(bool(claim["citations"]), "missing citations")
        next_start = (
            value["claims"][index + 1]["answer_start"]
            if index + 1 < len(value["claims"])
            else len(answer)
        )
        for citation in claim["citations"]:
            key = (citation["source_id"], citation["chunk_id"], citation["source_version"])
            require(key in sources, "citation not selected")
            source = sources[key]
            s, e = citation["source_start"], citation["source_end"]
            require(
                0 <= s < e <= len(source["text"]) and source["text"][s:e] == citation["quote"],
                "quote/span mismatch",
            )
            cid = citation["citation_id"]
            binding = (key, s, e, citation["quote"])
            require(cid == source["citation_id"], "citation alias not in input binding")
            require(cid not in bindings or bindings[cid] == binding, "conflicting reused alias")
            bindings[cid] = binding
            require("[" + cid + "]" in answer[b:next_start], "missing/badly bound visible marker")
    # General entailment, relevance and facet coverage are not inferred from structural validity.


def final(value, context, observation):
    typed("procurement-final", value)
    for action in value["claimed_actions"]:
        require(
            observation is not None and observation["status"] in {"CREATED", "ALREADY_EXISTS"},
            "unconfirmed effect",
        )
        d = observation["data"]
        r = context["request"]
        require(
            action["po_id"] == d["po_id"] and action["supporting_result_ref"] == d["result_ref"],
            "wrong result reference",
        )
        for k in ["request_revision", "supplier_id", "quantity", "total_amount", "currency"]:
            require(d[k] == r[k], "PO result binding")
        require(d["mock"] is True, "mock required")


def authored_tool_response(name, response, context):
    """Check the represented field-table variants only, not a shared runtime schema."""
    require(set(response) == {"status", "data", "error"}, "tool envelope fields")
    require(
        response["error"] is None and isinstance(response["data"], dict),
        "expected authored non-error result",
    )
    d = response["data"]
    status = response["status"]
    fields = {
        "search_policy": {
            "query",
            "requested_top_k",
            "returned_count",
            "matches",
            "policy_set_version",
            "retriever_version",
            "applicability",
        },
        "get_supplier": {"requested_supplier_id", "supplier", "directory_version"},
        "calculate_approval_level": {
            "calculation_ref",
            "request_revision",
            "approval_required",
            "approval_level",
            "policy_id",
            "policy_version",
            "basis",
        },
        "request_approval": {
            "approval_request_id",
            "request_revision",
            "calculation_ref",
            "decision_status",
            "approval_evidence",
            "decision_ref",
            "reason",
        },
        "create_purchase_order": {
            "po_id",
            "request_revision",
            "supplier_id",
            "quantity",
            "total_amount",
            "currency",
            "mock",
            "created_at",
            "idempotency_key",
            "result_ref",
        },
    }
    require(set(d) == fields[name], "authored result fields differ from represented table variant")
    if name == "search_policy":
        require(
            status == "MATCHED"
            and d["applicability"] == "APPLICABLE"
            and len(d["matches"]) == d["returned_count"] > 0,
            "policy result inconsistent",
        )
        needed = {
            "policy_id",
            "document_id",
            "source_id",
            "source_version",
            "chunk_id",
            "text",
            "content_hash",
            "locator",
            "rank",
            "score",
            "score_kind",
            "higher_is_better",
            "metadata",
        }
        for p in d["matches"]:
            require(
                set(p) == needed and type(p["rank"]) is int and p["rank"] >= 1,
                "policy evidence fields",
            )
            require(
                hashlib.sha256(p["text"].encode("utf-8")).hexdigest() == p["content_hash"],
                "policy snapshot hash",
            )
            require(
                "title" in p["metadata"] and "domain" in p["metadata"],
                "policy applicability metadata",
            )
    elif name == "get_supplier":
        require(status == "FOUND" and d["supplier"] is not None, "represented lookup is not FOUND")
        require(
            set(d["supplier"])
            == {
                "supplier_id",
                "display_name",
                "status",
                "record_version",
                "source_ref",
                "observed_at",
            },
            "supplier fields",
        )
        require(
            d["supplier"]["status"] in {"APPROVED", "NOT_APPROVED", "UNKNOWN"}, "supplier status"
        )
        require(
            d["supplier"]["supplier_id"]
            == d["requested_supplier_id"]
            == context["request"]["supplier_id"],
            "supplier identity",
        )
    elif name == "calculate_approval_level":
        require(
            status == "CALCULATED" and type(d["approval_required"]) is bool,
            "calculated requirement must be boolean",
        )
        require(
            (d["approval_level"] is None) == (d["approval_required"] is False),
            "calculated level/null mismatch",
        )
        require(
            d["request_revision"] == context["request"]["request_revision"], "calculation revision"
        )
        require(
            set(d["basis"])
            == {"amount", "currency", "threshold", "threshold_currency", "comparator", "rule_ref"},
            "basis fields",
        )
        require(
            d["basis"]["amount"] == context["request"]["total_amount"]
            and d["basis"]["currency"] == context["request"]["currency"],
            "calculation basis mismatch",
        )
    elif name == "request_approval":
        require(
            status in {"PENDING", "APPROVED", "DENIED", "CANCELLED"}
            and status == d["decision_status"],
            "approval decision mismatch",
        )
        require(
            (d["approval_evidence"] is not None) == (status == "APPROVED"),
            "approval evidence nullability",
        )
        require(
            d["request_revision"] == context["request"]["request_revision"], "approval revision"
        )
        if status == "APPROVED":
            require(
                d["approval_evidence"]["approval_request_id"] == d["approval_request_id"],
                "approval request identity mismatch",
            )
            require(
                d["calculation_ref"]
                == context["observations"]["calculation"]["data"]["calculation_ref"],
                "approval calculation reference mismatch",
            )
            approval_binding(d["approval_evidence"], context)
    elif name == "create_purchase_order":
        require(status == "CREATED", "represented PO variant is CREATED")
        for key in ["request_revision", "supplier_id", "quantity", "total_amount", "currency"]:
            require(d[key] == context["request"][key], "PO snapshot mismatch")
        require(d["mock"] is True and bool(d["result_ref"]), "mock/result required")


def batch(proposals):
    require(len(proposals) == 1, "multi-call batch rejected without partial dispatch")


cases = {}
for folder in sorted((BASE / "examples").iterdir()):
    if not folder.is_dir():
        continue
    inp = load(folder / "input.json")
    exp = load(folder / "expected.json")
    review = load(folder / "review.json")
    cases[folder.name] = (inp, exp, review)
    kind = exp["kind"]
    name = folder.name
    if kind == "EXTRACTION":
        check(name + " extraction shape and missingness", lambda i=exp: extraction(i["output"]))
    elif kind == "PROCUREMENT_FINAL_CANDIDATE":
        check(
            name + " record-only supported final candidate",
            lambda e=exp, i=inp: final(
                e["output"],
                i["runtime_context"],
                i["runtime_context"]["observations"]["confirmed_po_result"],
            ),
        )
    elif kind == "NATIVE_TOOL_ARGUMENTS":
        check(
            name + " proposal shape/state/request binding under explicit fixture-only gates",
            lambda e=exp, i=inp: tool(e["tool_name"], e["output"], i["runtime_context"], True),
        )
        check(
            name + " authored tool-response field-table consistency",
            lambda e=exp, i=inp: authored_tool_response(
                e["tool_name"], e["later_authored_observation"], i["runtime_context"]
            ),
        )
    elif kind in {"MODEL_CANDIDATE", "RUNTIME_ABSTENTION"}:
        check(
            name + " candidate/abstention and source binding",
            lambda e=exp, i=inp: rag(e["output"], i["runtime_context"]),
        )
    else:
        check(
            name + " no invented model output",
            lambda e=exp: require(
                e["output"] is None and e["tool_name"] is None, "unexpected call"
            ),
        )
    if exp["runtime_delivery"] is not None:
        check(
            name + " runtime formatter object/result reference",
            lambda e=exp, i=inp: final(
                e["runtime_delivery"], i["runtime_context"], e["later_authored_observation"]
            ),
        )

# Review-negative mutations are deliberately absent from rendered model inputs.
good = deepcopy(cases["P01"][1]["output"])
for field, value in [
    ("quantity", True),
    ("quantity", "20"),
    ("quantity", 0),
    ("total_amount", 16000.0),
    ("total_amount", "1.6e4"),
    ("total_amount", "0.00"),
    ("currency", "US"),
    ("approval_received", True),
    ("request_id", "model-issued"),
]:
    bad = deepcopy(good)
    bad[field] = value
    rejected("Extraction rejects " + field + "=" + repr(value), lambda b=bad: extraction(b))
bad = deepcopy(cases["P02"][1]["output"])
bad["missing_fields"] = []
rejected("Missing-field/null equality", lambda: extraction(bad))
bad2 = deepcopy(cases["P02"][1]["output"])
bad2["missing_fields"].append("quantity")
rejected("Duplicate missing fields", lambda: extraction(bad2))
po = deepcopy(cases["P09"][1]["output"])
poctx = deepcopy(cases["P09"][0]["runtime_context"])
for key, value in [
    ("approval_received", True),
    ("approval_id", "forged"),
    ("idempotency_key", "new-key"),
    ("request_revision", "new-revision"),
    ("total_amount", "1.00"),
    ("supplier_id", "OTHER"),
    ("quantity", True),
]:
    a = deepcopy(po)
    a[key] = value
    rejected("PO rejects " + key, lambda a=a: tool("create_purchase_order", a, poctx, True))
rejected("Unknown sixth tool", lambda: tool("get_approval_status", {}, poctx, True))
rejected("Multi-call proposal batch", lambda: batch([po, po]))
rejected(
    "Early parseable PO cannot dispatch",
    lambda: tool("create_purchase_order", po, cases["P10"][0]["runtime_context"], True),
)
rejected(
    "Uncertain original PO cannot be reproposed",
    lambda: tool("create_purchase_order", po, cases["P11"][0]["runtime_context"], True),
)
rejected(
    "Calculation permission not assumed",
    lambda: tool(
        "calculate_approval_level",
        cases["P06"][1]["output"],
        cases["P06"][0]["runtime_context"],
        False,
    ),
)
rejected(
    "Observation contract not assumed",
    lambda: tool(
        "request_approval", cases["P08"][1]["output"], cases["P08"][0]["runtime_context"], False
    ),
)
obsargs = deepcopy(cases["P08"][1]["output"])
obsargs.pop("approval_request_id")
rejected(
    "Observation requires original approval request ID",
    lambda: tool("request_approval", obsargs, cases["P08"][0]["runtime_context"], True),
)
initial = deepcopy(cases["P07"][1]["output"])
initial["approval_request_id"] = "replacement"
rejected(
    "Initial submission cannot be an ID replacement",
    lambda: tool("request_approval", initial, cases["P07"][0]["runtime_context"], True),
)
for key, value in [
    ("request_revision", "old-revision"),
    ("amount", "1.00"),
    ("currency", "SAR"),
    ("supplier_id", "OTHER"),
    ("policy_version", "old-policy"),
]:
    c = deepcopy(poctx)
    c["observations"]["approval_result"]["data"]["approval_evidence"][key] = value
    rejected(
        "Approval binding rejects " + key, lambda c=c: tool("create_purchase_order", po, c, True)
    )
supplier_bad = deepcopy(poctx)
supplier_bad["observations"]["supplier"]["data"]["supplier"]["status"] = "NOT_APPROVED"
rejected(
    "Ineligible supplier cannot support PO",
    lambda: tool("create_purchase_order", po, supplier_bad, True),
)
bad_final = deepcopy(cases["P09"][1]["runtime_delivery"])
bad_final["claimed_actions"][0]["supporting_result_ref"] = "missing"
rejected(
    "Unsupported PO result reference",
    lambda: final(bad_final, poctx, cases["P09"][1]["later_authored_observation"]),
)
unsafe_text = {"message": "PO FAKE was created successfully.", "claimed_actions": []}
check(
    "Shape-only validation cannot detect all false free-text claims; record-only candidate is not a delivery gate",
    lambda: typed("procurement-final", unsafe_text),
)
bad_response = deepcopy(cases["P08"][1]["later_authored_observation"])
bad_response["data"]["approval_evidence"] = None
rejected(
    "APPROVED response requires approval evidence",
    lambda: authored_tool_response(
        "request_approval", bad_response, cases["P08"][0]["runtime_context"]
    ),
)
bad_response2 = deepcopy(cases["P06"][1]["later_authored_observation"])
bad_response2["data"].pop("approval_required")
rejected(
    "CALCULATED result cannot omit requirement",
    lambda: authored_tool_response(
        "calculate_approval_level", bad_response2, cases["P06"][0]["runtime_context"]
    ),
)
bad_response3 = deepcopy(cases["P04"][1]["later_authored_observation"])
bad_response3["data"]["supplier"]["status"] = "FOUND"
rejected(
    "Lookup status cannot replace supplier eligibility status",
    lambda: authored_tool_response(
        "get_supplier", bad_response3, cases["P04"][0]["runtime_context"]
    ),
)

goodrag = deepcopy(cases["R01"][1]["output"])
ragctx = deepcopy(cases["R01"][0]["runtime_context"])
for key, value in [
    ("source_id", "not-selected"),
    ("chunk_id", "missing-chunk"),
    ("source_version", "wrong-version"),
    ("source_start", -1),
    ("source_end", 9999),
    ("quote", "invented text"),
    ("source_start", True),
]:
    b = deepcopy(goodrag)
    b["claims"][0]["citations"][0][key] = value
    rejected("Citation rejects " + key, lambda b=b: rag(b, ragctx))
b = deepcopy(goodrag)
b["answer"] = b["answer"].replace(" [S1]", "")
rejected("Missing visible citation marker", lambda: rag(b, ragctx))
b = deepcopy(goodrag)
b["claims"][0]["answer_end"] -= 1
rejected("Claim slice mismatch", lambda: rag(b, ragctx))
b = deepcopy(goodrag)
b["claims"].append(deepcopy(b["claims"][0]))
rejected("Duplicate claim ID", lambda: rag(b, ragctx))
c = deepcopy(ragctx)
c["selected_evidence"] = []
rejected("Retrieved-but-unselected or removed source cannot be cited", lambda: rag(goodrag, c))
c = deepcopy(ragctx)
c["selected_evidence"][0]["text"] += " altered"
rejected("Source snapshot hash mismatch", lambda: rag(goodrag, c))
b = deepcopy(cases["R02"][1]["output"])
b["claims"][1]["citations"][0]["citation_id"] = "S1"
rejected("Reused alias cannot change evidence", lambda: rag(b, cases["R02"][0]["runtime_context"]))
c = deepcopy(cases["R02"][0]["runtime_context"])
c["selected_evidence"][1]["citation_id"] = "S1"
b2 = deepcopy(b)
b2["answer"] = b2["answer"].replace("[S2]", "[S1]")
rejected("Same input alias bound to two different source spans", lambda: rag(b2, c))
b = deepcopy(cases["R03"][1]["output"])
b["answer"] = "Guessed warranty is one year."
rejected(
    "Abstention cannot contain an enterprise answer",
    lambda: rag(b, cases["R03"][0]["runtime_context"]),
)
b = deepcopy(goodrag)
b["abstention_reason"] = "INCOMPLETE_SUPPORT"
rejected("ANSWER requires reason NONE", lambda: rag(b, ragctx))
b = deepcopy(cases["R03"][1]["output"])
b["outcome"] = "ERROR"
rejected("Technical ERROR is not a model candidate enum", lambda: rag(b, ragctx))
rejected(
    "Fabricated source mutation is retained but rejected",
    lambda: rag(cases["R07"][1]["later_authored_observation"], cases["R07"][0]["runtime_context"]),
)
for name in ["R01", "R02", "R08", "R09"]:
    value = cases[name][1]["output"]
    check(
        name + " authored claims have verbatim positive support",
        lambda value=value: require(
            all(c["text"] == ci["quote"] for c in value["claims"] for ci in c["citations"]),
            "authored support not verbatim",
        ),
    )
uni = cases["R09"][0]["runtime_context"]["selected_evidence"][0]["text"]
check(
    "Unicode fixture distinguishes code points from bytes and UTF-16 units",
    lambda: require(
        len(uni) < len(uni.encode("utf-16-le")) // 2 < len(uni.encode("utf-8")),
        "fixture lacks differing units",
    ),
)

manifest = load(BASE / "prompt-manifest.json")


def digest(value):
    return hashlib.sha256(
        (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    ).hexdigest()


profile_reference = load(BASE / "schemas/generation-profiles-reference.json")
common_reference = load(BASE / "schemas/generation-configuration-reference.json")
for template in manifest["templates"]:
    p = BASE / "templates" / template["role"]
    check(
        "Template exact-byte hash " + template["role"],
        lambda p=p, t=template: require(
            hashlib.sha256(p.read_bytes()).hexdigest() == t["template_sha256"], "template hash"
        ),
    )
    check(
        "Generation common/profile fingerprint " + template["role"],
        lambda t=template: require(
            t["generation_configuration_sha256"] == digest(common_reference)
            and t["generation_profile_sha256"]
            == digest(profile_reference[t["generation_profile_id"]]),
            "profile hash",
        ),
    )
    if template["output_schema_sha256"] is not None:
        check(
            "Output schema fingerprint " + template["role"],
            lambda t=template: require(
                t["output_schema_sha256"] in {digest(s) for s in schema_json.values()},
                "schema hash",
            ),
        )
    if template["tool_catalog_sha256"] is not None:
        check(
            "Tool catalog fingerprint " + template["role"],
            lambda t=template: require(
                t["tool_catalog_sha256"] == digest(tool_schemas), "catalog hash"
            ),
        )
for item in manifest["examples"]:
    p = BASE / "examples" / item["id"] / "rendered-prompt.txt"
    check(
        "Rendered input hash " + item["id"],
        lambda p=p, item=item: require(
            hashlib.sha256(p.read_bytes()).hexdigest() == item["rendered_prompt_sha256"],
            "render hash",
        ),
    )
    text = p.read_text()
    check(
        "No expected-output file serialized into " + item["id"],
        lambda text=text: require(
            '"expected_output"' not in text
            and '"independent_review_annotation"' not in text
            and '"ground_truth"' not in text,
            "expectation leakage",
        ),
    )
check(
    "Exactly five declared tools",
    lambda: require(
        set(tool_schemas)
        == {
            "search_policy",
            "get_supplier",
            "calculate_approval_level",
            "request_approval",
            "create_purchase_order",
        },
        "catalog changed",
    ),
)
for name, path, value in [
    ("Wrong supplier record", ["supplier", "data", "supplier", "supplier_id"], "OTHER"),
    ("Wrong lookup supplier identity", ["supplier", "data", "requested_supplier_id"], "OTHER"),
    (
        "Approval for another approval request",
        ["approval_result", "data", "approval_evidence", "approval_request_id"],
        "OTHER",
    ),
    ("Approval for another calculation", ["approval_result", "data", "calculation_ref"], "OTHER"),
    (
        "Calculation for another request revision",
        ["calculation", "data", "request_revision"],
        "OTHER",
    ),
    ("String approval requirement", ["calculation", "data", "approval_required"], "false"),
    ("Integer approval requirement", ["calculation", "data", "approval_required"], 1),
    ("Mismatched calculation basis", ["calculation", "data", "basis", "amount"], "1.00"),
    (
        "Conflicting approval envelope status",
        ["approval_result", "data", "decision_status"],
        "PENDING",
    ),
]:
    context = deepcopy(poctx)
    target = context["observations"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    rejected(name, lambda context=context: tool("create_purchase_order", po, context, True))
rejected("Duplicate top-level JSON key", lambda: parse_json('{"quantity":20,"quantity":1}'))
rejected(
    "Duplicate nested JSON key",
    lambda: parse_json('{"data":{"approval_required":false,"approval_required":true}}'),
)
check(
    "Unique JSON members retain exact values",
    lambda: require(
        parse_json('{"quantity":20,"total_amount":"16000.00"}')
        == {"quantity": 20, "total_amount": "16000.00"},
        "parser changed data",
    ),
)
report = {
    "result": "PASS",
    "checks": len(checks),
    "scope": "Authored offline prompt/schema/binding/hash and negative-mutation checks only",
    "python_version": sys.version.split()[0],
    "pydantic_version": pydantic.__version__,
    "templates": len(manifest["templates"]),
    "procurement_examples": sum(k.startswith("P") for k in cases),
    "rag_examples": sum(k.startswith("R") for k in cases),
    "standalone_json_schema_engine": "NOT_RUN; strict Pydantic models constructed from the reused simple schema subset",
    "semantic_note": "Positive claim examples are verbatim supported. No general semantic entailment, relevance, authenticity or approval-validity verifier is implemented by this runner.",
    "live_provider_tools_database": "NOT_RUN",
    "canonical_trace_validation": "PENDING_SHARED_CONTRACT",
    "stakeholder_acceptance": "PENDING",
    "assertions": checks,
}
(BASE / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "assertions"}, indent=2))

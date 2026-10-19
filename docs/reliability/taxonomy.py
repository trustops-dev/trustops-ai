PRIMARY_FAILURE_CLASSES = (
    "NORMAL",
    "RETRIEVAL_FAILURE",
    "HALLUCINATION",
    "TOOL_SELECTION_ERROR",
    "INVALID_TOOL_ARGUMENTS",
    "WORKFLOW_VIOLATION",
    "POLICY_VIOLATION",
    "PROMPT_INJECTION",
    "UNSUPPORTED_COMPLETION",
)


FAILURE_TAXONOMY = {

    "NORMAL": {
        "definition": "The execution satisfies the expected reliability conditions for the scenario.",

        "required_evidence": [
            "expected_scenario",
            "observed_execution",
            "successful_required_events",
        ]
    },


    "RETRIEVAL_FAILURE": {
        "definition": "Required or expected evidence was not retrieved by the retrieval stage.",

        "required_evidence": [
            "retrieval_query",
            "expected_relevant_evidence",
            "retrieved_document_ids",
            "retrieval_ranks_or_scores",
        ]
    },


    "HALLUCINATION": {
        "definition": "The final answer contains a claim that is not adequately supported by the available evidence.",

        "required_evidence": [
            "final_answer",
            "available_evidence",
            "claim_to_evidence_relationship",
        ]
    },


    "TOOL_SELECTION_ERROR": {
        "definition": "The agent selected a tool that is not the expected or permitted tool for the observed task or workflow stage.",

        "required_evidence": [
            "expected_tool",
            "observed_tool",
            "workflow_stage",
        ]
    },


    "INVALID_TOOL_ARGUMENTS": {
        "definition": "The selected tool is appropriate, but one or more tool inputs violate the tool schema or required constraints.",

        "required_evidence": [
            "tool_name",
            "tool_arguments",
            "tool_schema_or_constraints",
        ]
    },


    "WORKFLOW_VIOLATION": {
        "definition": "The observed action or tool sequence violates the expected workflow stage, transition, or approval ordering.",

        "required_evidence": [
            "expected_workflow",
            "observed_workflow",
            "stage_or_transition_evidence",
        ]
    },


    "POLICY_VIOLATION": {
        "definition": "The execution violates an applicable company or system policy according to independent policy evidence.",

        "required_evidence": [
            "applicable_policy",
            "policy_evidence",
            "observed_action",
        ]
    },


    "PROMPT_INJECTION": {
        "definition": "The execution contains evidence of an instruction or content attempting to manipulate the AI system into bypassing intended instructions or controls.",

        "required_evidence": [
            "injection_content_or_instruction",
            "injection_context",
            "observed_or_expected_security_effect",
        ]
    },


    "UNSUPPORTED_COMPLETION": {
        "definition": "The final response claims or implies successful completion of an action without sufficient successful execution evidence.",

        "required_evidence": [
            "final_response",
            "expected_action",
            "tool_call_or_action_result",
        ]
    },
}

def is_valid_primary_label(label: str) -> bool:
    return label in PRIMARY_FAILURE_CLASSES

print(is_valid_primary_label("NORMAL"))
print(is_valid_primary_label("RAG_ERROR"))

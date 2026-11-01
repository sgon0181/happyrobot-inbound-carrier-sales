"""Configure only the new unpublished prototype workflow, using private secrets."""

import json
import time
from service.config import settings, ROOT
from service.scripts.cli_platform import CliPlatform as Platform

WORKFLOW = "01a19476-5384-704b-9c5e-569fd96f9adf"
VERSION = "01a195f7-d2e8-79da-a553-ddbeed310f4d"
HOST = "https://codex-e2e-lab-sg-20261031.fly.dev"
BASE = "/versions/" + VERSION
HANDOFF_LINE = (
    "We have agreed on the rate. A senior representative will review and confirm the booking. "
    "I am now transferring you to a senior representative; this transfer is simulated for the demo."
)
DEFINITIONS = [
    ("verify_carrier", "/carriers/verify", [("mc", "MC digits stated by the caller.")]),
    ("send_code", "/otp/send", []),
    (
        "verify_code",
        "/otp/verify",
        [("code", "The six digits the caller actually read. Preserve leading zeros.")],
    ),
    (
        "find_loads",
        "/loads/search",
        [
            ("equipment", "DRY_VAN, REEFER, FLATBED, STEP_DECK or POWER_ONLY."),
            ("origin_state", "Two-letter state, or blank."),
            ("dest_state", "Two-letter state, or blank."),
        ],
    ),
    (
        "agree_rate",
        "/negotiate",
        [
            ("load_id", "A load from find_loads."),
            ("rate", "Exact whole-number ask, or the current offer on acceptance."),
        ],
    ),
    ("request_booking", "/bookings", []),
    ("finish_call", None, []),
    ("finish_handoff", None, []),
]


def paragraph(text):
    return [{"type": "paragraph", "children": [{"text": text}]}]


def variable(group, name):
    return "{{$var:" + group + "." + name + "}}"


def close_url():
    return [
        {
            "type": "paragraph",
            "children": [
                {"text": HOST + "/calls/"},
                {
                    "type": "variable",
                    "group_id": "current",
                    "variable_id": "run_id",
                    "children": [{"text": ""}],
                },
                {"text": "/close"},
            ],
        }
    ]


def node_map(p):
    nodes = p.request(BASE + "/nodes")["data"]
    by_name = {node["name"]: node for node in nodes}
    if len(by_name) != len(nodes):
        raise ValueError("Duplicate prototype node names")
    return by_name


def wait_for_result_fields(p, tool, action, approved, attempts=60, interval=0.5):
    """Wait for custom-output schema refresh without testing any integration.

    Inspect can briefly return the previous output, including a lone error.
    Such a response must never become the model-visible contract.
    """
    expected = set(approved)
    for attempt in range(attempts):
        response = p.request(BASE + "/tools/" + tool + "/tool-call-result/inspect", {})
        data = response.get("data", response)
        matching = [node for node in data.get("nodes", []) if node.get("node_id") == action]
        if len(matching) == 1:
            node = matching[0]
            paths = [field["path"] for field in node.get("fields", [])]
            if (
                node.get("state") == "valid"
                and set(paths) == expected
                and len(paths) == len(expected)
            ):
                return list(approved)
        if attempt + 1 < attempts:
            time.sleep(interval)
    raise RuntimeError("Approved tool result schema did not become available; visibility unchanged")


def main():
    values = settings()
    p = Platform(values)
    response = p.request("/versions/" + VERSION)
    version = response.get("data", response)
    if version.get("is_live") or version.get("is_published"):
        raise RuntimeError(
            "Fork the prototype to a writable version and refresh its node IDs before configuring"
        )
    nodes = node_map(p)
    prompt_id = nodes["Prompt"]["id"]
    agent_id = nodes["Inbound Voice Agent"]["id"]
    close_id = nodes["Prototype post-call close"]["id"]
    path = "/workflows/" + WORKFLOW + "/variables"
    existing = p.request(path)["data"]
    key = "PROTOTYPE_AGENT_KEY"
    if not any(v["key"] == key for v in existing):
        result = p.request(
            path,
            {
                "key": key,
                "value_development": values["AGENT_API_KEY"],
                "value_staging": values["AGENT_API_KEY"],
                "value_production": values["AGENT_API_KEY"],
                "is_hidden_in_ui": True,
            },
        )
        print("Private prototype workflow key configured")
    token = [
        {
            "type": "paragraph",
            "children": [
                {
                    "type": "variable",
                    "children": [{"text": ""}],
                    "group_id": "use_case_variables",
                    "variable_id": key,
                }
            ],
        }
    ]
    # Finish parent configuration before sampling child tool schemas. Parent
    # changes can invalidate the child outputs used by native inspection.
    text = (ROOT / "happyrobot/prototype-prompt.txt").read_text()
    p.request(
        BASE + "/nodes/" + prompt_id,
        {
            "type": "prompt",
            "prompt_md": text,
            "initial_message": paragraph(
                "Hi, this is HappyRobot Logistics carrier sales. What is your MC number?"
            ),
        },
        "PUT",
    )
    agent = p.request(BASE + "/nodes/" + agent_id)["data"]
    config = agent["configuration"]
    config.update(disable_hangup=False, max_call_duration=540, max_silence_hold_duration=60)
    p.request(
        BASE + "/nodes/" + agent_id,
        {"type": "agent", "event_id": agent["event_id"], "configuration": config},
        "PUT",
    )
    p.request(
        BASE + "/nodes/" + close_id,
        {
            "type": "action",
            "event_id": "01926f2b-2973-7ebf-ada1-e984251e27ec",
            "name": "Prototype post-call close",
            "configuration": {
                "url": close_url(),
                "body": {
                    "raw": '{"run_id":' + variable("current", "run_id") + "}",
                    "contentType": "application/json",
                    "schemaVersion": 2,
                },
                "token": token,
                "authType": "bearer",
                "ignore5XX": False,
                "ignoreTimeouts": False,
                "webhookSchemaVersion": 2,
            },
        },
        "PUT",
    )
    schema = {
        "status": "SCHEMA_EXAMPLE",
        "carrier_name": "SCHEMA_EXAMPLE",
        "code_passed": False,
        "channel": "email",
        "destination": "email on file",
        "offer": 1000,
        "round": 1,
        "final": False,
        "rate": 1000,
        "agreed_rate": 1000,
        "load_id": "SCHEMA_EXAMPLE",
        "handoff_allowed": False,
        "outcome": "SCHEMA_EXAMPLE",
        "confirmation_prompt": "May I book load SCHEMA_EXAMPLE at $1000 total?",
        "end_call_required": False,
        "loads": [
            {
                "load_id": "SCHEMA_EXAMPLE",
                "origin_city": "SCHEMA_EXAMPLE",
                "origin_state": "TX",
                "destination_city": "SCHEMA_EXAMPLE",
                "destination_state": "GA",
                "pickup_datetime": "2099-01-01T00:00:00Z",
                "delivery_datetime": "2099-01-02T00:00:00Z",
                "equipment_type": "DRY_VAN",
                "offer": 1000,
                "weight": 42000,
                "commodity_type": "Freight",
                "num_of_pieces": 20,
                "miles": 800,
                "dimensions": "636 x 96 x 108 in",
                "notes": "SCHEMA_EXAMPLE",
            }
        ],
    }
    configured = []
    for name, route, parameters in DEFINITIONS:
        tool = nodes[name]["id"]
        action = nodes["Prototype " + name]["id"]
        binding_group = nodes[name]["persistent_id"]
        if name == "finish_call":
            parameters = [
                (
                    "closing_message",
                    "The short refusal, outage, test-only result or caller goodbye to say aloud, with no codes or confidential pricing. Senior review uses finish_handoff instead.",
                )
            ]
        descriptions = {
            "find_loads": "Find matching loads after verification. Present one offer, total first, then a short operational summary. Price questions are answered without negotiation or booking tools. For terminal no_match or tms_unavailable, use finish_call with the actual result, then native hangup.",
            "agree_rate": (
                "Use only for complete price acceptance or a genuine counter amount. Rate questions "
                "never call this tool. The latest complete caller turn must explicitly accept "
                "the price or propose a new amount. Is that your final price, Is that final, "
                "and What is the most you can pay are information questions: answer from the "
                "current offer without any tool. On counter or ask_again state the returned offer, ask if it "
                "works, then wait. Say final only when final is true. On agreed confirm that total "
                "and prepare booking permission with request_booking. Never infer acceptance."
            ),
            "request_booking": (
                "Prepare permission after price agreement. On confirmation_required clearly say "
                "Yes, I can do the agreed total, then read the exact confirmation_prompt as the final sentence, "
                "then wait. A fresh natural yes, Sure or Yeah go ahead calls this tool directly. "
                "Rate questions are conversation, not permission, refusal or a closing reason."
            ),
            "finish_call": "Close a refusal, outage, test-only result or clear caller goodbye. Never use for senior_review; use finish_handoff there. NEVER use for pending permission, an unanswered question, hesitation or misunderstanding. Continue helping in those cases. Give the actual public reason in closing_message and the native spoken message, then use native end_conversation.",
            "finish_handoff": "Use ONLY after the backend returns senior_review. This tool plays the complete fixed review and simulated-transfer disclosure and closes the record. Then use native end_conversation. No message arguments or extra speech. Never use for price questions, pending permission, refusals or consent_verified.",
        }
        function = {
            "description": paragraph(
                descriptions.get(
                    name,
                    "Call "
                    + name
                    + " in the required verification, matching, negotiation and handoff order. Only the backend decides.",
                )
            ),
            "parameters": [
                {
                    "name": k,
                    "description": paragraph(d),
                    "required": k not in ("origin_state", "dest_state"),
                    "binding": {"mode": "agent"},
                }
                for k, d in parameters
            ],
            "message": {"type": "none"},
        }
        if name == "finish_call":
            function["message"] = {
                "type": "ai",
                "description": paragraph(
                    "Speak the closing_message argument as the terminal business outcome. Use only the public facts in this conversation. "
                    "Do not ask a question or include a verification code, internal pricing or private information. "
                    "This tool is never for senior_review; finish_handoff handles that outcome with fixed speech. "
                    "Explain the actual refusal, failure, test-only result or caller goodbye briefly, then say goodbye without a transfer."
                ),
            }
        if name == "finish_handoff":
            function["message"] = {
                "type": "fixed",
                "content": paragraph(HANDOFF_LINE),
                "uninterruptible": True,
            }
        p.request(
            BASE + "/nodes/" + tool, {"type": "tool", "name": name, "function": function}, "PUT"
        )
        body = {"run_id": variable("current", "run_id")}
        for field, _ in parameters:
            body[field] = variable(binding_group, field)
        raw = "{" + ",".join(json.dumps(k) + ":" + v for k, v in body.items()) + "}"
        config = {
            "url": paragraph(HOST + route) if route else close_url(),
            "body": {"raw": raw, "contentType": "application/json", "schemaVersion": 2},
            "token": token,
            "authType": "bearer",
            "ignore5XX": False,
            "ignoreTimeouts": False,
            "webhookSchemaVersion": 2,
        }
        p.request(
            BASE + "/nodes/" + action,
            {
                "type": "action",
                "event_id": "01926f2b-2973-7ebf-ada1-e984251e27ec",
                "name": "Prototype " + name,
                "configuration": config,
            },
            "PUT",
        )
        configured.append((name, tool, action))
    # No parent/tool configuration changes follow these samples. Each result is
    # inspected before model visibility is written, without executing any action.
    for name, tool, action in configured:
        p.request(BASE + "/nodes/" + action + "/custom-output", {"data": schema}, "PUT")
        exposed = wait_for_result_fields(p, tool, action, schema)
        p.request(
            BASE + "/tools/" + tool + "/tool-call-result/visibility",
            {"node_id": action, "exposed_fields": exposed},
            "PUT",
        )
        print(name, "configured;", len(exposed), "safe fields")
    print("Prototype workflow configured, still unpublished")


if __name__ == "__main__":
    main()

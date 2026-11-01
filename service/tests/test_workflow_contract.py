"""Static contract checks against the actual sanitized native snapshot."""

import json
import re
import unittest
from service.config import ROOT
from service.scripts.configure_workflow import HANDOFF_LINE


class WorkflowContractTests(unittest.TestCase):
    def test_forked_http_inputs_use_persistent_tool_groups(self):
        snapshot = json.loads((ROOT / "happyrobot/prototype-workflow.json").read_text())
        by_id = {n["id"]: n for n in snapshot["nodes"]}
        checked = 0
        for node in snapshot["nodes"]:
            if not node["name"].startswith("Prototype "):
                continue
            raw = (node.get("configuration", {}).get("body") or {}).get("raw", "")
            for group in re.findall(r"\{\{\$var:([^.:}]+)\.", raw):
                if group == "current":
                    continue
                parent = by_id[node["parent_id"]]
                self.assertEqual(group, parent["persistent_id"], node["name"])
                checked += 1
        self.assertGreaterEqual(checked, 6)

    def test_model_parameters_cannot_supply_call_identity_or_booking_facts(self):
        snapshot = json.loads((ROOT / "happyrobot/prototype-workflow.json").read_text())
        for node in snapshot["nodes"]:
            if node["type"] != "tool":
                continue
            names = {p["name"] for p in node["function"].get("parameters", [])}
            self.assertFalse(
                names & {"run_id", "call_id", "verified", "confirmed", "max_rate", "api_key"}
            )
            if node["name"] == "request_booking":
                self.assertFalse(names)

    def test_general_close_has_ai_guidance_without_own_variable_reference(self):
        snapshot = json.loads((ROOT / "happyrobot/prototype-workflow.json").read_text())
        finish = next(n for n in snapshot["nodes"] if n["name"] == "finish_call")
        parameter = next(
            p for p in finish["function"]["parameters"] if p["name"] == "closing_message"
        )
        self.assertTrue(parameter["required"])
        message = finish["function"]["message"]
        self.assertEqual(message["type"], "ai")
        description = json.dumps(message["description"])
        self.assertIn("closing_message", description)
        self.assertNotIn("group_id", description)

    def test_handoff_speech_is_a_fixed_literal_without_agent_arguments(self):
        snapshot = json.loads((ROOT / "happyrobot/prototype-workflow.json").read_text())
        tool = next(n for n in snapshot["nodes"] if n["name"] == "finish_handoff")
        self.assertEqual(tool["function"]["parameters"], [])
        message = tool["function"]["message"]
        self.assertEqual(message["type"], "fixed")
        self.assertTrue(message["uninterruptible"])
        self.assertEqual(
            message["content"], [{"type": "paragraph", "children": [{"text": HANDOFF_LINE}]}]
        )
        self.assertNotIn("group_id", json.dumps(message))

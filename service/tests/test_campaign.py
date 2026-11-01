"""SIMULATED append-only follow-up booking authorization."""

import unittest
from service.core.campaign import permission


class CampaignTests(unittest.TestCase):
    def data(self):
        return {
            "bookings": {
                "first": {"write_intent_id": "intent-1", "reference": "REF", "cohort": "real"}
            },
            "call_events": {
                "approval": {
                    "action": "live_booking_authorization",
                    "load_id": "LD2",
                    "call_id": None,
                    "baseline_intent_ids": ["intent-1"],
                    "consumed_intent_id": None,
                }
            },
        }

    def test_follow_up_is_exact_load_and_single_use(self):
        data = self.data()
        self.assertIsNone(permission(data, "call-2", "LD3"))
        approval = permission(data, "call-2", "LD2")
        self.assertIsNotNone(approval)
        approval["consumed_intent_id"] = "intent-2"
        self.assertIsNone(permission(data, "call-2", "LD2"))

    def test_later_intent_or_cohort_change_cannot_reset_budget(self):
        data = self.data()
        data["bookings"]["first"]["cohort"] = "synthetic"
        data["bookings"]["second"] = {"write_intent_id": "intent-2"}
        self.assertIsNone(permission(data, "call-2", "LD2"))
        data["call_events"]["approval"]["baseline_intent_ids"] = ["intent-1", "intent-2"]
        self.assertIsNotNone(permission(data, "call-2", "LD2"))
        data["bookings"]["third"] = {"write_intent_id": "intent-3"}
        self.assertIsNone(permission(data, "call-2", "LD2"))

    def test_prior_reference_is_not_automatically_new_permission(self):
        data = self.data()
        data["call_events"] = {}
        self.assertIsNone(permission(data, "call-2", "LD2"))

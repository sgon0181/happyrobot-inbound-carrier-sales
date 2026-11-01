"""Eligibility uses carrier authority, never broker authority alone."""

import unittest

from service.adapters.fmcsa.client import FMCSAClient


class FMCSAPolicyTests(unittest.TestCase):
    def test_active_broker_without_carrier_authority_is_ineligible(self):
        carrier = {
            "statusCode": "A",
            "allowedToOperate": "Y",
            "outOfService": "N",
            "brokerAuthorityStatus": "A",
            "commonAuthorityStatus": "N",
            "contractAuthorityStatus": "N",
        }
        eligible, reason, _ = FMCSAClient.assess(carrier)
        self.assertFalse(eligible)
        self.assertEqual(reason, "carrier_authority_inactive_or_unverified")

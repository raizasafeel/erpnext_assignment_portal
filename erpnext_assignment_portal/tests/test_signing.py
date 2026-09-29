from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal import signing
from erpnext_assignment_portal.constants import SETTINGS

TEST_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f
-----END PRIVATE KEY-----
"""
PATH = "/api/method/erpnext_assignment_checks.api.verify_owner"
SIG = "hXHFnB5WH6S4n4fk9ZigERhOU5XIFeGiI2YQMEnfYrQvyR8b/kesUEQ0D5XqSjKRTXfeU0JaEt+dI2veNda5BA=="


class TestSigning(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)

	@patch.dict(frappe.conf, {"grader_signing_key": TEST_PRIVATE_KEY})
	def test_matches_support_app_vector(self):
		frappe.db.set_single_value(SETTINGS, "signing_key_id", "test")
		h = signing.sign("trial.m.frappe.cloud", PATH, b'{"email":"student@example.com"}', now=1790000000)
		self.assertEqual(
			h,
			{"X-Grader-Key-Id": "test", "X-Grader-Timestamp": "1790000000", "X-Grader-Signature": SIG},
		)

	@patch.dict(frappe.conf, {"grader_signing_key": ""})
	def test_missing_key(self):
		self.assertRaises(frappe.ValidationError, signing.sign, "h", "/p", b"")

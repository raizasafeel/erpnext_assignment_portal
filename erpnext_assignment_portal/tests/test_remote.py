import io
from unittest.mock import MagicMock, patch

import frappe
import requests
import urllib3
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal import remote


def response(status=200, body=b'{"message": {"ok": true}}'):
	r = MagicMock(status_code=status)
	r.raw = io.BytesIO(body)
	r.__enter__.return_value = r
	return r


@patch("erpnext_assignment_portal.remote.sign", return_value={"X-Grader-Key-Id": "k"})
class TestRemote(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		patcher = patch(
			"erpnext_assignment_portal.erpnext_assignment_portal.doctype.grader_settings"
			".grader_settings.GraderSettings.host_patterns",
			return_value=["*.m.frappe.cloud"],
		)
		patcher.start()
		self.addCleanup(patcher.stop)

	def call(self):
		return remote.post_signed("https://rza.m.frappe.cloud", remote.VERIFY_OWNER, {"email": "a@b.c"})

	@patch("erpnext_assignment_portal.remote.requests.post", return_value=response())
	def test_ok_and_call_shape(self, post, sign):
		self.assertEqual(self.call(), {"ok": True})
		kwargs = post.call_args.kwargs
		self.assertEqual(
			post.call_args.args[0], "https://rza.m.frappe.cloud/api/method/" + remote.VERIFY_OWNER
		)
		self.assertFalse(kwargs["allow_redirects"])
		self.assertEqual(kwargs["timeout"], (5, 30))
		self.assertEqual(kwargs["headers"]["Accept-Encoding"], "identity")
		sign.assert_called_once_with(
			"rza.m.frappe.cloud", "/api/method/" + remote.VERIFY_OWNER, kwargs["data"]
		)

	def test_error_mapping(self, sign):
		cases = {
			"timeout": dict(side_effect=requests.Timeout()),
			"unreachable": dict(side_effect=requests.ConnectionError()),
			"not_installed": dict(return_value=response(417)),
			"rejected": dict(return_value=response(403)),
			"bad_response": dict(return_value=response(302)),
		}
		for code, kw in cases.items():
			with self.subTest(code=code), patch("erpnext_assignment_portal.remote.requests.post", **kw):
				with self.assertRaises(remote.RemoteError) as ctx:
					self.call()
				self.assertEqual(ctx.exception.code, code)

	def test_bad_bodies(self, sign):
		for body in (
			b"not json",
			b'{"message": [1]}',
			b"{}",
			b"x" * (remote.MAX_RESPONSE_BYTES + 1),
			b"[" * 100000,
		):
			with (
				self.subTest(body=body[:20]),
				patch("erpnext_assignment_portal.remote.requests.post", return_value=response(body=body)),
			):
				with self.assertRaises(remote.RemoteError) as ctx:
					self.call()
				self.assertEqual(ctx.exception.code, "bad_response")

	def test_read_failures_map_to_codes(self, sign):
		cases = {
			"timeout": urllib3.exceptions.ReadTimeoutError(None, "u", "t"),
			"unreachable": urllib3.exceptions.ProtocolError("reset"),
		}
		for code, exc in cases.items():
			r = response()
			r.raw = MagicMock()
			r.raw.read.side_effect = exc
			with (
				self.subTest(code=code),
				patch("erpnext_assignment_portal.remote.requests.post", return_value=r),
			):
				with self.assertRaises(remote.RemoteError) as ctx:
					self.call()
				self.assertEqual(ctx.exception.code, code)

	@patch("erpnext_assignment_portal.remote.requests.post")
	def test_site_outside_patterns_makes_no_request(self, post, sign):
		for site in ("https://evil.example.com", "https://RZA.m.frappe.cloud/", "http://rza.m.frappe.cloud"):
			with self.subTest(site=site), self.assertRaises(remote.RemoteError) as ctx:
				remote.post_signed(site, remote.VERIFY_OWNER, {})
			self.assertEqual(ctx.exception.code, "rejected")
		post.assert_not_called()
		sign.assert_not_called()

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal.constants import MAX_CHECKS, ROLE, SECTION, SETTINGS


class TestDoctypes(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)

	def make_section(self, filters):
		return frappe.get_doc(
			{
				"doctype": SECTION,
				"slug": "probe-section",
				"title": "Probe",
				"checks": [{"title": "c", "target_doctype": "Warehouse", "filters": filters}],
			}
		)

	def test_check_id_is_assigned_and_stable(self):
		s = self.make_section([["name", "=", "x"]]).insert()
		check_id = s.checks[0].check_id
		self.assertTrue(check_id)
		s.checks[0].title = "renamed"
		s.save()
		self.assertEqual(s.checks[0].check_id, check_id)

	def test_duplicated_check_ids_are_regenerated(self):
		s = self.make_section([["name", "=", "x"]])
		s.append("checks", {"title": "copy", "target_doctype": "Warehouse", "filters": "[]"})
		s.insert()
		first = s.checks[0].check_id
		s.checks[1].check_id = first
		s.save()
		self.assertEqual(s.checks[0].check_id, first)
		self.assertNotEqual(s.checks[1].check_id, first)

	def test_check_id_copied_from_another_section_is_regenerated(self):
		original = self.make_section([["name", "=", "x"]]).insert()
		copy = frappe.copy_doc(original)
		copy.slug = "probe-section-copy"
		copy.checks[0].check_id = original.checks[0].check_id
		copy.insert()
		self.assertTrue(copy.checks[0].check_id)
		self.assertNotEqual(copy.checks[0].check_id, original.checks[0].check_id)

	def test_check_id_is_unique_at_the_db(self):
		self.assertTrue(frappe.get_meta("Grader Check").get_field("check_id").unique)
		a = self.make_section([["name", "=", "x"]]).insert()
		b = self.make_section([["name", "=", "y"]])
		b.slug = "probe-section-b"
		b.insert()
		with self.assertRaises(Exception) as ctx:
			frappe.db.set_value("Grader Check", b.checks[0].name, "check_id", a.checks[0].check_id)
		self.assertTrue(frappe.db.is_duplicate_entry(ctx.exception))

	def test_student_is_indexed_on_run(self):
		self.assertTrue(frappe.get_meta("Grader Run").get_field("student").search_index)

	def test_check_id_is_no_copy(self):
		self.assertTrue(frappe.get_meta("Grader Check").get_field("check_id").no_copy)

	def test_filter_shape_is_validated(self):
		for bad in (
			'"x"',
			'[["name"]]',
			'[["name","regexp","x"]]',
			'[["name","is","maybe"]]',
			'[["name","in","x"]]',
		):
			with self.subTest(bad=bad):
				doc = self.make_section(bad)
				doc.slug = frappe.generate_hash(length=8)
				self.assertRaises(frappe.ValidationError, doc.insert)

	def test_slug_cannot_change(self):
		s = self.make_section([["name", "=", "x"]])
		s.slug = "probe-slug-lock"
		s.insert()
		s.slug = "other"
		try:
			s.save()
		except frappe.CannotChangeConstantError:
			pass
		self.assertEqual(frappe.db.get_value(SECTION, "probe-slug-lock", "slug"), "probe-slug-lock")
		self.assertFalse(frappe.db.exists(SECTION, "other"))

	def test_defaults_seeded(self):
		self.assertTrue(frappe.db.exists("Role", ROLE))
		self.assertIn("*.m.frappe.cloud", frappe.get_single(SETTINGS).host_patterns())

	def test_blank_min_defaults_to_one(self):
		s = self.make_section([["name", "=", "x"]])
		s.checks[0].expected_min = None
		s.insert()
		self.assertEqual(s.checks[0].expected_min, 1)

	def test_bounds_are_validated(self):
		for low, high in ((-1, 0), (5, 2)):
			with self.subTest(low=low, high=high):
				s = self.make_section([["name", "=", "x"]])
				s.checks[0].expected_min = low
				s.checks[0].expected_max = high
				with self.assertRaises(frappe.ValidationError):
					s.insert()

	def test_zero_max_is_no_upper_bound_and_min_equal_max_is_valid(self):
		s = self.make_section([["name", "=", "x"]])
		s.checks[0].expected_max = 0
		s.insert()
		s.checks[0].expected_min = 2
		s.checks[0].expected_max = 2
		s.save()

	def test_published_checks_are_capped(self):
		def build(slug, count, published):
			s = self.make_section([["name", "=", "x"]])
			s.slug = slug
			s.published = published
			s.checks = []
			for i in range(count):
				s.append("checks", {"title": f"c{i}", "target_doctype": "Warehouse", "filters": "[]"})
			return s

		already = frappe.db.count(
			"Grader Check",
			{
				"parenttype": SECTION,
				"parent": ["in", frappe.get_all(SECTION, filters={"published": 1}, pluck="name") or [""]],
			},
		)
		room = MAX_CHECKS - already
		build("probe-cap-a", room, 1).insert()
		with self.assertRaises(frappe.ValidationError):
			build("probe-cap-b", 1, 1).insert()
		build("probe-cap-c", 1, 0).insert()

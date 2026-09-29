from __future__ import annotations

import frappe
from frappe.model.utils.rename_field import rename_field


def execute() -> None:
	if not frappe.db.exists("DocType", "ERPNext Assignment Submission"):
		return
	# `frappe.db.exists("DocType", ...)` only checks the metadata record, not the physical
	# table. Guard against a fresh install where the table hasn't been created yet.
	if not frappe.db.has_table("ERPNext Assignment Submission"):
		return
	cols = frappe.db.get_table_columns("ERPNext Assignment Submission")
	if "day" not in cols:
		return  # already migrated / fresh install
	if "section" not in cols:
		rename_field("ERPNext Assignment Submission", "day", "section")
	else:
		# Model-sync already created `section` (the JSON rename was synced before this
		# post_model_sync patch ran). The legacy `day` column survives as an orphan, so
		# copy its values into `section` where `section` is still unset.
		frappe.db.sql(
			"""UPDATE `tabERPNext Assignment Submission`
			   SET `section` = `day`
			   WHERE (`section` IS NULL OR `section` = '')
			     AND `day` IS NOT NULL AND `day` != ''"""
		)
	# No frappe.db.commit() — the patch runner commits; omitting keeps the patch
	# rollback-safe under FrappeTestCase.

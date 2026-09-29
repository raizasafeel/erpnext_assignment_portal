# Days → Sections migration

The student portal's unit of work changed from **Day** to **Section**. One `ERPNext Assignment`
is now one section (exploded from each top-level key of the legacy per-day `checks` JSON).

## Schema changes
- `ERPNext Assignment`: removed `day`; added `section` (Data, reqd, autoname source), `section_order` (Int), `blurb` (Small Text). Autonamed as the hyphen-slug of `section`, suffixed on collision (`company-setup`, `company-setup-2`).
- `ERPNext Assignment Submission`: `day` (Link) renamed to `section` (Link → ERPNext Assignment). One submission per attempt **per section** (history kept; the UI shows the latest per section).

## Migration patches (`patches/v0_0_1/`, post_model_sync, idempotent)
1. `split_days_into_sections` — explodes each multi-key assignment into one row per section, slices the markdown per section heading, backfills single-key rows.
2. `rename_submission_day_to_section` — `rename_field` when `section` absent, else SQL-copies `day`→`section` (model-sync creates `section` before this patch runs).
3. `split_submissions_by_section` — splits each historical multi-section submission into per-section submissions, re-pointing dangling links.

## API changes
- `get_assignments()` now returns `section`, `section_order`, `blurb`, `total_checks`, `assignment_details` (ordered by `section_order`, then `section`); no longer returns `day`.
- `get_my_submissions()` returns `section` instead of `day`.
- **`grade_day(day)` removed.** Replaced by **`regrade()`** (no args) — a single site-wide re-check that grades every published section in one call and writes one submission per section.

## Environment change
- `erpnext_assignment_portal` was **uninstalled** from `erpnext-grader.localhost`: it shipped a colliding `ERPNext Assignment` DocType (old `day`-unique schema) on the same table, which broke `bench migrate`. `erpnext_assignment_portal` now solely owns the assignment doctypes.

## TODO — docs.frappe.io/learning (per CLAUDE.md docs-update trigger)
- [ ] Document the new `section` / `section_order` / `blurb` fields on `ERPNext Assignment`.
- [ ] Document the `grade_day` → `regrade` whitelisted-endpoint change (breaking; add to release notes).
- [ ] Note `get_assignments` / `get_my_submissions` now return `section`, not `day`.
- [ ] Mark the "Days" concept as removed/replaced by "Sections" in any user-facing guide.

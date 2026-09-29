# ERPNext Assignment Portal

Grader portal for the ERPNext assignment on Frappe School (v2). Students link their Frappe Cloud trial site, run checks against it, and see pass/fail per check. The portal runs on the school site and needs the `lms` app. The trial site runs the companion app `erpnext_assignment_checks`.

Requires Python >= 3.14 (see `pyproject.toml`).

## How it works

1. A student enrolled in the configured course links their trial site at `/assignments-portal/erpnext`.
2. The portal sends a signed request to the trial site to confirm the student is a System Manager there (`verify_owner`).
3. On a run, the portal sends the published checks (target doctype and filters) in a signed request (`run_checks`). The trial site answers with a count per check.
4. The portal compares each count with the check's expected min and max and stores a Grader Run.

The trial site returns counts only, never field values or names. Requests are signed with an Ed25519 key. Only `https` sites on an allowed host pattern are contacted, with no redirects.

## Setup

### Grader Settings

Open Grader Settings on the school site.

| Field | Meaning |
| --- | --- |
| `course` | LMS Course. Only students enrolled in it can use the portal. |
| `signing_key_id` | Id of the key the portal signs with, for example `grader-2026-10`. Must match an id in the trial app's `PUBLIC_KEYS`. |
| `allowed_hosts` | Host patterns a student may link. Installing the app adds `*.m.frappe.cloud` if the table is empty. |
| `run_rate_limit_per_hour` | Runs per student per hour. Default 10. |
| `default_link_days` | Days a new link stays valid. Default 10. Set 0 for no expiry. |

Users with the System Manager or Grader Manager role can manage sections, checks, settings, and student sites.

### Signing key

1. Generate an Ed25519 key pair offline.
2. Put the private key PEM in the school site's `site_config.json` as `grader_signing_key`. On Frappe Cloud, set it in the site config from the dashboard.
3. Set `signing_key_id` in Grader Settings.
4. Put the public key PEM in `PUBLIC_KEYS` in `erpnext_assignment_checks/signing.py`, keyed by the same id, and release the trial app.

The private key is never committed to a repository, and never pasted into chat, tickets, or docs. Only the public key is committed. To rotate, add the new public key in one release of the trial app, switch `signing_key_id` and `grader_signing_key`, then remove the old public key in a later release.

Without `grader_signing_key` and `signing_key_id`, runs and linking fail.

### Importing v1 sections

```
bench --site <site> execute erpnext_assignment_portal.import_v1.run --args "['<path to v1_sections.json>']"
```

The file is a JSON list of v1 section rows. Each row becomes a Grader Section with its checks. Sections that already exist are skipped. The command prints one line per section:

- `<slug>: N checks` for a created section.
- `EXISTS <slug>` for a skipped section.
- `SPLIT ...` when one v1 check with several row matches was split into separate checks. The same-document requirement is dropped.
- `SKIPPED ...` for a v1 entry that could not be converted.
- `DETAILS EMPTY` or `DETAILS MIXED` when the assignment text needs hand editing.

v1 submissions are not migrated.

## Run errors

A failed Grader Run has one of these `error_code` values.

| Code | Meaning | What the student should do |
| --- | --- | --- |
| `unreachable` | The trial site could not be reached. | Check the site is running, then re-check. |
| `timeout` | The trial site did not answer in time. | Try again in a few minutes. |
| `not_installed` | The grader app is missing on the trial site. | Install `erpnext_assignment_checks` on the trial site. |
| `rejected` | The trial site refused the request, or the address is not allowed. | Make sure the app is up to date, then contact the instructor. |
| `bad_response` | The trial site sent a reply the portal could not use. | Update the grader app on the trial site and retry. |
| `internal` | A portal-side failure, or a run stuck for over 10 minutes. | Retry. If it repeats, contact the instructor. |

## Limits

- Runs: `run_rate_limit_per_hour` per student. A second start while a run is in progress returns that run.
- Linking: 10 attempts per student per hour.
- One trial site per student, and one student per site.
- Each check count is capped at 1000 on the trial site.

## Staff actions

Grader Student Site has staff-only fields: `status` (set to Revoked to block the student) and `expires_on`. Revoking or extending needs no action on the trial site. The portal checks both before each run, so a revoked or expired link cannot run and an extension applies on the next run.

## Development

Uses `pre-commit` for ruff and formatting:

```
cd apps/erpnext_assignment_portal
pre-commit install
```

License: MIT

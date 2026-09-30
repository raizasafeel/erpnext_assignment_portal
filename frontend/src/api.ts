import { call } from "frappe-ui"

export interface SectionCheck {
	check_id: string
	title: string
}
export interface Section {
	slug: string
	title: string
	details: string
	checks: SectionCheck[]
}
export interface RunResult {
	section: string
	check_id: string
	passed: number
	found_count: number
	check_error: string | null
}
export interface Run {
	name: string
	status: "Queued" | "Running" | "Done" | "Error" | string
	error_code: string | null
	started_on: string | null
	finished_on: string | null
	passed: number
	total: number
	results: RunResult[]
}
export interface Context {
	user: string
	full_name: string
	site: { site: string; status: string; expires_on: string | null; expired: boolean; revoked: boolean } | null
	last_run: Run | null
}

const m = (name: string) => `erpnext_assignment_portal.api.${name}`
export const getContext = () => call<Context>(m("get_context"))
export const getSections = () => call<Section[]>(m("get_sections"))
export const getRun = (run: string) => call<Run>(m("get_run"), { run })
export const linkSite = (site: string) => call<{ site: string }>(m("link_site"), { site })
export const startRun = () => call<{ run: string }>(m("start_run"))

export interface App {
	name: string
	title: string
	logo: string
	route: string
}
export const getApps = () => call<App[]>("frappe.apps.get_apps")
export const logout = () => call("logout")

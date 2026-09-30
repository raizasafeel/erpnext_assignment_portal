import type { DropdownOptions } from "frappe-ui"
import { h } from "vue"
import type { App } from "../api"
import { __ } from "../translate"

export const PORTAL_APP = "erpnext_assignment_portal"

export interface UserMenuActions {
	relink?: () => void
	logout: () => void
	open: (route: string) => void
}

function appLogo(app: App) {
	return () => h("img", { class: "size-4 shrink-0 rounded-3", src: app.logo, alt: "" })
}

export function isSystemUser(cookie: string = document.cookie): boolean {
	return new URLSearchParams(cookie.split("; ").join("&")).get("system_user") === "yes"
}

export function userMenu(apps: App[], actions: UserMenuActions, systemUser = isSystemUser()): DropdownOptions {
	const others = apps
		.filter((app) => app.name !== PORTAL_APP)
		.map((app) => ({
			label: __(app.title),
			slots: { prefix: appLogo(app) },
			onClick: () => actions.open(app.route),
		}))
	if (systemUser) others.unshift({ label: __("Desk"), slots: { prefix: () => h("span", { class: "lucide-monitor size-4" }) }, onClick: () => actions.open("/app") })
	return [
		{
			icon: "lucide-layout-grid",
			label: __("Apps"),
			submenu: others,
			condition: () => others.length > 0,
		},
		{
			icon: "lucide-link",
			label: __("Link a different site"),
			onClick: () => actions.relink?.(),
			condition: () => Boolean(actions.relink),
		},
		{ icon: "lucide-log-out", label: __("Log out"), onClick: () => actions.logout() },
	]
}

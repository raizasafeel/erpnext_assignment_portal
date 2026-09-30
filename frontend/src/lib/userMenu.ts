import type { ColorScheme, DropdownOptions } from "frappe-ui"
import { h } from "vue"
import type { App } from "../api"
import { __ } from "../translate"

export const PORTAL_APP = "erpnext_assignment_portal"

export interface ThemeControl {
	scheme: ColorScheme
	set: (scheme: ColorScheme) => void
}

export interface UserMenuActions {
	relink?: () => void
	theme?: ThemeControl
	logout: () => void
	open: (route: string) => void
}

function appLogo(app: App) {
	return () => h("img", { class: "size-4 shrink-0 rounded-3", src: app.logo, alt: "" })
}

function themeOptions(theme: ThemeControl) {
	const choices: { value: ColorScheme; label: string; icon: string }[] = [
		{ value: "light", label: __("Light"), icon: "lucide-sun" },
		{ value: "dark", label: __("Dark"), icon: "lucide-moon" },
		{ value: "system", label: __("System"), icon: "lucide-monitor" },
	]
	return choices.map((c) => ({
		label: c.label,
		icon: c.icon,
		selected: theme.scheme === c.value,
		slots: theme.scheme === c.value ? { suffix: () => h("span", { class: "lucide-check size-4", "aria-hidden": "true" }) } : undefined,
		onClick: () => theme.set(c.value),
	}))
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
		{
			icon: "lucide-sun-moon",
			label: __("Theme"),
			submenu: actions.theme ? themeOptions(actions.theme) : [],
			condition: () => Boolean(actions.theme),
		},
		{ icon: "lucide-log-out", label: __("Log out"), onClick: () => actions.logout() },
	]
}

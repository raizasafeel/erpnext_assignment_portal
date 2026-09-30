import { describe, expect, it, vi } from "vitest"
import { isSystemUser, userMenu } from "./userMenu"

const APPS = [
	{ name: "lms", title: "Learning", logo: "/l.svg", route: "/lms" },
	{ name: "erpnext_assignment_portal", title: "Assignment Portal", logo: "/p.svg", route: "/assignments-portal/erpnext" },
]
const actions = () => ({ relink: vi.fn(), logout: vi.fn(), open: vi.fn() })
type Option = {
	label: string
	submenu?: Option[]
	selected?: boolean
	condition?: () => boolean
	onClick?: () => void
}
const find = (menu: unknown, label: string) => (menu as Option[]).find((o) => o.label === label)!

describe("userMenu", () => {
	it("lists the other apps under Apps, never the portal itself", () => {
		const a = actions()
		const apps = find(userMenu(APPS, a, false), "Apps")
		expect(apps.submenu?.map((o) => o.label)).toEqual(["Learning"])
		apps.submenu?.[0].onClick?.()
		expect(a.open).toHaveBeenCalledWith("/lms")
	})
	it("adds Desk only for system users", () => {
		const labels = (system: boolean) => find(userMenu(APPS, actions(), system), "Apps").submenu?.map((o) => o.label)
		expect(labels(true)).toEqual(["Desk", "Learning"])
		expect(labels(false)).toEqual(["Learning"])
	})
	it("hides Apps when there is nowhere else to go", () => {
		expect(find(userMenu(APPS.slice(1), actions(), false), "Apps").condition?.()).toBe(false)
	})
	it("reads the system_user cookie", () => {
		expect(isSystemUser("sid=x; system_user=yes")).toBe(true)
		expect(isSystemUser("sid=x; system_user=no")).toBe(false)
	})
	it("offers light, dark and system themes and marks the current one", () => {
		const set = vi.fn()
		const theme = find(userMenu([], { ...actions(), theme: { scheme: "dark", set } }, false), "Theme")
		expect(theme.submenu?.map((o) => [o.label, o.selected])).toEqual([
			["Light", false],
			["Dark", true],
			["System", false],
		])
		theme.submenu?.[2].onClick?.()
		expect(set).toHaveBeenCalledWith("system")
	})
	it("hides Theme when no control is given", () => {
		expect(find(userMenu([], actions(), false), "Theme").condition?.()).toBe(false)
	})
})

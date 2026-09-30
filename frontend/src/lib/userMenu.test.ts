import { describe, expect, it, vi } from "vitest"
import { isSystemUser, userMenu } from "./userMenu"

const APPS = [
	{ name: "lms", title: "Learning", logo: "/l.svg", route: "/lms" },
	{ name: "erpnext_assignment_portal", title: "Assignment Portal", logo: "/p.svg", route: "/assignments-portal/erpnext" },
]
const actions = () => ({ relink: vi.fn(), logout: vi.fn(), open: vi.fn() })
type Option = { label: string; submenu?: Option[]; condition?: () => boolean; onClick?: () => void }
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
	it("logs out", () => {
		const a = actions()
		find(userMenu([], a, false), "Log out").onClick?.()
		expect(a.logout).toHaveBeenCalledOnce()
	})
	it("reads the system_user cookie", () => {
		expect(isSystemUser("sid=x; system_user=yes")).toBe(true)
		expect(isSystemUser("sid=x; system_user=no")).toBe(false)
	})
})

import { flushPromises, mount } from "@vue/test-utils"
import { toast } from "frappe-ui"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import Portal from "./Portal.vue"

const api = vi.hoisted(() => ({
	getContext: vi.fn(),
	getSections: vi.fn(),
	getRun: vi.fn(),
	startRun: vi.fn(),
	linkSite: vi.fn(),
}))
const realtime = vi.hoisted(() => ({ handler: null as null | ((e: { run: string; status: string }) => void) }))

vi.mock("../api", () => api)
vi.mock("../socket", () => ({
	onRunUpdate: (fn: (e: { run: string; status: string }) => void) => {
		realtime.handler = fn
		return () => {}
	},
}))
vi.mock("vue-router", () => ({ useRoute: () => ({ params: {} }), useRouter: () => ({ replace: vi.fn() }) }))
vi.mock("frappe-ui", async () => {
	const { stub } = await import("../test/stub")
	const names = ["Alert", "Badge", "BottomSheet", "Button", "DesktopShell", "Dialog", "Dropdown", "ItemListRow",
		"LoadingIndicator", "MobileShell", "PageHeader", "Sidebar", "SidebarHeader", "SidebarItem"]
	return { ...Object.fromEntries(names.map((n) => [n, stub(n)])), toast: { success: vi.fn(), error: vi.fn() } }
})
vi.mock("../components/LinkSiteForm.vue", async () => ({ default: (await import("../test/stub")).stub("LinkSiteForm") }))
vi.mock("../components/RunAlert.vue", async () => ({ default: (await import("../test/stub")).stub("RunAlert") }))
vi.mock("../components/SectionPanel.vue", async () => ({ default: (await import("../test/stub")).stub("SectionPanel") }))

const SECTIONS = [{ slug: "wh", title: "Warehouses", details: "", checks: [{ check_id: "1", title: "Mumbai" }] }]
const run = (status: string) => ({
	name: "r1", status, error_code: null, started_on: null, finished_on: null, passed: 0, total: 1, results: [],
})
const context = (over = {}) => ({
	user: "s@example.com", full_name: "S",
	site: { site: "https://s.m.frappe.cloud", status: "Active", expires_on: null, expired: false },
	last_run: null, ...over,
})

function setScreen(mobile: boolean) {
	window.matchMedia = vi.fn().mockReturnValue({ matches: mobile, addEventListener: vi.fn(), removeEventListener: vi.fn() })
}

function render() {
	return mount(Portal, { global: { mocks: { __: (s: string) => s } } })
}

const has = (w: ReturnType<typeof render>, name: string) => w.find(`[data-stub="${name}"]`).exists()
const stillRunning = (w: ReturnType<typeof render>) => w.findComponent({ name: "RunAlert" }).vm.$attrs["still-running"]

describe("Portal", () => {
	beforeEach(() => {
		vi.clearAllMocks()
		setScreen(false)
		api.getSections.mockResolvedValue(SECTIONS)
	})
	afterEach(() => {
		vi.useRealTimers()
	})

	it("shows the loader until the context arrives", () => {
		api.getContext.mockReturnValue(new Promise(() => {}))
		expect(has(render(), "LoadingIndicator")).toBe(true)
	})

	it("shows the not-enrolled alert when get_context is forbidden", async () => {
		api.getContext.mockRejectedValue(Object.assign(new Error("no"), { exc_type: "PermissionError" }))
		const w = render()
		await flushPromises()
		expect(w.find('[data-title="You are not enrolled"]').exists()).toBe(true)
		expect(has(w, "LinkSiteForm")).toBe(false)
	})

	it("shows the link form when no site is linked", async () => {
		api.getContext.mockResolvedValue(context({ site: null }))
		const w = render()
		await flushPromises()
		expect(has(w, "LinkSiteForm")).toBe(true)
	})

	it("shows the desktop dashboard for a linked site", async () => {
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		expect(has(w, "DesktopShell")).toBe(true)
		expect(has(w, "SectionPanel")).toBe(true)
		expect(has(w, "MobileShell")).toBe(false)
	})

	it("uses the mobile shell and section sheet on a narrow screen", async () => {
		setScreen(true)
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		expect(has(w, "MobileShell")).toBe(true)
		expect(has(w, "BottomSheet")).toBe(true)
		expect(has(w, "DesktopShell")).toBe(false)
	})

	it("polls a running run every 5s and settles when it is done", async () => {
		vi.useFakeTimers()
		api.getContext.mockResolvedValue(context({ last_run: run("Running") }))
		api.getRun.mockResolvedValueOnce(run("Running")).mockResolvedValueOnce(run("Done"))
		const w = render()
		await flushPromises()
		await vi.advanceTimersByTimeAsync(5000)
		expect(api.getRun).toHaveBeenCalledTimes(1)
		await vi.advanceTimersByTimeAsync(5000)
		expect(api.getRun).toHaveBeenCalledTimes(2)
		expect(toast.success).toHaveBeenCalledOnce()
		expect(stillRunning(w)).toBe(false)
	})

	it("stops polling after 2 minutes and says it is still running", async () => {
		vi.useFakeTimers()
		api.getContext.mockResolvedValue(context({ last_run: run("Running") }))
		api.getRun.mockResolvedValue(run("Running"))
		const w = render()
		await flushPromises()
		await vi.advanceTimersByTimeAsync(130000)
		expect(stillRunning(w)).toBe(true)
		const calls = api.getRun.mock.calls.length
		await vi.advanceTimersByTimeAsync(30000)
		expect(api.getRun).toHaveBeenCalledTimes(calls)
	})

	it("settles on the realtime event without waiting for the poll", async () => {
		vi.useFakeTimers()
		api.getContext.mockResolvedValue(context({ last_run: run("Running") }))
		api.getRun.mockResolvedValue(run("Done"))
		render()
		await flushPromises()
		realtime.handler?.({ run: "r1", status: "Done" })
		await flushPromises()
		expect(toast.success).toHaveBeenCalledOnce()
		await vi.advanceTimersByTimeAsync(5000)
		expect(api.getRun).toHaveBeenCalledTimes(1)
	})

	it("ignores a realtime event for a run the poll already settled", async () => {
		vi.useFakeTimers()
		api.getContext.mockResolvedValue(context({ last_run: run("Running") }))
		api.getRun.mockResolvedValue(run("Done"))
		render()
		await flushPromises()
		await vi.advanceTimersByTimeAsync(5000)
		realtime.handler?.({ run: "r1", status: "Done" })
		await flushPromises()
		expect(toast.success).toHaveBeenCalledOnce()
		expect(api.getRun).toHaveBeenCalledTimes(1)
	})
})

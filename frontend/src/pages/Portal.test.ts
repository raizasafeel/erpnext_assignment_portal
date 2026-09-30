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
	getApps: vi.fn(),
	logout: vi.fn(),
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
		"LoadingIndicator", "MobileShell", "PageHeader"]
	const { ref } = await import("vue")
	const scheme = ref("system")
	return {
		...Object.fromEntries(names.map((n) => [n, stub(n)])),
		toast: { success: vi.fn(), error: vi.fn() },
		useColorScheme: () => ({ colorScheme: scheme, setColorScheme: (v: string) => (scheme.value = v) }),
	}
})
vi.mock("../components/LinkSiteForm.vue", async () => ({ default: (await import("../test/stub")).stub("LinkSiteForm") }))
vi.mock("../components/RunAlert.vue", async () => ({ default: (await import("../test/stub")).stub("RunAlert") }))
vi.mock("../components/HeroCard.vue", async () => ({ default: (await import("../test/stub")).stub("HeroCard") }))
vi.mock("../components/PortalSidebar.vue", async () => ({ default: (await import("../test/stub")).stub("PortalSidebar") }))
vi.mock("../components/SectionCard.vue", async () => ({ default: (await import("../test/stub")).stub("SectionCard") }))
vi.mock("../components/SiteBar.vue", async () => ({ default: (await import("../test/stub")).stub("SiteBar") }))

const SECTIONS = [
	{ slug: "wh", title: "Warehouses", details: "", checks: [{ check_id: "1", title: "Mumbai" }] },
	{ slug: "coa", title: "Chart of Accounts", details: "", checks: [{ check_id: "2", title: "Stock" }] },
]
const run = (status: string) => ({
	name: "r1", status, error_code: null, started_on: null, finished_on: null, passed: 0, total: 1, results: [],
})
const context = (over = {}) => ({
	user: "s@example.com", full_name: "S",
	site: { site: "https://s.m.frappe.cloud", status: "Active", expires_on: null, expired: false, revoked: false },
	last_run: null, last_done_run: null, ...over,
})

function setScreen(mobile: boolean, reducedMotion = false) {
	window.matchMedia = vi.fn().mockImplementation((query: string) => ({
		matches: query.includes("reduced-motion") ? reducedMotion : mobile,
		addEventListener: vi.fn(),
		removeEventListener: vi.fn(),
	}))
}

const spy = vi.hoisted(() => ({ callback: null as null | IntersectionObserverCallback, observed: [] as Element[] }))
class FakeObserver {
	constructor(callback: IntersectionObserverCallback) {
		spy.callback = callback
	}
	observe(el: Element) {
		spy.observed.push(el)
	}
	unobserve() {}
	disconnect() {}
}

function render() {
	return mount(Portal, { global: { mocks: { __: (s: string) => s } } })
}

const has = (w: ReturnType<typeof render>, name: string) => w.find(`[data-stub="${name}"]`).exists()
const hero = (w: ReturnType<typeof render>) => w.findComponent({ name: "HeroCard" }).vm.$attrs
const cards = (w: ReturnType<typeof render>) => w.findAllComponents({ name: "SectionCard" })
const openCards = (w: ReturnType<typeof render>) =>
	cards(w).filter((c) => c.vm.$attrs.open).map((c) => (c.vm.$attrs.section as { slug: string }).slug)
const scrolled = () => vi.mocked(Element.prototype.scrollIntoView).mock
const stillRunning = (w: ReturnType<typeof render>) => w.findComponent({ name: "RunAlert" }).vm.$attrs["still-running"]

describe("Portal", () => {
	beforeEach(() => {
		vi.clearAllMocks()
		setScreen(false)
		api.getSections.mockResolvedValue(SECTIONS)
		api.getApps.mockResolvedValue([])
		Element.prototype.scrollIntoView = vi.fn()
		spy.callback = null
		spy.observed = []
		vi.stubGlobal("IntersectionObserver", FakeObserver)
	})
	afterEach(() => {
		vi.useRealTimers()
		vi.unstubAllGlobals()
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
		expect(has(w, "PortalSidebar")).toBe(true)
		expect(has(w, "HeroCard")).toBe(true)
		expect(cards(w)).toHaveLength(2)
		expect(has(w, "MobileShell")).toBe(false)
	})

	it("uses the mobile shell and section sheet on a narrow screen", async () => {
		setScreen(true)
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		expect(has(w, "MobileShell")).toBe(true)
		expect(has(w, "BottomSheet")).toBe(true)
		expect(has(w, "PortalSidebar")).toBe(false)
		expect(cards(w)).toHaveLength(2)
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

	it.each([
		["revoked", { revoked: true, expired: false }],
		["expired", { revoked: false, expired: true }],
	])("blocks Re-check when the site is %s", async (_, state) => {
		const base = context().site
		api.getContext.mockResolvedValue(context({ site: { ...base, ...state } }))
		const w = render()
		await flushPromises()
		const alert = w.findComponent({ name: "RunAlert" }).vm.$attrs
		expect([alert.revoked, alert.expired]).toEqual([state.revoked, state.expired])
		expect(hero(w).blocked).toBe(true)
	})

	it("allows Re-check for an active site", async () => {
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		expect(hero(w).blocked).toBe(false)
	})

	it("re-checks from the hero card", async () => {
		api.getContext.mockResolvedValue(context())
		api.startRun.mockResolvedValue({ run: "r1" })
		api.getRun.mockResolvedValue(run("Done"))
		const w = render()
		await flushPromises()
		w.findComponent({ name: "HeroCard" }).vm.$emit("recheck")
		await flushPromises()
		expect(api.startRun).toHaveBeenCalledOnce()
		expect(toast.success).toHaveBeenCalledOnce()
	})

	it("opens only the first unfinished section at first", async () => {
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		expect(openCards(w)).toEqual(["wh"])
		expect(w.findComponent({ name: "PortalSidebar" }).vm.$attrs.active).toBe("wh")
	})

	it("scrolls to a picked section smoothly and expands it", async () => {
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		w.findComponent({ name: "PortalSidebar" }).vm.$emit("pick", "coa")
		await flushPromises()
		expect(openCards(w)).toEqual(["wh", "coa"])
		expect(scrolled().contexts.map((el) => (el as Element).id)).toEqual(["section-coa"])
		expect(scrolled().calls[0][0]).toMatchObject({ behavior: "smooth", block: "start" })
		expect(w.findComponent({ name: "PortalSidebar" }).vm.$attrs.active).toBe("coa")
	})

	it("jumps without animation when the user prefers reduced motion", async () => {
		setScreen(false, true)
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		w.findComponent({ name: "PortalSidebar" }).vm.$emit("pick", "coa")
		await flushPromises()
		expect(scrolled().calls[0][0]).toMatchObject({ behavior: "auto" })
	})

	it("opens and closes each section card on its own", async () => {
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		cards(w)[1].vm.$emit("update:open", true)
		await flushPromises()
		expect(openCards(w)).toEqual(["wh", "coa"])
		cards(w)[0].vm.$emit("update:open", false)
		await flushPromises()
		expect(openCards(w)).toEqual(["coa"])
	})

	it("follows the scroll position in the sidebar", async () => {
		api.getContext.mockResolvedValue(context())
		const w = render()
		await flushPromises()
		const coa = spy.observed.find((el) => el.id === "section-coa")!
		spy.callback?.([{ target: coa, isIntersecting: true } as unknown as IntersectionObserverEntry], {} as IntersectionObserver)
		await flushPromises()
		expect(w.findComponent({ name: "PortalSidebar" }).vm.$attrs.active).toBe("coa")
	})

	it("keeps the last Done run's results after a run that errored", async () => {
		const done = { ...run("Done"), name: "r0", finished_on: "2026-09-29 12:00:00",
			results: [{ section: "wh", check_id: "1", passed: 1, found_count: 1, check_error: null }] }
		api.getContext.mockResolvedValue(context({ last_run: { ...run("Error"), error_code: "unreachable" }, last_done_run: done }))
		const w = render()
		await flushPromises()
		const scores = w.findComponent({ name: "PortalSidebar" }).vm.$attrs.scores as Record<string, { passed: number }>
		expect(scores.wh.passed).toBe(1)
		expect(hero(w).overview).toMatchObject({ passed: 1, total: 2 })
		expect(cards(w)[0].vm.$attrs.run).toEqual(done)
		expect(w.findComponent({ name: "SiteBar" }).vm.$attrs.run).toEqual(done)
		expect((w.findComponent({ name: "RunAlert" }).vm.$attrs.run as { status: string }).status).toBe("Error")
	})

	it("keeps the previous results while a re-check runs and after it fails", async () => {
		vi.useFakeTimers()
		const done = { ...run("Done"), name: "r0",
			results: [{ section: "wh", check_id: "1", passed: 1, found_count: 1, check_error: null }] }
		api.getContext.mockResolvedValue(context({ last_run: done, last_done_run: done }))
		api.startRun.mockResolvedValue({ run: "r1" })
		api.getRun.mockResolvedValueOnce(run("Running")).mockResolvedValueOnce({ ...run("Error"), error_code: "timeout" })
		const w = render()
		await flushPromises()
		w.findComponent({ name: "HeroCard" }).vm.$emit("recheck")
		await flushPromises()
		expect(hero(w).overview).toMatchObject({ passed: 1 })
		await vi.advanceTimersByTimeAsync(5000)
		expect((w.findComponent({ name: "RunAlert" }).vm.$attrs.run as { status: string }).status).toBe("Error")
		expect(hero(w).overview).toMatchObject({ passed: 1 })
	})

	it("gives the sidebar menu Apps and Log out", async () => {
		api.getContext.mockResolvedValue(context())
		api.getApps.mockResolvedValue([{ name: "lms", title: "Learning", logo: "/l.svg", route: "/lms" }])
		const w = render()
		await flushPromises()
		const menu = w.findComponent({ name: "PortalSidebar" }).vm.$attrs.menu as { label: string }[]
		expect(menu.map((o) => o.label)).toEqual(["Apps", "Link a different site", "Theme", "Log out"])
	})
})

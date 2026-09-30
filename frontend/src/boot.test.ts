import { describe, expect, it } from "vitest"

describe("boot", () => {
	it("reads the per-key globals jinjaBootData writes", async () => {
		const course = { name: "c", title: "C" }
		Object.assign(window, { csrf_token: "t", site_name: "s", socketio_port: 9000, course })
		const { boot } = await import("./boot")
		expect(boot).toEqual({ csrf_token: "t", site_name: "s", socketio_port: 9000, course })
	})
})

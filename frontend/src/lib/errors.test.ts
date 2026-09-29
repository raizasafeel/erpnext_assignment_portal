import { describe, expect, it } from "vitest"
import { requestErrorMessage, runErrorMessage } from "./errors"

describe("runErrorMessage", () => {
	it.each(["unreachable", "timeout", "not_installed", "rejected", "bad_response", "internal"])("has a message for %s", (code) => {
		expect(runErrorMessage(code)).not.toBe(runErrorMessage("unknown-code"))
	})
})

describe("requestErrorMessage", () => {
	it("shows the server's message, not the request line", () => {
		const e = Object.assign(new Error("/api/method/x PermissionError"), { messages: ["Too many link attempts."] })
		expect(requestErrorMessage(e)).toBe("Too many link attempts.")
	})
	it("falls back to the error message", () => {
		expect(requestErrorMessage(new Error("offline"))).toBe("offline")
	})
})

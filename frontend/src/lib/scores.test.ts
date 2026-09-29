import { describe, expect, it } from "vitest"
import { checkResult, sectionScores } from "./scores"

const sections = [
	{ slug: "a", title: "A", details: "", checks: [{ check_id: "1", title: "x" }, { check_id: "2", title: "y" }] },
	{ slug: "b", title: "B", details: "", checks: [{ check_id: "3", title: "z" }] },
]
const run = {
	name: "r", status: "Done", error_code: null, started_on: null, finished_on: null, passed: 2, total: 3,
	results: [
		{ section: "a", check_id: "1", passed: 1, found_count: 1, check_error: null },
		{ section: "a", check_id: "2", passed: 0, found_count: 0, check_error: null },
		{ section: "b", check_id: "3", passed: 1, found_count: 4, check_error: null },
	],
}

describe("sectionScores", () => {
	it("scores each section from the run", () => {
		expect(sectionScores(sections, run)).toEqual({
			a: { passed: 1, total: 2, percent: 50 },
			b: { passed: 1, total: 1, percent: 100 },
		})
	})
	it("is all zero before any run", () => {
		expect(sectionScores(sections, null).a).toEqual({ passed: 0, total: 2, percent: 0 })
	})
	it("ignores results of an errored run", () => {
		expect(sectionScores(sections, { ...run, status: "Error" }).b.passed).toBe(0)
	})
	it("finds a check result", () => {
		expect(checkResult(run, "3")?.found_count).toBe(4)
	})
})

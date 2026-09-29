import type { Run, RunResult, Section } from "../api"

export interface Score {
	passed: number
	total: number
	percent: number
}

export function sectionScores(sections: Section[], run: Run | null): Record<string, Score> {
	const done = run?.status === "Done" ? run.results : []
	return Object.fromEntries(
		sections.map((s) => {
			const passed = done.filter((r) => r.section === s.slug && r.passed).length
			const total = s.checks.length
			return [s.slug, { passed, total, percent: total ? Math.round((passed / total) * 100) : 0 }]
		}),
	)
}

export function checkResult(run: Run | null, checkId: string): RunResult | undefined {
	return run?.status === "Done" ? run.results.find((r) => r.check_id === checkId) : undefined
}

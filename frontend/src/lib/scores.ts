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

export type SectionStatus = "done" | "partial" | "todo"

export interface Overview {
	passed: number
	total: number
	percent: number
	sectionsDone: number
	sectionsTotal: number
}

export function sectionStatus(score: Score): SectionStatus {
	if (score.total && score.passed === score.total) return "done"
	return score.passed ? "partial" : "todo"
}

export function overview(scores: Record<string, Score>): Overview {
	const graded = Object.values(scores).filter((s) => s.total)
	const passed = graded.reduce((sum, s) => sum + s.passed, 0)
	const total = graded.reduce((sum, s) => sum + s.total, 0)
	return {
		passed,
		total,
		percent: total ? Math.round((passed / total) * 100) : 0,
		sectionsDone: graded.filter((s) => sectionStatus(s) === "done").length,
		sectionsTotal: graded.length,
	}
}

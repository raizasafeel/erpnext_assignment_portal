import { __ } from "../translate"

const MESSAGES: Record<string, string> = {
	unreachable: "We couldn't reach your site. Check that it is running and try again.",
	timeout: "Your site took too long to answer. Try again in a minute.",
	not_installed: "The grader app isn't installed on your site.",
	rejected: "Your site refused the grader. Make sure the grader app is up to date.",
	bad_response: "Your site sent an answer we couldn't read. Update the grader app and try again.",
	internal: "Something went wrong on our side. Try again.",
}

export function runErrorMessage(code: string | null): string {
	return __((code && MESSAGES[code]) || "Grading didn't finish. Try again.")
}

export function requestErrorMessage(error: unknown): string {
	const e = error as Error & { messages?: string[] }
	return e.messages?.find(Boolean) ?? e.message
}

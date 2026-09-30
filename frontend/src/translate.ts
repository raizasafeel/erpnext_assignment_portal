// Placeholder substitution only: the portal is English-only for now.
export function __(message: string, replace?: (string | number)[]): string {
	if (!replace) return message
	return message.replace(/{(\d+)}/g, (match, i) => String(replace[Number(i)] ?? match))
}

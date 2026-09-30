const TASK = /^\s*\[( |x|X)\]\s*/

export function hasContent(html: string): boolean {
	const body = new DOMParser().parseFromString(html || "", "text/html").body
	return Boolean(body.textContent?.trim() || body.querySelector("img, table, iframe, video"))
}

export function withChecklistMarks(html: string): string {
	const doc = new DOMParser().parseFromString(html || "", "text/html")
	for (const li of Array.from(doc.querySelectorAll("li"))) {
		if (!TASK.test(li.textContent ?? "")) continue
		const done = /^\s*\[[xX]\]/.test(li.textContent ?? "")
		replaceMarker(li, done ? "\u2611 " : "\u2610 ")
	}
	return doc.body.innerHTML
}

function replaceMarker(li: Element, mark: string) {
	const walker = li.ownerDocument.createTreeWalker(li, NodeFilter.SHOW_TEXT)
	let node = walker.nextNode()
	while (node && !node.textContent?.trim()) node = walker.nextNode()
	if (node?.textContent) node.textContent = node.textContent.replace(TASK, mark)
}

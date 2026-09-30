const TASK = /^\s*\[( |x|X)\]\s*/

export function hasContent(html: string): boolean {
	const body = new DOMParser().parseFromString(html || "", "text/html").body
	return Boolean(body.textContent?.trim() || body.querySelector("img, table, iframe, video"))
}

export function withTaskLists(html: string): string {
	const doc = new DOMParser().parseFromString(html || "", "text/html")
	for (const list of Array.from(doc.querySelectorAll("ul"))) {
		const items = Array.from(list.children)
		if (!items.length || !items.every((li) => li.tagName === "LI" && TASK.test(li.textContent ?? "")))
			continue
		list.setAttribute("data-type", "taskList")
		for (const li of items) {
			const checked = /^\s*\[[xX]\]/.test(li.textContent ?? "")
			li.setAttribute("data-type", "taskItem")
			li.setAttribute("data-checked", String(checked))
			stripMarker(li)
		}
	}
	return doc.body.innerHTML
}

function stripMarker(li: Element) {
	const walker = li.ownerDocument.createTreeWalker(li, NodeFilter.SHOW_TEXT)
	let node = walker.nextNode()
	while (node && !node.textContent?.trim()) node = walker.nextNode()
	if (node?.textContent) node.textContent = node.textContent.replace(TASK, "")
}

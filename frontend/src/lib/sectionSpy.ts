import type { Ref } from "vue"
import type { Section } from "../api"

const SPY_MARGIN = "0px 0px -60% 0px"
const SPY_PAUSE_MS = 1000
const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)"

export function useSectionSpy(sections: Ref<Section[]>, activeSlug: Ref<string>) {
	const cards = new Map<string, HTMLElement>()
	const inView = new Set<string>()
	let spy: IntersectionObserver | null = null
	let pausedUntil = 0

	function track(slug: string, el: HTMLElement | null) {
		const previous = cards.get(slug)
		if (previous === el) return
		if (previous) spy?.unobserve(previous)
		if (el) {
			cards.set(slug, el)
			spy?.observe(el)
		} else cards.delete(slug)
	}

	function onSpy(entries: IntersectionObserverEntry[]) {
		for (const entry of entries) {
			const slug = (entry.target as HTMLElement).dataset.slug ?? ""
			if (entry.isIntersecting) inView.add(slug)
			else inView.delete(slug)
		}
		if (Date.now() < pausedUntil) return
		const first = sections.value.find((s) => inView.has(s.slug))
		if (first) activeSlug.value = first.slug
	}

	function start() {
		if (!("IntersectionObserver" in window)) return
		spy = new IntersectionObserver(onSpy, { rootMargin: SPY_MARGIN })
		cards.forEach((el) => spy?.observe(el))
	}

	function stop() {
		spy?.disconnect()
	}

	function pause() {
		pausedUntil = Date.now() + SPY_PAUSE_MS
	}

	function scrollTo(slug: string) {
		const smooth = !window.matchMedia(REDUCED_MOTION_QUERY).matches
		cards.get(slug)?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" })
	}

	return { track, start, stop, pause, scrollTo }
}

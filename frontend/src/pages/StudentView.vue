<template>
	<div class="flex flex-col min-h-screen bg-surface-gray-1">
		<AppHeader
			:connected="connected"
			:site-label="siteLabel"
			:last-checked="lastChecked"
			:sec-passed="overall.secPassed"
			:sec-total="overall.secTotal"
			@open-details="detailsOpen = true"
			@logout="logout.submit()"
		/>

		<div v-if="!connected" class="flex flex-1 items-center justify-center p-6">
			<ConnectSitePanel :default-site="siteUrl" @connected="portalContext.fetch()" />
		</div>

		<div
			v-else
			class="mx-auto grid max-w-[1320px] items-start lg:grid-cols-[272px_minmax(0,1fr)]"
		>
			<SectionNav :states="states" :active-name="activeName" @jump="jumpTo" />
			<main class="px-6 pb-32 pt-6 md:px-8">
				<AnalyticsHero
					:student-name="studentName"
					:overall="overall"
					:regrading="regrading"
					@regrade="runRegrade"
					@jump-fix="firstFailingName && jumpTo(firstFailingName)"
				/>
				<div
					v-if="assignmentsResource.loading"
					class="rounded-md border border-outline-gray-2 bg-surface-white p-4 text-base text-ink-gray-6"
				>
					Loading sections…
				</div>
				<div
					v-else-if="!states.length"
					class="rounded-md border border-outline-gray-2 bg-surface-white p-4 text-base text-ink-gray-6"
				>
					No assignments published yet.
				</div>
				<div v-else class="flex flex-col gap-4">
					<SectionCard
						v-for="(s, i) in states"
						:key="s.section.name"
						:state="s"
						:index="i"
						:default-open="defaultOpenFor(s)"
						@mounted="registerEl"
					/>
				</div>
			</main>
		</div>

		<SiteDetailsDialog
			v-model="detailsOpen"
			:site-url="siteUrl"
			:last-checked="lastChecked"
			@disconnected="portalContext.fetch()"
		/>
	</div>
</template>

<script setup lang="ts">
import { createResource, toast } from "frappe-ui"
import { computed, onMounted, onUnmounted, ref } from "vue"

import AnalyticsHero from "@/components/AnalyticsHero.vue"
import AppHeader from "@/components/AppHeader.vue"
import ConnectSitePanel from "@/components/ConnectSitePanel.vue"
import SectionCard from "@/components/SectionCard.vue"
import SectionNav from "@/components/SectionNav.vue"
import SiteDetailsDialog from "@/components/SiteDetailsDialog.vue"
import { buildSectionStates, overallStats } from "@/lib/sections"
import type {
	AssignmentSection,
	SectionState,
	SectionSubmission,
} from "@/types"

type PortalContext = {
	user: string
	full_name: string
	course: string
	site: {
		name: string
		site: string
		last_checked: string
		connected: boolean
	} | null
}

const portalContext = createResource({
	url: "erpnext_assignment_portal.erpnext_assignment_portal.api.get_current_user_info",
	auto: true,
})

const assignmentsResource = createResource({
	url: "erpnext_assignment_portal.erpnext_assignment_portal.api.get_assignments",
	auto: true,
})

const submissionsResource = createResource({
	url: "erpnext_assignment_portal.erpnext_assignment_portal.api.get_my_submissions",
	auto: true,
})

const regrade = createResource({
	url: "erpnext_assignment_portal.erpnext_assignment_portal.api.regrade",
})

const logout = createResource({
	url: "logout",
	onSuccess() {
		window.location.href = "/login"
	},
})

const context = computed(() => portalContext.data as PortalContext | null)
const firstName = computed(
	() => context.value?.full_name?.split(" ")[0] ?? "there",
)
const studentName = firstName

const assignments = computed(
	() => (assignmentsResource.data as AssignmentSection[] | null) ?? [],
)
const submissions = computed(
	() => (submissionsResource.data as SectionSubmission[] | null) ?? [],
)
const states = computed(() =>
	buildSectionStates(assignments.value, submissions.value),
)
const overall = computed(() => overallStats(states.value))

const siteUrl = computed(() => context.value?.site?.site ?? "")
const siteLabel = computed(
	() => siteUrl.value.replace(/^https?:\/\//, "") || null,
)
const connected = computed(() => !!context.value?.site?.connected)
const lastChecked = computed(() => context.value?.site?.last_checked ?? null)
const detailsOpen = ref(false)

const firstFailingName = computed(
	() => states.value.find((s) => s.status !== "passed")?.section.name ?? null,
)
const defaultOpenFor = (s: SectionState) => s.status !== "passed"

// Scroll-spy: track which section is nearest the top of the viewport.
const activeName = ref<string | null>(null)
const sectionEls = new Map<string, HTMLElement>()

function registerEl(name: string, el: HTMLElement) {
	sectionEls.set(name, el)
}

function jumpTo(name: string) {
	activeName.value = name
	sectionEls.get(name)?.scrollIntoView({ behavior: "smooth", block: "start" })
}

function onScroll() {
	let current: string | null = null
	for (const s of states.value) {
		const el = sectionEls.get(s.section.name)
		if (!el) continue
		if (el.getBoundingClientRect().top <= 120) current = s.section.name
	}
	if (current) activeName.value = current
}

onMounted(() => window.addEventListener("scroll", onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener("scroll", onScroll))

const regrading = ref(false)

function newestSubmissionTime(): number {
	let max = 0
	for (const s of submissions.value) {
		const t = new Date(s.submission_time).getTime()
		if (!Number.isNaN(t) && t > max) max = t
	}
	return max
}

async function runRegrade() {
	if (regrading.value) return
	regrading.value = true
	try {
		const before = newestSubmissionTime()
		await regrade.submit()
		const deadline = Date.now() + 60_000 // give up after 60s
		while (Date.now() < deadline) {
			await new Promise((r) => setTimeout(r, 2000)) // recheck every 2s
			await submissionsResource.reload()
			if (newestSubmissionTime() > before) break
		}
	} catch (e) {
		const err = e as { messages: string[]; message: string }
		toast.error(err?.messages?.[0] || err?.message || "Grading failed")
	} finally {
		regrading.value = false
	}
}
</script>

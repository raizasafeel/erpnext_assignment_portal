<template>
	<div v-if="loading" class="flex h-screen items-center justify-center">
		<LoadingIndicator class="size-6" />
	</div>
	<div v-else-if="notEnrolled" class="p-6">
		<Alert
			theme="amber"
			:title="__('You are not enrolled')"
			:description="__('Enroll in the course to use the grader.')"
		/>
	</div>
	<div v-else-if="loadError" class="p-6">
		<Alert theme="red" :title="__('Could not load the portal')" :description="loadError" />
	</div>
	<LinkSiteForm v-else-if="!ctx?.site" @linked="load" />
	<component :is="isMobile ? MobileShell : DesktopShell" v-else>
		<template #sidebar>
			<PortalSidebar
				v-if="!isMobile"
				:sections="sections"
				:scores="scores"
				:active="activeSlug"
				:full-name="ctx.full_name"
				:menu="menu"
				@pick="goTo"
			/>
		</template>
		<PageHeader>
			<div v-if="isMobile" class="flex w-full items-center justify-between gap-2">
				<Button
					variant="ghost"
					icon-right="lucide-chevron-down"
					:label="activeSection?.title ?? __('Sections')"
					@click="picking = true"
				/>
				<Dropdown
					:options="menu"
					:button="{ icon: 'lucide-ellipsis', variant: 'ghost' }"
				/>
			</div>
			<SiteBar
				v-else
				class="w-full justify-end"
				:site="ctx.site"
				:run="run"
				:overview="stats"
				@relink="relinking = true"
			/>
		</PageHeader>
		<div class="mx-auto flex w-full max-w-5xl flex-col gap-4 p-4 sm:p-6">
			<SiteBar
				v-if="isMobile"
				:site="ctx.site"
				:run="run"
				:overview="stats"
				@relink="relinking = true"
			/>
			<RunAlert
				:run="run"
				:expired="ctx.site.expired"
				:revoked="ctx.site.revoked"
				:still-running="stillRunning"
			/>
			<HeroCard
				:full-name="ctx.full_name"
				:overview="stats"
				:grading="grading"
				:blocked="siteBlocked"
				@recheck="recheck"
			/>
			<div
				v-for="(s, i) in sections"
				:id="`section-${s.slug}`"
				:key="s.slug"
				:ref="(el) => track(s.slug, el as HTMLElement | null)"
				:data-slug="s.slug"
				class="scroll-mt-4"
			>
				<SectionCard
					:section="s"
					:index="i"
					:run="run"
					:score="scores[s.slug]"
					:open="openSlugs.has(s.slug)"
					@update:open="setOpen(s.slug, $event)"
				/>
			</div>
		</div>
		<BottomSheet v-if="isMobile" v-model:open="picking" :title="__('Sections')">
			<ItemListRow
				v-for="s in sections"
				:key="s.slug"
				size="lg"
				:active="s.slug === activeSlug"
				@click="goTo(s.slug)"
			>
				<template #label>
					<span class="text-base text-ink-gray-8">{{ s.title }}</span>
				</template>
				<template #suffix>
					<Badge theme="gray" :label="scoreLabel(s.slug)" />
				</template>
			</ItemListRow>
		</BottomSheet>
	</component>
	<Dialog v-if="ctx?.site" v-model:open="relinking" :title="__('Link a different site')">
		<LinkSiteForm :default-site="ctx.site.site" @linked="onRelinked" />
	</Dialog>
</template>

<script setup lang="ts">
import {
	Alert,
	Badge,
	BottomSheet,
	Button,
	DesktopShell,
	Dialog,
	Dropdown,
	ItemListRow,
	LoadingIndicator,
	MobileShell,
	PageHeader,
	toast,
} from "frappe-ui";
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
	type App,
	type Context,
	type Run,
	type Section,
	getApps,
	getContext,
	getRun,
	getSections,
	logout,
	startRun,
} from "../api";
import HeroCard from "../components/HeroCard.vue";
import LinkSiteForm from "../components/LinkSiteForm.vue";
import PortalSidebar from "../components/PortalSidebar.vue";
import RunAlert from "../components/RunAlert.vue";
import SectionCard from "../components/SectionCard.vue";
import SiteBar from "../components/SiteBar.vue";
import { requestErrorMessage } from "../lib/errors";
import { overview, sectionScores, sectionStatus } from "../lib/scores";
import { userMenu } from "../lib/userMenu";
import { onRunUpdate } from "../socket";
import { __ } from "../translate";

const POLL_MS = 5000;
const POLL_LIMIT_MS = 120000;
const MOBILE_QUERY = "(max-width: 767px)";
const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";
const SPY_MARGIN = "0px 0px -60% 0px";
const SPY_PAUSE_MS = 1000;
const FINISHED = ["Done", "Error"];
const IN_PROGRESS = ["Queued", "Running"];

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const notEnrolled = ref(false);
const loadError = ref("");
const ctx = ref<Context | null>(null);
const sections = ref<Section[]>([]);
const run = ref<Run | null>(null);
const grading = ref(false);
const stillRunning = ref(false);
const relinking = ref(false);
const picking = ref(false);
const mobileQuery = window.matchMedia(MOBILE_QUERY);
const isMobile = ref(mobileQuery.matches);
const apps = ref<App[]>([]);
const activeSlug = ref("");
const openSlugs = ref(new Set<string>());
const cards = new Map<string, HTMLElement>();
const inView = new Set<string>();
let spy: IntersectionObserver | null = null;
let spyPausedUntil = 0;
let pollTimer: ReturnType<typeof setTimeout> | undefined;

const siteBlocked = computed(() => Boolean(ctx.value?.site?.expired || ctx.value?.site?.revoked));
const scores = computed(() => sectionScores(sections.value, run.value));
const stats = computed(() => overview(scores.value));
const activeSection = computed(() => sections.value.find((s) => s.slug === activeSlug.value));
const menu = computed(() =>
	userMenu(apps.value, {
		relink: () => (relinking.value = true),
		logout: signOut,
		open: (path) => window.location.assign(path),
	})
);

function scoreLabel(slug: string) {
	const { passed, total } = scores.value[slug];
	return `${passed}/${total}`;
}

function onMobileChange(e: MediaQueryListEvent) {
	isMobile.value = e.matches;
}

function setOpen(slug: string, open: boolean) {
	if (open) openSlugs.value.add(slug);
	else openSlugs.value.delete(slug);
}

function scrollTo(slug: string) {
	const smooth = !window.matchMedia(REDUCED_MOTION_QUERY).matches;
	cards.get(slug)?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
}

async function goTo(slug: string) {
	picking.value = false;
	setOpen(slug, true);
	activeSlug.value = slug;
	spyPausedUntil = Date.now() + SPY_PAUSE_MS;
	router.replace({ params: { section: slug } });
	await nextTick();
	scrollTo(slug);
}

function track(slug: string, el: HTMLElement | null) {
	const previous = cards.get(slug);
	if (previous === el) return;
	if (previous) spy?.unobserve(previous);
	if (el) {
		cards.set(slug, el);
		spy?.observe(el);
	} else cards.delete(slug);
}

function onSpy(entries: IntersectionObserverEntry[]) {
	for (const entry of entries) {
		const slug = (entry.target as HTMLElement).dataset.slug ?? "";
		if (entry.isIntersecting) inView.add(slug);
		else inView.delete(slug);
	}
	if (Date.now() < spyPausedUntil) return;
	const first = sections.value.find((s) => inView.has(s.slug));
	if (first) activeSlug.value = first.slug;
}

function startSpy() {
	if (!("IntersectionObserver" in window)) return;
	spy = new IntersectionObserver(onSpy, { rootMargin: SPY_MARGIN });
	cards.forEach((el) => spy?.observe(el));
}

function initialSection(): string {
	const linked = sections.value.find((s) => s.slug === route.params.section);
	const pending = sections.value.find((s) => sectionStatus(scores.value[s.slug]) !== "done");
	return (linked ?? pending ?? sections.value[0])?.slug ?? "";
}

async function loadApps() {
	try {
		apps.value = (await getApps()) ?? [];
	} catch {
		apps.value = [];
	}
}

async function signOut() {
	try {
		await logout();
	} finally {
		window.location.href = "/login";
	}
}

async function load() {
	loadError.value = "";
	try {
		ctx.value = await getContext();
		sections.value = await getSections();
	} catch (e) {
		if ((e as { exc_type?: string }).exc_type === "PermissionError") notEnrolled.value = true;
		else loadError.value = requestErrorMessage(e);
		loading.value = false;
		return;
	}
	run.value = ctx.value.last_run;
	loading.value = false;
	const first = initialSection();
	activeSlug.value = first;
	if (first) setOpen(first, true);
	if (route.params.section === first) nextTick(() => scrollTo(first));
	if (run.value && IN_PROGRESS.includes(run.value.status)) watchRun(run.value.name);
}

function onRelinked() {
	relinking.value = false;
	load();
}

async function recheck() {
	grading.value = true;
	try {
		const { run: name } = await startRun();
		const latest = await getRun(name);
		if (FINISHED.includes(latest.status)) return settle(latest);
		run.value = latest;
		watchRun(name);
	} catch (e) {
		grading.value = false;
		toast.error(requestErrorMessage(e));
	}
}

function watchRun(name: string) {
	grading.value = true;
	stillRunning.value = false;
	const started = Date.now();
	clearTimeout(pollTimer);
	const tick = async () => {
		try {
			const latest = await getRun(name);
			if (FINISHED.includes(latest.status)) return settle(latest);
		} catch {
			// a failed poll is retried on the next tick
		}
		if (Date.now() - started > POLL_LIMIT_MS) {
			grading.value = false;
			stillRunning.value = true;
			return;
		}
		pollTimer = setTimeout(tick, POLL_MS);
	};
	pollTimer = setTimeout(tick, POLL_MS);
}

function isSettled(name: string) {
	return run.value?.name === name && FINISHED.includes(run.value.status);
}

function settle(latest: Run) {
	clearTimeout(pollTimer);
	if (isSettled(latest.name)) return;
	run.value = latest;
	grading.value = false;
	stillRunning.value = false;
	if (latest.status === "Done") toast.success(__("Grading finished"));
}

let stop = () => {};
onMounted(() => {
	mobileQuery.addEventListener("change", onMobileChange);
	startSpy();
	load();
	loadApps();
	stop = onRunUpdate(async (e) => {
		if (e.run === run.value?.name && !isSettled(e.run)) settle(await getRun(e.run));
	});
});
onUnmounted(() => {
	mobileQuery.removeEventListener("change", onMobileChange);
	stop();
	spy?.disconnect();
	clearTimeout(pollTimer);
});
</script>

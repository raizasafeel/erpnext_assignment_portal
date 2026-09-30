<template>
	<div v-if="loading" class="flex h-screen items-center justify-center">
		<LoadingIndicator class="size-6" />
	</div>
	<NotEnrolled v-else-if="notEnrolled" :course="boot.course ?? null" @logout="signOut" />
	<div v-else-if="loadError" class="p-6">
		<Alert theme="red" :title="__('Could not load the portal')" :description="loadError" />
	</div>
	<LinkSitePage v-else-if="!ctx?.site" @linked="load" @logout="signOut" />
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
				:run="graded"
				:overview="stats"
				@relink="relinking = true"
			/>
		</PageHeader>
		<div class="mx-auto flex w-full max-w-5xl flex-col gap-4 p-4 sm:p-6">
			<SiteBar
				v-if="isMobile"
				:site="ctx.site"
				:run="graded"
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
				:ref="(el) => spy.track(s.slug, el as HTMLElement | null)"
				:data-slug="s.slug"
				class="scroll-mt-4"
			>
				<SectionCard
					:section="s"
					:index="i"
					:run="graded"
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
	type Section,
	getApps,
	getContext,
	getSections,
	logout,
} from "../api";
import HeroCard from "../components/HeroCard.vue";
import LinkSiteForm from "../components/LinkSiteForm.vue";
import LinkSitePage from "../components/LinkSitePage.vue";
import NotEnrolled from "../components/NotEnrolled.vue";
import PortalSidebar from "../components/PortalSidebar.vue";
import RunAlert from "../components/RunAlert.vue";
import SectionCard from "../components/SectionCard.vue";
import SiteBar from "../components/SiteBar.vue";
import { boot } from "../boot";
import { requestErrorMessage } from "../lib/errors";
import { useRunWatcher } from "../lib/runWatcher";
import { overview, sectionScores, sectionStatus } from "../lib/scores";
import { useSectionSpy } from "../lib/sectionSpy";
import { useTheme } from "../lib/theme";
import { userMenu } from "../lib/userMenu";

const MOBILE_QUERY = "(max-width: 767px)";

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const notEnrolled = ref(false);
const loadError = ref("");
const ctx = ref<Context | null>(null);
const sections = ref<Section[]>([]);
const relinking = ref(false);
const picking = ref(false);
const mobileQuery = window.matchMedia(MOBILE_QUERY);
const isMobile = ref(mobileQuery.matches);
const apps = ref<App[]>([]);
const activeSlug = ref("");
const openSlugs = ref(new Set<string>());
const theme = useTheme();
const { run, lastDone, grading, stillRunning, restore, recheck } = useRunWatcher();
const spy = useSectionSpy(sections, activeSlug);

const siteBlocked = computed(() => Boolean(ctx.value?.site?.expired || ctx.value?.site?.revoked));
const graded = computed(() => (run.value?.status === "Done" ? run.value : lastDone.value));
const scores = computed(() => sectionScores(sections.value, graded.value));
const stats = computed(() => overview(scores.value));
const activeSection = computed(() => sections.value.find((s) => s.slug === activeSlug.value));
const menu = computed(() =>
	userMenu(apps.value, {
		relink: () => (relinking.value = true),
		theme: { scheme: theme.colorScheme.value, set: theme.setColorScheme },
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

async function goTo(slug: string) {
	picking.value = false;
	setOpen(slug, true);
	activeSlug.value = slug;
	spy.pause();
	router.replace({ params: { section: slug } });
	await nextTick();
	spy.scrollTo(slug);
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
	} catch (e) {
		toast.error(requestErrorMessage(e));
		return;
	}
	window.location.href = "/login";
}

async function load() {
	loadError.value = "";
	try {
		[ctx.value, sections.value] = await Promise.all([getContext(), getSections()]);
	} catch (e) {
		if ((e as { exc_type?: string }).exc_type === "PermissionError") notEnrolled.value = true;
		else loadError.value = requestErrorMessage(e);
		loading.value = false;
		return;
	}
	restore(ctx.value.last_run, ctx.value.last_done_run);
	loading.value = false;
	openFirstSection();
}

function openFirstSection() {
	const first = initialSection();
	activeSlug.value = first;
	if (first) setOpen(first, true);
	if (route.params.section === first) nextTick(() => spy.scrollTo(first));
}

function onRelinked() {
	relinking.value = false;
	load();
}

onMounted(() => {
	mobileQuery.addEventListener("change", onMobileChange);
	spy.start();
	load();
	loadApps();
});
onUnmounted(() => {
	mobileQuery.removeEventListener("change", onMobileChange);
	spy.stop();
});
</script>

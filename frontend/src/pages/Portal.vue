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
	<MobileShell v-else-if="isMobile">
		<PageHeader>
			<div class="flex w-full items-center justify-between gap-2">
				<Button
					variant="ghost"
					icon-right="lucide-chevron-down"
					:label="current?.title ?? __('Sections')"
					@click="picking = true"
				/>
				<div class="flex items-center gap-2">
					<Dropdown
						:options="menu"
						:button="{ icon: 'lucide-ellipsis', variant: 'ghost' }"
					/>
					<Button
						variant="solid"
						:loading="grading"
						:disabled="ctx.site.expired"
						:label="__('Re-check')"
						@click="recheck"
					/>
				</div>
			</div>
		</PageHeader>
		<div class="flex flex-col gap-4 p-4">
			<RunAlert :run="run" :expired="ctx.site.expired" :still-running="stillRunning" />
			<SectionPanel
				v-if="current"
				:section="current"
				:run="run"
				:score="scores[current.slug]"
			/>
		</div>
		<BottomSheet v-model:open="picking" :title="__('Sections')">
			<ItemListRow
				v-for="s in sections"
				:key="s.slug"
				size="lg"
				:active="s.slug === current?.slug"
				@click="pick(s.slug)"
			>
				<template #label>
					<span class="text-base text-ink-gray-8">{{ s.title }}</span>
				</template>
				<template #suffix>
					<Badge theme="gray" :label="scoreLabel(s.slug)" />
				</template>
			</ItemListRow>
		</BottomSheet>
	</MobileShell>
	<DesktopShell v-else>
		<template #sidebar>
			<Sidebar :collapsible="false" width="16rem">
				<SidebarHeader
					:title="__('ERPNext Assignment Portal')"
					:subtitle="ctx.site.site"
				/>
				<SidebarItem
					v-for="s in sections"
					:key="s.slug"
					:label="s.title"
					:suffix="scoreLabel(s.slug)"
					:active="s.slug === current?.slug"
					@click="pick(s.slug)"
				/>
			</Sidebar>
		</template>
		<PageHeader>
			<div class="flex w-full items-center justify-between gap-4">
				<span class="text-lg font-semibold text-ink-gray-9">
					{{ __("Your progress") }}
				</span>
				<div class="flex items-center gap-2">
					<Dropdown
						:options="menu"
						:button="{ label: ctx.full_name, variant: 'ghost' }"
					/>
					<Button
						variant="solid"
						:loading="grading"
						:disabled="ctx.site.expired"
						:label="__('Re-check')"
						@click="recheck"
					/>
				</div>
			</div>
		</PageHeader>
		<div class="flex flex-col gap-4 p-6">
			<RunAlert :run="run" :expired="ctx.site.expired" :still-running="stillRunning" />
			<SectionPanel
				v-if="current"
				:section="current"
				:run="run"
				:score="scores[current.slug]"
			/>
		</div>
	</DesktopShell>
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
	Sidebar,
	SidebarHeader,
	SidebarItem,
	toast,
} from "frappe-ui";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
	type Context,
	type Run,
	type Section,
	getContext,
	getRun,
	getSections,
	startRun,
} from "../api";
import LinkSiteForm from "../components/LinkSiteForm.vue";
import RunAlert from "../components/RunAlert.vue";
import SectionPanel from "../components/SectionPanel.vue";
import { requestErrorMessage } from "../lib/errors";
import { sectionScores } from "../lib/scores";
import { onRunUpdate } from "../socket";
import { __ } from "../translate";

const POLL_MS = 5000;
const POLL_LIMIT_MS = 120000;
const MOBILE_QUERY = "(max-width: 767px)";
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
let pollTimer: ReturnType<typeof setTimeout> | undefined;

const scores = computed(() => sectionScores(sections.value, run.value));
const current = computed(
	() => sections.value.find((s) => s.slug === route.params.section) ?? sections.value[0]
);
const menu = computed(() => [
	{ label: __("Link a different site"), onClick: () => (relinking.value = true) },
]);

function scoreLabel(slug: string) {
	const { passed, total } = scores.value[slug];
	return `${passed}/${total}`;
}

function onMobileChange(e: MediaQueryListEvent) {
	isMobile.value = e.matches;
}

function pick(slug: string) {
	picking.value = false;
	router.replace({ params: { section: slug } });
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
	load();
	stop = onRunUpdate(async (e) => {
		if (e.run === run.value?.name && !isSettled(e.run)) settle(await getRun(e.run));
	});
});
onUnmounted(() => {
	mobileQuery.removeEventListener("change", onMobileChange);
	stop();
	clearTimeout(pollTimer);
});
</script>

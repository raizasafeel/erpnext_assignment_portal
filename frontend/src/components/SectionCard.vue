<template>
	<section
		class="overflow-hidden rounded-7 border border-outline-gray-2 bg-surface-base"
		:aria-labelledby="`${id}-title`"
	>
		<h2 :id="`${id}-title`">
			<button
				type="button"
				class="flex w-full items-center gap-3 px-5 py-4 text-start hover:bg-surface-gray-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
				:aria-expanded="open"
				:aria-controls="`${id}-body`"
				@click="emit('update:open', !open)"
			>
				<span class="w-6 shrink-0 text-sm tabular-nums text-ink-gray-4">{{ number }}</span>
				<span class="min-w-0 flex-1 truncate text-base font-semibold text-ink-gray-9">
					{{ section.title }}
				</span>
				<Badge :theme="badge.theme" :label="badge.label" />
				<span
					class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5 transition-transform"
					:class="open ? 'rotate-180' : ''"
					aria-hidden="true"
				/>
			</button>
		</h2>
		<div
			v-show="open"
			:id="`${id}-body`"
			class="grid border-t border-outline-gray-1 md:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]"
		>
			<div class="flex min-w-0 flex-col gap-3 p-5">
				<h3
					class="flex items-center gap-2 text-xs font-semibold uppercase text-ink-gray-5"
				>
					<span class="lucide-file-text size-4" aria-hidden="true" />
					{{ __("What to do") }}
				</h3>
				<SectionDetails v-if="open && details" :html="details" />
				<p v-else-if="!details" class="text-p-base text-ink-gray-5">
					{{
						__(
							"There are no written instructions for this section. Use the checks as your guide."
						)
					}}
				</p>
			</div>
			<div
				class="flex min-w-0 flex-col gap-3 border-outline-gray-1 bg-surface-gray-1 p-5 max-md:border-t md:border-s"
			>
				<div class="flex items-center justify-between gap-2">
					<h3
						class="flex items-center gap-2 text-xs font-semibold uppercase text-ink-gray-5"
					>
						<span class="lucide-list-checks size-4" aria-hidden="true" />
						{{ __("Checks") }}
					</h3>
					<span class="text-sm text-ink-gray-6">
						{{ __("{0}/{1} passing", [score.passed, score.total]) }}
					</span>
				</div>
				<ul class="flex flex-col gap-1.5">
					<li
						v-for="row in rows"
						:key="row.check_id"
						:data-state="row.state"
						class="flex items-start gap-2 rounded-4 px-3 py-2"
						:class="ROW[row.state]"
					>
						<span
							class="mt-0.5 size-4 shrink-0"
							:class="ICON[row.state]"
							aria-hidden="true"
						/>
						<span class="min-w-0 flex-1 text-sm text-ink-gray-8">
							<span class="sr-only">{{ STATE_LABEL[row.state] }}:</span>
							{{ row.title }}
						</span>
						<Badge v-if="row.error" theme="amber" size="sm" :label="row.error" />
					</li>
				</ul>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { Badge, LoadingText } from "frappe-ui";
import { computed, defineAsyncComponent } from "vue";
import type { Run, Section } from "../api";
import { hasContent, withChecklistMarks } from "../lib/details";
import { type Score, type SectionStatus, checkResult, sectionStatus } from "../lib/scores";
import { __ } from "../translate";

const SectionDetails = defineAsyncComponent({
	loader: () => import("./SectionDetails.vue"),
	loadingComponent: LoadingText,
});

type RowState = "pass" | "fail" | "pending";

const ROW: Record<RowState, string> = {
	pass: "bg-surface-green-1",
	fail: "bg-surface-red-1",
	pending: "bg-surface-base",
};
const ICON: Record<RowState, string> = {
	pass: "lucide-circle-check text-ink-green-6",
	fail: "lucide-circle-x text-ink-red-6",
	pending: "lucide-circle-dashed text-ink-gray-4",
};
const STATE_LABEL: Record<RowState, string> = {
	pass: __("Passed"),
	fail: __("Not yet"),
	pending: __("Not checked"),
};
const BADGE: Record<
	SectionStatus,
	{ theme: "green" | "amber" | "red"; label: (s: Score) => string }
> = {
	done: { theme: "green", label: (s) => __("Done · {0}/{1}", [s.passed, s.total]) },
	partial: { theme: "amber", label: (s) => __("In progress · {0}/{1}", [s.passed, s.total]) },
	todo: { theme: "red", label: (s) => __("Not started · {0}/{1}", [s.passed, s.total]) },
};

const props = defineProps<{
	section: Section;
	index: number;
	run: Run | null;
	score: Score;
	open: boolean;
}>();
const emit = defineEmits<{ "update:open": [value: boolean] }>();

const id = computed(() => `section-card-${props.section.slug}`);
const number = computed(() => String(props.index + 1).padStart(2, "0"));
const details = computed(() =>
	hasContent(props.section.details) ? withChecklistMarks(props.section.details) : ""
);
const badge = computed(() => {
	const b = BADGE[sectionStatus(props.score)];
	return { theme: b.theme, label: b.label(props.score) };
});
const rows = computed(() =>
	props.section.checks.map((check) => {
		const result = checkResult(props.run, check.check_id);
		const state: RowState = !result ? "pending" : result.passed ? "pass" : "fail";
		const error = result?.check_error ? __("Couldn't check") : "";
		return { ...check, state, error };
	})
);
</script>

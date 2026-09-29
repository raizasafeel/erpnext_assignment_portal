<template>
	<div class="flex flex-col gap-6">
		<div class="flex items-center justify-between gap-4">
			<h2 class="text-lg font-semibold text-ink-gray-9">{{ section.title }}</h2>
			<Badge
				:theme="score.total && score.passed === score.total ? 'green' : 'gray'"
				:label="`${score.passed}/${score.total}`"
			/>
		</div>
		<Progress :value="score.percent" size="md" />
		<div class="flex flex-col">
			<ItemListRow v-for="check in section.checks" :key="check.check_id" size="md">
				<template #prefix>
					<Badge v-bind="badgeFor(check.check_id)" size="sm" />
				</template>
				<template #label>
					<span class="text-base text-ink-gray-8">{{ check.title }}</span>
				</template>
			</ItemListRow>
		</div>
		<SectionDetails v-if="section.details" :html="section.details" />
	</div>
</template>

<script setup lang="ts">
import { Badge, ItemListRow, LoadingText, Progress } from "frappe-ui";
import { defineAsyncComponent } from "vue";
import type { Run, Section } from "../api";
import { checkResult, type Score } from "../lib/scores";
import { __ } from "../translate";

const SectionDetails = defineAsyncComponent({
	loader: () => import("./SectionDetails.vue"),
	loadingComponent: LoadingText,
});

const props = defineProps<{ section: Section; run: Run | null; score: Score }>();

function badgeFor(checkId: string) {
	const r = checkResult(props.run, checkId);
	if (!r) return { theme: "gray" as const, label: __("Not checked") };
	if (r.check_error) return { theme: "amber" as const, label: __("Can't check") };
	return r.passed
		? { theme: "green" as const, label: __("Passed") }
		: { theme: "red" as const, label: __("Not yet") };
}
</script>

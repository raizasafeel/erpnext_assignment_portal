<template>
	<div
		class="relative grid size-20 shrink-0 place-items-center"
		role="img"
		:aria-label="__('{0}% of checks passing', [value])"
	>
		<svg class="absolute inset-0 size-full -rotate-90" viewBox="0 0 36 36" aria-hidden="true">
			<circle
				class="text-ink-gray-2"
				cx="18"
				cy="18"
				:r="RADIUS"
				fill="none"
				stroke="currentColor"
				stroke-width="4"
			/>
			<circle
				class="text-ink-green-5"
				cx="18"
				cy="18"
				:r="RADIUS"
				fill="none"
				stroke="currentColor"
				stroke-width="4"
				stroke-linecap="round"
				:stroke-dasharray="`${arc} ${CIRCUMFERENCE}`"
			/>
		</svg>
		<span class="text-lg font-semibold text-ink-gray-9">{{ value }}%</span>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const RADIUS = 15;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const props = defineProps<{ value: number }>();
const arc = computed(() => (Math.min(Math.max(props.value, 0), 100) / 100) * CIRCUMFERENCE);
</script>

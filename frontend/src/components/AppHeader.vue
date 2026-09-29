<script setup lang="ts">
import { Button, Progress, Tooltip } from 'frappe-ui'
import { LucideCheck, LucideClock, LucideLogOut, LucideUnplug } from 'lucide-vue-next'

defineProps<{
  connected: boolean
  siteLabel: string | null
  lastChecked: string | null
  secPassed: number
  secTotal: number
}>()
defineEmits<{ (e: 'open-details'): void; (e: 'logout'): void }>()
</script>

<template>
  <header class="sticky top-0 z-40 flex h-[60px] items-center justify-between gap-4
                 border-b border-outline-gray-2 bg-surface-white px-5">
    <div class="flex items-center gap-3">
      <GraderLogo />
      <div class="flex flex-col leading-tight">
        <span class="text-base font-semibold text-ink-gray-9">ERPNext Assignment Portal</span>
        <span class="text-xs text-ink-gray-5">Student Portal</span>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <button
        v-if="connected"
        class="flex items-center gap-2 rounded-md border border-outline-gray-2 bg-surface-white
               px-2.5 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
        @click="$emit('open-details')"
      >
        <span class="size-1.5 rounded-full bg-surface-green-3" />
        <span class="font-medium tabular-nums">{{ siteLabel }}</span>
      </button>

      <div v-if="lastChecked" class="hidden items-center gap-1.5 text-xs text-ink-gray-5 md:flex">
        <LucideClock class="size-3.5" />
        <span>Checked {{ lastChecked }}</span>
      </div>

      <div v-if="secTotal" class="hidden w-40 flex-col gap-1 md:flex">
        <div class="flex justify-between text-xs text-ink-gray-5">
          <span>Overall progress</span>
          <span class="font-medium text-ink-gray-7 tabular-nums">{{ secPassed }}/{{ secTotal }}</span>
        </div>
        <Progress :value="secTotal ? Math.round((secPassed / secTotal) * 100) : 0" size="sm" />
      </div>

      <div class="flex items-center gap-1 border-l border-outline-gray-2 pl-2">
        <Tooltip v-if="connected" text="Site details">
          <Button variant="ghost" @click="$emit('open-details')">
            <template #icon><LucideUnplug class="size-4" /></template>
          </Button>
        </Tooltip>
        <Tooltip text="Log out">
          <Button variant="ghost" @click="$emit('logout')">
            <template #icon><LucideLogOut class="size-4" /></template>
          </Button>
        </Tooltip>
      </div>
    </div>
  </header>
</template>

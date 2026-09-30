import { toast } from "frappe-ui"
import { onMounted, onUnmounted, ref } from "vue"
import { type Run, getRun, startRun } from "../api"
import { type RunEvent, onRunUpdate } from "../socket"
import { __ } from "../translate"
import { requestErrorMessage } from "./errors"

const POLL_MS = 5000
const POLL_LIMIT_MS = 120000
const FINISHED = ["Done", "Error"]
const IN_PROGRESS = ["Queued", "Running"]

export function useRunWatcher() {
	const run = ref<Run | null>(null)
	const lastDone = ref<Run | null>(null)
	const grading = ref(false)
	const stillRunning = ref(false)
	let pollTimer: ReturnType<typeof setTimeout> | undefined
	let stopListening = () => {}

	function isSettled(name: string) {
		return run.value?.name === name && FINISHED.includes(run.value.status)
	}

	function settle(latest: Run) {
		clearTimeout(pollTimer)
		if (isSettled(latest.name)) return
		run.value = latest
		if (latest.status === "Done") lastDone.value = latest
		grading.value = false
		stillRunning.value = false
		if (latest.status === "Done") toast.success(__("Grading finished"))
	}

	function watchRun(name: string) {
		grading.value = true
		stillRunning.value = false
		const started = Date.now()
		clearTimeout(pollTimer)
		const tick = async () => {
			try {
				const latest = await getRun(name)
				if (FINISHED.includes(latest.status)) return settle(latest)
			} catch {
				// a failed poll is retried on the next tick
			}
			if (Date.now() - started > POLL_LIMIT_MS) {
				grading.value = false
				stillRunning.value = true
				return
			}
			pollTimer = setTimeout(tick, POLL_MS)
		}
		pollTimer = setTimeout(tick, POLL_MS)
	}

	function restore(latest: Run | null, done: Run | null) {
		run.value = latest
		lastDone.value = done
		if (latest && IN_PROGRESS.includes(latest.status)) watchRun(latest.name)
	}

	async function recheck() {
		grading.value = true
		try {
			const { run: name } = await startRun()
			const latest = await getRun(name)
			if (FINISHED.includes(latest.status)) return settle(latest)
			run.value = latest
			watchRun(name)
		} catch (e) {
			grading.value = false
			toast.error(requestErrorMessage(e))
		}
	}

	async function onRealtime(e: RunEvent) {
		if (e.run !== run.value?.name || isSettled(e.run)) return
		try {
			settle(await getRun(e.run))
		} catch {
			// the poll picks the run up on its next tick
		}
	}

	onMounted(() => {
		stopListening = onRunUpdate(onRealtime)
	})
	onUnmounted(() => {
		stopListening()
		clearTimeout(pollTimer)
	})

	return { run, lastDone, grading, stillRunning, restore, recheck }
}

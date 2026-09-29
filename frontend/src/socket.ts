import { io, type Socket } from "socket.io-client"
import { boot } from "./boot"

export interface RunEvent {
	run: string
	status: string
}

const RUN_EVENT = "grader_run"
const DEFAULT_SOCKETIO_PORT = 9000

let socket: Socket | null = null

function connect(): Socket {
	const { protocol, hostname, port } = window.location
	const socketPort = port ? `:${boot.socketio_port || DEFAULT_SOCKETIO_PORT}` : ""
	return io(`${protocol}//${hostname}${socketPort}/${boot.site_name}`, {
		withCredentials: true,
		reconnectionAttempts: 5,
	})
}

export function onRunUpdate(handler: (e: RunEvent) => void): () => void {
	socket ??= connect()
	socket.on(RUN_EVENT, handler)
	return () => socket?.off(RUN_EVENT, handler)
}

export interface Boot {
	csrf_token: string
	site_name: string
	socketio_port?: number
}

const globals = window as unknown as Partial<Boot>

export const boot: Boot = {
	csrf_token: globals.csrf_token ?? "",
	site_name: globals.site_name ?? "",
	socketio_port: globals.socketio_port,
}

from __future__ import annotations

import asyncio
import json
import logging
import os
import typing

from aiohttp import web

if typing.TYPE_CHECKING:
    from .client import BotManager

logger = logging.getLogger("AutoWorldDashboard")


class DashboardServer:
    def __init__(self, manager: "BotManager", host: str = "0.0.0.0", port: int = 8080):
        self.manager = manager
        self.host = host
        self.port = port
        self.ws_clients: set[web.WebSocketResponse] = set()
        self.logs_history: list[dict] = []
        self.runner: typing.Optional[web.AppRunner] = None
        self.site: typing.Optional[web.TCPSite] = None

        # Link manager to dashboard
        self.manager.dashboard = self

    def add_log_entry(self, slot: str, category: str, message: str, timestamp: str = ""):
        entry = {
            "time": timestamp,
            "slot": slot,
            "category": category,
            "message": message,
        }
        self.logs_history.append(entry)
        if len(self.logs_history) > 2000:
            self.logs_history.pop(0)

        # Broadcast log to all open WebSockets
        self.broadcast({"type": "log", "entry": entry})

    def notify_state_changed(self):
        self.broadcast({"type": "state", "bots": self.get_bots_state()})

    def broadcast(self, payload: dict):
        if not self.ws_clients:
            return
        msg = json.dumps(payload)
        for ws in list(self.ws_clients):
            if not ws.closed:
                asyncio.create_task(self._safe_send(ws, msg))

    async def _safe_send(self, ws: web.WebSocketResponse, msg: str):
        try:
            await ws.send_str(msg)
        except Exception:
            self.ws_clients.discard(ws)

    def get_bots_state(self) -> list[dict]:
        bots = []
        for bot in self.manager.bots.values():
            keys = [k for k in bot.received_item_names if "Key" in k or "Token" in k]
            bots.append({
                "name": bot.slot_name,
                "slot": bot.slot,
                "team": bot.team,
                "connected": bot.connected,
                "auto_enabled": bot.auto_enabled,
                "finished_game": bot.finished_game,
                "interval": bot.interval,
                "variance": bot.variance,
                "missing_count": len(bot.missing_locations),
                "checked_count": len(bot.checked_locations),
                "keys": keys,
            })
        return bots

    async def handle_index(self, request: web.Request) -> web.Response:
        html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "<h1>Auto World Dashboard</h1><p>dashboard.html not found</p>"
        return web.Response(text=content, content_type="text/html")

    async def handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.ws_clients.add(ws)

        # Send initial state
        init_payload = {
            "type": "init",
            "server_address": self.manager.server_address,
            "bots": self.get_bots_state(),
            "logs": self.logs_history[-500:],
        }
        await ws.send_str(json.dumps(init_payload))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        command = data.get("command", "")
                        if command:
                            await self.manager.handle_command(command)
                            self.notify_state_changed()
                    except Exception as e:
                        logger.error(f"Error handling dashboard command: {e}")
        finally:
            self.ws_clients.discard(ws)

        return ws

    async def start(self):
        app = web.Application()
        app.router.add_get("/", self.handle_index)
        app.router.add_get("/ws", self.handle_ws)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"[DASHBOARD] Web UI active at http://localhost:{self.port}")

    async def stop(self):
        for ws in list(self.ws_clients):
            await ws.close()
        self.ws_clients.clear()
        if self.runner:
            await self.runner.cleanup()

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import random
import ssl
import sys
import time
import typing
import urllib.parse
import uuid

import websockets
from NetUtils import ClientStatus, JSONtoTextParser, decode, encode
from Utils import get_cert_none_ssl_context, init_logging, stream_input
from .items import ITEM_NAME_TO_ID, ITEM_TABLE
from .locations import LOCATION_NAME_TO_ID, LOCATION_TABLE

logger = logging.getLogger("AutoWorldBot")


def get_timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


class AutoBot:
    def __init__(
        self,
        slot_name: str,
        server_address: str,
        password: typing.Optional[str] = None,
        interval: float = 30.0,
        variance: float = 0.30,
        auto_enabled: bool = True,
        manager: "BotManager" = None,
    ):
        self.slot_name = slot_name
        self.server_address = server_address
        self.password = password
        self.interval = max(0.5, float(interval))
        self.variance = max(0.0, min(0.9, float(variance)))
        self.auto_enabled = auto_enabled
        self.manager = manager

        self.team: typing.Optional[int] = None
        self.slot: typing.Optional[int] = None
        self.connected = False
        self.finished_game = False

        self.missing_locations: list[int] = []
        self.checked_locations: set[int] = set()
        self.items_received: list[dict] = []
        self.received_item_names: list[str] = []

        self.slot_info: dict = {}
        self.slot_data: dict = {}
        self.players: dict[int, str] = {0: "Archipelago"}
        self.item_id_to_name: dict[int, str] = {v: k for k, v in ITEM_NAME_TO_ID.items()}
        self.loc_id_to_name: dict[int, str] = {v: k for k, v in LOCATION_NAME_TO_ID.items()}

        self.websocket: typing.Optional[websockets.WebSocketClientProtocol] = None
        self.listen_task: typing.Optional[asyncio.Task] = None
        self.loop_task: typing.Optional[asyncio.Task] = None
        self.hint_loop_task: typing.Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()

    def log(self, message: str, level: str = "INFO", category: str = "system"):
        if level == "ERROR":
            logger.error(f"[{self.slot_name}] {message}")
        elif level == "WARNING":
            logger.warning(f"[{self.slot_name}] {message}")
        else:
            logger.info(f"[{self.slot_name}] {message}")

        if self.manager and self.manager.dashboard:
            self.manager.dashboard.add_log_entry(self.slot_name, category, message, get_timestamp())

    async def connect(self, target_url: typing.Optional[str] = None):
        self.stop_event.clear()
        if target_url is None:
            raw = self.server_address.strip()
            if raw.startswith("archipelago://"):
                raw = raw.replace("archipelago://", "wss://")

            if "://" in raw:
                target_url = raw
            else:
                host_part = raw.split(":")[0].lower()
                if host_part in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    target_url = f"ws://{raw}"
                else:
                    target_url = f"wss://{raw}"

        self.log(f"Connecting to {target_url}...", category="system")
        try:
            ssl_context = None
            if target_url.startswith("wss://"):
                ssl_context = get_cert_none_ssl_context()

            server_url = urllib.parse.urlparse(target_url)
            port = server_url.port or 38281

            self.websocket = await websockets.connect(
                target_url,
                port=port,
                ssl=ssl_context,
                max_size=None,
                ping_interval=30,
                ping_timeout=10,
                extra_headers=[("User-Agent", "ArchipelagoAutoBot/1.0")],
            )
            self.connected = True
            self.listen_task = asyncio.create_task(self._listen_loop())
            self.loop_task = asyncio.create_task(self._auto_check_loop())
            self.hint_loop_task = asyncio.create_task(self._auto_hint_loop())
            if self.manager:
                self.manager.notify_state()
        except (websockets.InvalidMessage, websockets.InvalidStatusCode, websockets.InvalidHandshake) as e:
            if target_url.startswith("ws://"):
                fallback_url = "wss://" + target_url[5:]
                self.log(f"Received handshake failure on ws://, attempting encrypted TLS connection ({fallback_url})...", category="system")
                await self.connect(fallback_url)
            elif target_url.startswith("wss://"):
                fallback_url = "ws://" + target_url[6:]
                self.log(f"Received TLS handshake failure on wss://, attempting unencrypted connection ({fallback_url})...", category="system")
                await self.connect(fallback_url)
            else:
                self.log(f"Connection failed: {e}", level="ERROR", category="error")
                self.connected = False
                if self.manager:
                    self.manager.notify_state()
        except Exception as e:
            self.log(f"Connection failed: {e}", level="ERROR", category="error")
            self.connected = False
            if self.manager:
                self.manager.notify_state()

    async def disconnect(self):
        self.stop_event.set()
        if self.hint_loop_task:
            self.hint_loop_task.cancel()
        if self.loop_task:
            self.loop_task.cancel()
        if self.listen_task:
            self.listen_task.cancel()
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.connected = False
        self.log("Disconnected.", category="system")
        if self.manager:
            self.manager.notify_state()

    async def send_packet(self, packet: list[dict]):
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(encode(packet))
            except Exception as e:
                self.log(f"Error sending packet: {e}", level="ERROR", category="error")

    async def _listen_loop(self):
        try:
            async for raw_message in self.websocket:
                try:
                    data = decode(raw_message)
                    for cmd_data in data:
                        await self._handle_packet(cmd_data)
                except Exception as e:
                    self.log(f"Error processing packet: {e}", level="ERROR", category="error")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log(f"Connection error: {e}", level="ERROR", category="error")
        finally:
            self.connected = False
            if self.manager:
                self.manager.notify_state()

    async def _handle_packet(self, cmd_data: dict):
        cmd = cmd_data.get("cmd")

        if cmd == "RoomInfo":
            # Respond with GetDataPackage and Connect
            await self.send_packet([
                {"cmd": "GetDataPackage"},
                {
                    "cmd": "Connect",
                    "password": self.password or "",
                    "game": "Auto World",
                    "name": self.slot_name,
                    "version": {"major": 0, "minor": 5, "build": 0, "class": "Version"},
                    "tags": ["AP", "DeathLink"],
                    "items_handling": 0b111,
                    "uuid": uuid.uuid4().hex,
                    "slot_data": True,
                }
            ])

        elif cmd == "DataPackage":
            dp = cmd_data.get("data", {})
            for game, gdata in dp.get("games", {}).items():
                for iname, iid in gdata.get("item_name_to_id", {}).items():
                    self.item_id_to_name[iid] = iname
                for lname, lid in gdata.get("location_name_to_id", {}).items():
                    self.loc_id_to_name[lid] = lname

        elif cmd == "Connected":
            self.connected = True
            self.team = cmd_data.get("team", 0)
            self.slot = cmd_data.get("slot", 1)
            self.missing_locations = cmd_data.get("missing_locations", [])
            self.checked_locations = set(cmd_data.get("checked_locations", []))
            self.slot_info = cmd_data.get("slot_info", {})
            self.slot_data = cmd_data.get("slot_data", {})

            for p in cmd_data.get("players", []):
                self.players[p.slot] = p.alias or p.name

            # Check if check_interval is specified in slot_data
            if "check_interval" in self.slot_data:
                if self.interval == 30.0:
                    self.interval = float(self.slot_data["check_interval"])

            # Check if check_interval_variance is specified in slot_data
            if "check_interval_variance" in self.slot_data:
                if self.variance == 0.30:
                    self.variance = float(self.slot_data["check_interval_variance"]) / 100.0

            self.log(
                f"Connected! (Slot {self.slot}, Team {self.team}) | "
                f"Missing checks: {len(self.missing_locations)} | "
                f"Interval: {self.interval}s (±{int(self.variance*100)}%) | Auto-check: {'ON' if self.auto_enabled else 'PAUSED'}",
                category="system"
            )

            # Check if already fulfilled victory
            self._check_victory_condition()
            if self.manager:
                self.manager.notify_state()

        elif cmd == "ConnectionRefused":
            errors = cmd_data.get("errors", [])
            self.log(f"Connection refused by server: {errors}", level="ERROR", category="error")
            await self.disconnect()

        elif cmd == "ReceivedItems":
            items = cmd_data.get("items", [])
            for item in items:
                # NetworkItem: item, location, player, flags
                iid = item.item if hasattr(item, "item") else item.get("item")
                loc_id = item.location if hasattr(item, "location") else item.get("location")
                sender = item.player if hasattr(item, "player") else item.get("player")

                item_name = self.item_id_to_name.get(iid, f"Item {iid}")
                sender_name = self.players.get(sender, f"Player {sender}")
                loc_name = self.loc_id_to_name.get(loc_id, f"Location {loc_id}")

                self.items_received.append(item)
                self.received_item_names.append(item_name)

                self.log(f"Received '{item_name}' from {sender_name} ({loc_name})", category="item")

            self._check_victory_condition()
            if self.manager:
                self.manager.notify_state()

        elif cmd == "RoomUpdate":
            new_checked = cmd_data.get("checked_locations", [])
            for loc in new_checked:
                self.checked_locations.add(loc)
                if loc in self.missing_locations:
                    self.missing_locations.remove(loc)

            if "players" in cmd_data:
                for p in cmd_data["players"]:
                    self.players[p.slot] = p.alias or p.name

            if self.manager:
                self.manager.notify_state()

        elif cmd == "PrintJSON":
            p_type = cmd_data.get("type", "")
            parts = cmd_data.get("data", [])
            full_text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
            cat = "chat"
            if p_type == "Goal":
                cat = "goal"
            elif p_type == "Hint":
                cat = "hint"
            elif p_type in ["ItemSend", "ItemCheat"]:
                cat = "item"
            
            if p_type in ["Chat", "ServerChat", "Goal", "Hint", "ItemCheat"]:
                self.log(f"[{p_type}] {full_text}", category=cat)

        elif cmd == "Bounced":
            tags = cmd_data.get("tags", [])
            if "DeathLink" in tags:
                data = cmd_data.get("data", {})
                source = data.get("source", "Unknown")
                cause = data.get("cause", "died")
                self.log(f"Received death triggered by {source}: {cause}", category="death")

    def _check_victory_condition(self):
        if self.finished_game:
            return

        goal_type = self.slot_data.get("goal", 0)
        # Goal 0: Victory Token
        if goal_type == 0:
            if "Victory Token" in self.received_item_names:
                self.trigger_goal("Found Victory Token!")
        # Goal 1: Full Clear
        elif goal_type == 1:
            if len(self.missing_locations) == 0:
                self.trigger_goal("Cleared all locations!")

    def trigger_goal(self, reason: str = ""):
        if self.finished_game:
            return
        self.finished_game = True
        self.log(f"Victory condition achieved! ({reason}) -> Sending CLIENT_GOAL", category="goal")
        asyncio.create_task(
            self.send_packet([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
        )
        if self.manager:
            self.manager.notify_state()

    def get_in_logic_missing_locations(self) -> list[int]:
        """Returns list of missing location IDs that are logically reachable given received items."""
        in_logic = []
        for loc_id in self.missing_locations:
            loc_name = self.loc_id_to_name.get(loc_id, "")
            if not loc_name or loc_name.startswith("Tier 1 -"):
                in_logic.append(loc_id)
            elif loc_name.startswith("Tier "):
                try:
                    tier_str = loc_name.split()[1]
                    tier_num = int(tier_str)
                    if tier_num == 1 or f"Tier {tier_num} Key" in self.received_item_names:
                        in_logic.append(loc_id)
                except (IndexError, ValueError):
                    in_logic.append(loc_id)
            else:
                in_logic.append(loc_id)
        return in_logic

    async def check_locations(self, count: int = 1) -> list[int]:
        if not self.connected or not self.missing_locations:
            return []

        # Find in-logic locations first
        in_logic = self.get_in_logic_missing_locations()
        pool = in_logic if in_logic else self.missing_locations

        to_check = pool[:count]
        if not to_check:
            return []

        for loc_id in to_check:
            self.missing_locations.remove(loc_id)
            self.checked_locations.add(loc_id)
            loc_name = self.loc_id_to_name.get(loc_id, f"ID {loc_id}")
            self.log(f"Checked location '{loc_name}' ({len(self.missing_locations)} remaining)", category="check")

        await self.send_packet([{"cmd": "LocationChecks", "locations": to_check}])
        self._check_victory_condition()
        if self.manager:
            self.manager.notify_state()
        return to_check

    async def _auto_check_loop(self):
        while not self.stop_event.is_set():
            jitter = random.uniform(1.0 - self.variance, 1.0 + self.variance)
            sleep_time = max(0.2, self.interval * jitter)
            await asyncio.sleep(sleep_time)
            if self.connected and self.auto_enabled and self.missing_locations:
                await self.check_locations(1)

    async def _auto_hint_loop(self):
        while not self.stop_event.is_set():
            jitter = random.uniform(1.0 - self.variance, 1.0 + self.variance)
            sleep_time = max(1.0, (self.interval * 5) * jitter)
            await asyncio.sleep(sleep_time)
            if self.connected and self.auto_enabled:
                await self.hint_random_missing_item()

    async def hint_random_missing_item(self) -> typing.Optional[str]:
        if not self.connected:
            return None

        tiers = self.slot_data.get("progression_tiers", 15)
        needed_progression = [f"Tier {t} Key" for t in range(2, tiers + 1)] + ["Victory Token"]
        missing_progression = [item for item in needed_progression if item not in self.received_item_names]

        if not missing_progression:
            # All items/keys for this slot have been found; stop auto-hinting
            return None

        item_to_hint = random.choice(missing_progression)
        self.log(f"Auto-hinting for item '{item_to_hint}'", category="hint")
        await self.send_chat(f"!hint {item_to_hint}")
        return item_to_hint

    async def send_chat(self, msg: str):
        if self.connected:
            self.log(f"Sent chat message: {msg}", category="chat")
            await self.send_packet([{"cmd": "Say", "text": msg}])

    async def trigger_death(self, cause: str = ""):
        if self.connected:
            cause_text = cause or f"{self.slot_name} was liquidated for science"
            self.log(f"Sending DeathLink bounce: {cause_text}", category="death")
            await self.send_packet([{
                "cmd": "Bounce",
                "tags": ["DeathLink"],
                "data": {
                    "time": time.time(),
                    "source": self.slot_name,
                    "cause": cause_text,
                }
            }])


class BotManager:
    def __init__(self, server_address: str, password: typing.Optional[str] = None):
        self.server_address = server_address
        self.password = password
        self.bots: dict[str, AutoBot] = {}
        self.running = True
        self.dashboard = None

    def notify_state(self):
        if self.dashboard:
            self.dashboard.notify_state_changed()

    def add_bot(
        self,
        slot_name: str,
        interval: float = 30.0,
        variance: float = 0.30,
        auto_enabled: bool = True,
    ) -> AutoBot:
        if slot_name in self.bots:
            return self.bots[slot_name]
        bot = AutoBot(
            slot_name=slot_name,
            server_address=self.server_address,
            password=self.password,
            interval=interval,
            variance=variance,
            auto_enabled=auto_enabled,
            manager=self,
        )
        self.bots[slot_name] = bot
        self.notify_state()
        return bot

    async def start_all(self):
        tasks = [bot.connect() for bot in self.bots.values()]
        await asyncio.gather(*tasks)

    async def stop_all(self):
        self.running = False
        tasks = [bot.disconnect() for bot in self.bots.values()]
        await asyncio.gather(*tasks)

    def print_status(self, target_slot: typing.Optional[str] = None):
        bots_to_show = (
            [self.bots[target_slot]]
            if target_slot and target_slot in self.bots
            else list(self.bots.values())
        )

        if not bots_to_show:
            print("No bots currently configured.")
            return

        print("\n" + "=" * 85)
        print(f"{'Slot Name':<15} {'Status':<12} {'Missing':<10} {'Checked':<10} {'Goal':<8} {'Auto':<8} {'Interval / Jitter'}")
        print("-" * 85)
        for bot in bots_to_show:
            status = "Connected" if bot.connected else "Disconnected"
            goal = "YES" if bot.finished_game else "No"
            auto = "ACTIVE" if bot.auto_enabled else "PAUSED"
            keys = [k for k in bot.received_item_names if "Key" in k or "Token" in k]
            keys_str = f" [Keys: {', '.join(keys)}]" if keys else ""
            print(
                f"{bot.slot_name:<15} {status:<12} {len(bot.missing_locations):<10} "
                f"{len(bot.checked_locations):<10} {goal:<8} {auto:<8} {bot.interval}s (±{int(bot.variance*100)}%){keys_str}"
            )
        print("=" * 85 + "\n")

    async def handle_command(self, cmd_line: str):
        parts = cmd_line.strip().split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ["help", "?"]:
            self._print_help()

        elif cmd in ["status", "list"]:
            target = args[0] if args else None
            self.print_status(target)

        elif cmd == "interval":
            if not args:
                print("Usage: interval <seconds>  OR  interval <slot> <seconds>")
                return
            if len(args) == 1:
                try:
                    sec = float(args[0])
                    for bot in self.bots.values():
                        bot.interval = max(0.5, sec)
                    logger.info(f"[SYSTEM] Updated check interval for all bots to {sec}s")
                except ValueError:
                    print("Invalid interval number.")
            else:
                slot, sec_str = args[0], args[1]
                if slot in self.bots:
                    try:
                        sec = float(sec_str)
                        self.bots[slot].interval = max(0.5, sec)
                        logger.info(f"[SYSTEM] Updated check interval for {slot} to {sec}s")
                    except ValueError:
                        print("Invalid interval number.")
                else:
                    print(f"Bot '{slot}' not found.")
            self.notify_state()

        elif cmd == "variance":
            if not args:
                print("Usage: variance <percent 0-90>  OR  variance <slot> <percent 0-90>")
                return
            if len(args) == 1:
                try:
                    pct = float(args[0])
                    v = max(0.0, min(0.9, pct / 100.0 if pct > 1.0 else pct))
                    for bot in self.bots.values():
                        bot.variance = v
                    logger.info(f"[SYSTEM] Updated interval variance for all bots to ±{int(v*100)}%")
                except ValueError:
                    print("Invalid variance percentage.")
            else:
                slot, pct_str = args[0], args[1]
                if slot in self.bots:
                    try:
                        pct = float(pct_str)
                        v = max(0.0, min(0.9, pct / 100.0 if pct > 1.0 else pct))
                        self.bots[slot].variance = v
                        logger.info(f"[SYSTEM] Updated interval variance for {slot} to ±{int(v*100)}%")
                    except ValueError:
                        print("Invalid variance percentage.")
                else:
                    print(f"Bot '{slot}' not found.")
            self.notify_state()

        elif cmd == "pause":
            target = args[0] if args else None
            if target:
                if target in self.bots:
                    self.bots[target].auto_enabled = False
                    logger.info(f"[SYSTEM] Paused auto-checks for {target}")
                else:
                    print(f"Bot '{target}' not found.")
            else:
                for bot in self.bots.values():
                    bot.auto_enabled = False
                logger.info("[SYSTEM] Paused auto-checks for all bots.")
            self.notify_state()

        elif cmd == "resume":
            target = args[0] if args else None
            if target:
                if target in self.bots:
                    self.bots[target].auto_enabled = True
                    logger.info(f"[SYSTEM] Resumed auto-checks for {target}")
                else:
                    print(f"Bot '{target}' not found.")
            else:
                for bot in self.bots.values():
                    bot.auto_enabled = True
                logger.info("[SYSTEM] Resumed auto-checks for all bots.")
            self.notify_state()

        elif cmd == "check":
            if not args:
                for bot in self.bots.values():
                    asyncio.create_task(bot.check_locations(1))
                return

            slot = args[0]
            count = 1
            if len(args) > 1:
                try:
                    count = int(args[1])
                except ValueError:
                    count = 1

            if slot.lower() == "all":
                for bot in self.bots.values():
                    asyncio.create_task(bot.check_locations(count))
            elif slot in self.bots:
                asyncio.create_task(self.bots[slot].check_locations(count))
            else:
                try:
                    c = int(slot)
                    for bot in self.bots.values():
                        asyncio.create_task(bot.check_locations(c))
                except ValueError:
                    print(f"Bot '{slot}' not found.")

        elif cmd == "goal":
            target = args[0] if args else None
            if target and target.lower() != "all":
                if target in self.bots:
                    self.bots[target].trigger_goal("Manual command")
                else:
                    print(f"Bot '{target}' not found.")
            else:
                for bot in self.bots.values():
                    bot.trigger_goal("Manual command")
            self.notify_state()

        elif cmd == "hint":
            if len(args) < 2:
                print("Usage: hint <slot> <item_or_location_name | missing>")
                return
            slot = args[0]
            target_name = " ".join(args[1:])
            if slot in self.bots:
                if target_name.lower() == "missing":
                    await self.bots[slot].hint_random_missing_item()
                else:
                    await self.bots[slot].send_chat(f"!hint {target_name}")
            else:
                print(f"Bot '{slot}' not found.")

        elif cmd == "say":
            if len(args) < 2:
                print("Usage: say <slot> <message>")
                return
            slot = args[0]
            msg = " ".join(args[1:])
            if slot in self.bots:
                await self.bots[slot].send_chat(msg)
            else:
                print(f"Bot '{slot}' not found.")

        elif cmd == "death":
            slot = args[0] if args else None
            cause = " ".join(args[1:]) if len(args) > 1 else ""
            if slot and slot in self.bots:
                await self.bots[slot].trigger_death(cause)
            elif not slot and self.bots:
                first_bot = next(iter(self.bots.values()))
                await first_bot.trigger_death(cause)
            else:
                print(f"Bot '{slot}' not found.")

        elif cmd == "connect":
            if not args:
                for bot in self.bots.values():
                    if not bot.connected:
                        asyncio.create_task(bot.connect())
                return
            slot = args[0]
            if slot in self.bots:
                asyncio.create_task(self.bots[slot].connect())
            else:
                bot = self.add_bot(slot)
                asyncio.create_task(bot.connect())

        elif cmd == "disconnect":
            slot = args[0] if args else None
            if slot and slot in self.bots:
                await self.bots[slot].disconnect()
            else:
                for bot in self.bots.values():
                    await bot.disconnect()
            self.notify_state()

        elif cmd in ["exit", "quit"]:
            logger.info("[SYSTEM] Shutting down bots...")
            await self.stop_all()

        else:
            print(f"Unknown command '{cmd}'. Type 'help' for available commands.")

    def _print_help(self):
        print("""
Available CLI Commands:
  help / ?                      Show this help menu
  status [slot]                 Show live status table of all or a specific bot
  interval <sec>                Set check interval in seconds for all bots
  interval <slot> <sec>         Set check interval for a specific slot
  variance <percent 0-90>       Set interval variance percentage for all bots
  variance <slot> <percent>     Set interval variance percentage for a specific slot
  pause [slot]                  Pause auto-checking for all or a specific bot
  resume [slot]                 Resume auto-checking for all or a specific bot
  check [slot|all] [count]      Manually trigger 1 or more location checks
  goal [slot|all]               Manually trigger goal completion (CLIENT_GOAL)
  hint <slot> <item/missing>    Send !hint command from slot (or hint random missing item)
  say <slot> <message>          Send a chat message to the room from slot
  death [slot] [cause]          Trigger a DeathLink bounce from slot
  connect [slot]                Connect or reconnect a slot
  disconnect [slot]             Disconnect a slot or all bots
  exit / quit                   Disconnect all bots and exit
""")


async def console_loop(manager: BotManager):
    queue: asyncio.Queue[str] = asyncio.Queue()
    stream_input(sys.stdin, queue)
    while manager.running:
        try:
            line = await queue.get()
            queue.task_done()
            if line:
                await manager.handle_command(line)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception(f"Error in console loop: {e}")


def main(*cli_args: str):
    init_logging("AutoWorldBot")

    parser = argparse.ArgumentParser(description="Archipelago Auto World Automated Bot Client")
    parser.add_argument("--connect", "-c", default="localhost:38281", help="Archipelago server host:port")
    parser.add_argument("--password", "-p", default="", help="Archipelago room password")
    parser.add_argument("--slots", "-s", nargs="+", default=["Bot1"], help="Slot name(s) to connect")
    parser.add_argument("--interval", "-i", type=float, default=30.0, help="Check interval in seconds (default: 30)")
    parser.add_argument("--variance", "-v", type=float, default=30.0, help="Interval variance percentage (default: 30)")
    parser.add_argument("--no-auto", action="store_true", help="Start with autonomous checks paused")
    parser.add_argument("--web-port", type=int, default=8080, help="Port for the interactive Web Dashboard (default: 8080)")
    parser.add_argument("--no-web", action="store_true", help="Disable the interactive Web Dashboard")

    args = parser.parse_args(cli_args if cli_args else None)

    manager = BotManager(server_address=args.connect, password=args.password)
    auto_enabled = not args.no_auto
    variance_val = max(0.0, min(0.9, args.variance / 100.0 if args.variance > 1.0 else args.variance))

    for slot in args.slots:
        manager.add_bot(slot, interval=args.interval, variance=variance_val, auto_enabled=auto_enabled)

    logger.info(f"[SYSTEM] Starting Auto World Bot Manager for slots: {', '.join(args.slots)}")
    logger.info(f"[SYSTEM] Target server: {args.connect} | Interval: {args.interval}s (±{int(variance_val*100)}%) | Auto: {'ON' if auto_enabled else 'PAUSED'}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    dashboard = None
    if not args.no_web:
        from .dashboard import DashboardServer
        dashboard = DashboardServer(manager, host="0.0.0.0", port=args.web_port)

    try:
        if dashboard:
            loop.create_task(dashboard.start())
        loop.create_task(manager.start_all())
        loop.run_until_complete(console_loop(manager))
    except KeyboardInterrupt:
        logger.info("[SYSTEM] Interrupted by user. Exiting...")
    finally:
        if dashboard:
            loop.run_until_complete(dashboard.stop())
        loop.run_until_complete(manager.stop_all())
        loop.close()


if __name__ == "__main__":
    main(*sys.argv[1:])

# Auto World Setup Guide

## Overview
**Auto World** is a specialized Archipelago world designed specifically for automated testing, debugging, and verification of external tools (such as trackers, alert bots, webhooks, and multiworld integrations).

It allows automated client bots to connect, self-play games, perform checks on configurable intervals, receive items, complete goals, and simulate events via command-line interface.

## Generating an Auto World Multiworld
You can generate a multiworld with one or more Auto World slots using the standard Archipelago generator or webhost.

Example player YAML:
```yaml
name: Bot1
game: Auto World
Auto World:
  location_count: 20
  progression_tiers: 3
  default_check_interval: 30
  goal: victory_token
```

## Running the Automated Bot Manager

You can launch the automated client manager directly from the command line:

```bash
# Connect 2 bots to a local Archipelago server with a 10s check interval:
python -m worlds.auto_world.client --connect localhost:38281 --slots Bot1 Bot2 --interval 10
```

### CLI Options
- `--connect` / `-c`: Host and port of the Archipelago server (default: `localhost:38281`).
- `--password` / `-p`: Room password (if required).
- `--slots` / `-s`: Space-separated list of slot names to connect.
- `--interval` / `-i`: Check interval in seconds (default: `30`).
- `--no-auto`: Start with auto-checking paused (for manual CLI testing).

### Interactive CLI Commands During Run
While bots are running, you can type live commands into the terminal:
- `status [slot]`: Show live status table of all or a specific bot.
- `interval <seconds>` / `interval <slot> <seconds>`: Change check interval dynamically.
- `pause [slot]` / `resume [slot]`: Pause or resume autonomous checks.
- `check [slot|all] [count]`: Instantly trigger 1 or more location checks.
- `goal [slot|all]`: Instantly trigger goal completion (`CLIENT_GOAL`).
- `hint <slot> <item/location>`: Send a `!hint` server command from that slot.
- `say <slot> <message>`: Send a chat message to the room.
- `death [slot] [cause]`: Send a DeathLink bounce.
- `disconnect [slot]` / `connect [slot]`: Disconnect or reconnect bots.
- `exit` / `quit`: Disconnect all bots and exit cleanly.

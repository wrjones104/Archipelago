# Auto World Setup Guide

## Overview
**Auto World** is a specialized Archipelago world designed for automated testing, debugging, and verification of external tools (such as trackers, alert bots, webhooks, and multiworld integrations).

It allows automated client bots to connect, self-play games, perform checks on configurable intervals with randomized jitter, receive items, complete goals, and simulate events via both a real-time **Web Dashboard** and **Command-Line Interface**.

---

## Generating an Auto World Multiworld
You can generate a multiworld with one or more Auto World slots using the standard Archipelago generator or webhost.

### Example Player YAML
```yaml
name: Bot{player}
game: Auto World
Auto World:
  location_count: 300           # Total checks (range: 5 to 300)
  progression_tiers: 15         # Number of unlock tiers (range: 1 to 15)
  check_interval: 30            # Base check interval in seconds (range: 1 to 3600)
  check_interval_variance: 30   # Random interval jitter % (range: 0 to 90%)
  goal: victory_token           # Goal: victory_token or full_clear
```

---

## Running the Automated Bot Manager

You can launch the automated client manager directly from the command line:

```bash
# Connect 8 bots with a 15s base check interval and 30% jitter:
python -m worlds.auto_world.client --connect archipelago.today:58493 --slots Bot1 Bot2 Bot3 Bot4 Bot5 Bot6 Bot7 Bot8 --interval 15 --variance 30
```

### CLI Arguments
- `--connect` / `-c`: Host and port of the Archipelago server (default: `localhost:38281`). Supports both unencrypted (`ws://`) and encrypted TLS (`wss://`) connections.
- `--password` / `-p`: Room password (if required).
- `--slots` / `-s`: Space-separated list of slot names to connect.
- `--interval` / `-i`: Base check interval in seconds (default: `30.0`).
- `--variance` / `-v`: Random interval jitter percentage (default: `30.0`, meaning $\pm 30\%$).
- `--no-auto`: Start with autonomous checking paused (for manual testing).
- `--web-port`: Port for the interactive Web Dashboard (default: `8080`). If the port is already occupied, the manager automatically increments to the next available open port (e.g. `8081`, `8082`).
- `--no-web`: Disable the embedded Web Dashboard server.

---

## Interactive Web Dashboard

When the bot manager starts, it hosts a real-time web dashboard at **`http://localhost:8080`**.

### Dashboard Features:
1. **Real-Time Filterable Log Stream**:
   - **Type Filter Pills**: Instantly toggle logs by category:
     - `All`: View full unified log stream.
     - `Checks`: Location checks and checks remaining.
     - `Items`: Incoming item receives and sends.
     - `Hints`: Hint requests and responses.
     - `Goals`: Goal completion announcements.
     - `Chat / Server`: Server chat messages and broadcast alerts.
     - `DeathLink`: DeathLink bounce packets.
     - `Errors`: Connection errors and exceptions.
   - **Slot Filter Dropdown**: Filter logs for a specific bot or view all slots together.
   - **Free-Text Search**: Live text search matching messages and slot names.
   - **Auto-Scroll Toggle & Clear Logs**: Pause scrolling to inspect past messages.

2. **Visual Slot Progression Chart**:
   - Side-by-side graphical progress comparison showing percentage and check counts for all slots.
   - Live celebration indicator (`🏆 WINNER`) as slots complete their goals.

3. **Per-Slot Management Cards**:
   - Live connection state badge (Connected / Disconnected) and Auto-check status (Active / Paused).
   - Dynamic completion progress bar ($0\% \to 100\%$).
   - Current interval and variance readout.
   - Held progression keys badges (`Tier 2 Key`, `Tier 3 Key`, `Victory Token`).
   - Celebration trophy banner (`🏆 GOAL COMPLETED!`).

4. **Live Interactive Controls (Web & CLI)**:
   - **Global Actions**: `Pause All`, `Resume All`, `Check +1 All`, `Check +5 All`, `Goal All`, and global interval/variance inputs.
   - **Per-Slot Actions**: `+1 Check`, `+5 Checks`, `💡 Hint Missing Item`, `⏸ Pause / ▶ Resume`, `🏆 Goal`, `💀 Death`, `🔌 Disconnect / Connect`.

---

## Autonomous Bot Behaviors

- **Location Checking with Jitter**:
  Each bot calculates its next check delay using:
  $$\text{Delay} = \text{Interval} \times \text{random}(1 - \text{variance}, 1 + \text{variance})$$
  This creates natural, staggered activity across multiple bots.
- **Auto-Hinting**:
  Bots automatically send `!hint <item>` for a randomly chosen missing progression key or Victory Token every $5 \times \text{interval}$ seconds.
  Once a bot has collected all of its required items, it automatically stops sending hint requests.
- **Auto-Goal**:
  When a bot receives its required victory item (or completes full clear), it automatically sends `CLIENT_GOAL` to trigger victory alerts on the server.

---

## Interactive CLI Commands Reference

You can also type live commands directly into the terminal while bots are running:

| Command | Description | Example |
| :--- | :--- | :--- |
| `status [slot]` | Show live status table of all or a specific bot | `status` |
| `interval <sec>` | Set check interval in seconds for all bots | `interval 10` |
| `interval <slot> <sec>` | Set check interval for a specific slot | `interval Bot1 5` |
| `variance <pct>` | Set interval variance percentage (0–90%) for all bots | `variance 40` |
| `variance <slot> <pct>` | Set interval variance for a specific slot | `variance Bot2 20` |
| `pause [slot]` | Pause auto-checking for all or a specific bot | `pause Bot1` |
| `resume [slot]` | Resume auto-checking for all or a specific bot | `resume Bot1` |
| `check [slot\|all] [count]` | Manually trigger 1 or more location checks | `check Bot1 5` |
| `goal [slot\|all]` | Manually trigger goal completion (`CLIENT_GOAL`) | `goal Bot1` |
| `hint <slot> <item\|missing>` | Send `!hint` command (or hint random missing item) | `hint Bot1 missing` |
| `say <slot> <message>` | Send a chat message to the room from slot | `say Bot1 Hello!` |
| `death [slot] [cause]` | Trigger a DeathLink bounce from slot | `death Bot1 Fell into lava` |
| `connect [slot]` | Connect or reconnect a slot | `connect Bot1` |
| `disconnect [slot]` | Disconnect a slot or all bots | `disconnect Bot1` |
| `exit` / `quit` | Disconnect all bots and exit cleanly | `exit` |

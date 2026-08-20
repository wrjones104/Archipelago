# Auto World

**Auto World** is an automated multiworld test environment designed for Archipelago.

## Features
- **Configurable Locations & Tiers**: Generate anywhere from 5 to 300 locations partitioned across 1 to 15 progression tiers.
- **Progression Logic**: Key items unlock higher tiers, allowing validation of progression logic, trackers, and item routing.
- **Automated Multi-Slot Bot Runner**: Headless Python runner that connects multiple slots concurrently, self-plays games, collects items, and reports goal completion to the server.
- **Interval Variance (Jitter)**: Configurable randomized interval jitter ($\pm 0\%$ to $\pm 90\%$) for natural staggered checking.
- **Smart Auto-Hinting**: Automatically hints missing progression keys every $5\times$ interval, stopping once all keys are found.
- **Interactive Web Dashboard (`http://localhost:8080`)**: Real-time browser UI featuring:
  - Categorized log stream with quick filter pills (`Checks`, `Items`, `Hints`, `Goals`, `Chat`, `DeathLink`, `Errors`).
  - Search box and per-slot dropdown filtering.
  - Graphical slot progression comparison chart.
  - Live cards with progress bars, key badges, and goal celebration banners.
  - Interactive live control buttons for global and per-slot actions.
- **Live Terminal CLI**: Interactive console commands (`check`, `interval`, `variance`, `pause`, `resume`, `goal`, `hint`, `say`, `death`, `status`).

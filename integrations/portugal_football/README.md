# Portugal Football for Home Assistant

Custom integration for Portuguese football, starting with Liga Portugal (Football-Data.org / competition code PPL).

## Features

- Live-match sensor
- League table
- Upcoming and recent fixtures
- Top scorers
- Derived statistics
- Binary sensor indicating when a league match is live
- Home Assistant bus event `portugal_football_goal` when the score changes during a live match
- Lovelace custom card with live, table, fixtures, scorers and stats views

## Installation from this monorepo

This repository contains multiple Home Assistant projects, so it is not directly installable as a normal HACS integration repository. Use the installer in:

`installations/install_portugal_football.sh`

From the Home Assistant Terminal & SSH add-on:

```bash
curl -fsSL https://raw.githubusercontent.com/BrunoCunha1983-creator/ha_apps/main/installations/install_portugal_football.sh | bash
```

Restart Home Assistant afterwards.

Then go to **Settings → Devices & services → Add integration → Portugal Football** and enter your Football-Data.org API key.

## Lovelace resource

Add:

```
/local/community/portugal_football/portugal-football-card.js
```

as a JavaScript Module in **Settings → Dashboards → Resources**.

Example:

```yaml
type: custom:portugal-football-card
view: table
```

Supported views: `live`, `table`, `fixtures`, `scorers`, `stats`.

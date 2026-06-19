# NEON RACER — Pygame Car Racing Game

A premium vertical-scrolling arcade racer with 8 themed stages, boss battles, campaign progression, per-level mechanics, and cyberpunk neon visuals.

---

## Game Controls

| Key | Action |
|---|---|
| **← / A** | Steer left |
| **→ / D** | Steer right |
| **P** | Pause / resume |
| **M** | Toggle mute |
| **ENTER** | Confirm / next stage / retry |
| **C** | Start campaign (menu or stage select) |
| **R** | Retry stage (results) / reset progress (stage select) |
| **ESC / Q** | Back / exit |

---

## Level System (Phases 13–21)

### Progression Flow

```
MENU → Stage Select → Play Stage
         ↓ score target reached (campaign)
       LEVEL UP screen (~3 sec)
         ↓
       Next stage (score carries over)
         ↓ all 8 stages cleared
       VICTORY screen
```

- **Arcade mode** (ENTER on stage select): single stage, score resets each run.
- **Campaign mode** (C on menu or stage select): chain stages with accumulating score and lives.

### 8 Stages

| # | Name | Mechanic | Boss |
|---|------|----------|------|
| 1 | City Streets | Tutorial pace, 3 lanes | — |
| 2 | Highway Rush | 4 lanes, trucks | — |
| 3 | Desert Storm | Sandstorm visibility | Giga Convoy |
| 4 | Mountain Pass | 2 lanes, falling boulders | — |
| 5 | Night City | Headlight cones | — |
| 6 | Rainy Highway | Slippery controls | Police Interceptor |
| 7 | Neon Race Track | Fast opponent weave traffic | — |
| 8 | Glacier Pass | Ice skidding | Blizzard Tank |

### Enemy Types (unlock by stage theme)

Sedan → Truck → Motorcycle → Boulder → Police Car → Bus

### Power-Ups (8 total, progressive unlock)

| Power-Up | Effect | Duration |
|----------|--------|----------|
| Shield | Blocks one hit | Until hit |
| Score Boost | 2× points | 8 sec |
| Slow-Mo | Enemies slow 50% | 5 sec |
| Nitro | Speed burst + invincible | 3 sec |
| Extra Life | +1 life (max 5) | Instant |
| Magnet | Pulls pickups toward you | 7 sec |
| Bomb | Clears all enemies | Instant |
| Ghost | Pass through enemies | 6 sec |

| Stage | New unlocks |
|-------|-------------|
| 1 | Score Boost |
| 2 | Shield |
| 3 | Slow-Mo, Ghost |
| 4 | Nitro |
| 5 | Extra Life |
| 6 | Magnet, Bomb |

### Save System

Progress is stored in `save.json`:

```json
{
  "unlocked_levels": [1, 2, 3],
  "high_scores": { "1": 980, "2": 750 }
}
```

Press **R** on the stage select screen to reset all progress.

---

## Features

- **LevelManager** + `levels.py` data config per stage
- Score-based progression (Option A) with Level Up transition screen
- Per-level modifiers: slippery physics, weather overlays, night headlights
- Parallax background scrolling
- Boss battles every 3rd stage with health bar and survival timer
- Star ratings (1–3) based on score vs target, animated reveal on completion
- Pixel-perfect mask collisions, screen shake, particles, procedural audio

---

## Folder Structure

```text
car_racing/
├── main.py              # Game engine, states, campaign flow
├── save.json            # Unlocked stages + per-stage high scores
├── game/
│   ├── levels.py        # LEVELS config + LevelManager
│   ├── road.py          # Road, parallax, weather FX
│   ├── player.py        # Player car + slippery physics
│   ├── enemy.py         # Enemy hierarchy + bosses
│   ├── powerup.py       # Power-up pickups
│   └── hud.py           # Scoreboard, boss bar, power-up timers
└── utils/
    ├── constants.py
    └── audio.py
```

---

## How to Run

```bash
pip install pygame
cd car_racing
python main.py
```

Requires **Python 3.8+**.

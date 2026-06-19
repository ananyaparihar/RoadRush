import pygame
import math
import random
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    LANE_WIDTH, COLOR_HUD_ACCENT, COLOR_WHITE
)

FPS = 60

POWERUP_DATA = {
    "shield": {
        "duration": -1,
        "duration_frames": -1,
        "color": (0, 180, 255),
        "icon": "SHD",
        "label": "SHIELD",
    },
    "score_boost": {
        "duration": 8,
        "duration_frames": 8 * FPS,
        "color": (255, 215, 0),
        "icon": "2X",
        "label": "SCORE BOOST",
    },
    "slowmo": {
        "duration": 5,
        "duration_frames": 5 * FPS,
        "color": (0, 255, 255),
        "icon": "SLO",
        "label": "SLOW-MO",
    },
    "nitro": {
        "duration": 3,
        "duration_frames": 3 * FPS,
        "color": (255, 140, 0),
        "icon": "NTR",
        "label": "NITRO",
    },
    "extra_life": {
        "duration": 0,
        "duration_frames": 0,
        "color": (255, 50, 80),
        "icon": "+1",
        "label": "EXTRA LIFE",
    },
    "magnet": {
        "duration": 7,
        "duration_frames": 7 * FPS,
        "color": (180, 80, 255),
        "icon": "MAG",
        "label": "MAGNET",
    },
    "bomb": {
        "duration": 0,
        "duration_frames": 0,
        "color": (40, 40, 50),
        "icon": "BOM",
        "label": "BOMB",
    },
    "ghost": {
        "duration": 6,
        "duration_frames": 6 * FPS,
        "color": (220, 220, 255),
        "icon": "GHO",
        "label": "GHOST",
    },
}

SPAWN_WEIGHTS = {
    "extra_life": 5,
    "bomb": 8,
    "nitro": 10,
    "ghost": 10,
    "shield": 15,
    "slowmo": 15,
    "magnet": 17,
    "score_boost": 20,
}

MAGNET_RADIUS = 150


class PowerUp:
    """Collectible power-up scrolling down the road."""

    def __init__(self, lane, road_left, lane_width, pu_type, road_speed=4.0):
        self.type = pu_type
        self.lane = lane
        self.size = 40
        data = POWERUP_DATA[pu_type]
        self.color = data["color"]
        self.icon = data["icon"]

        self.x = road_left + lane * lane_width + (lane_width - self.size) // 2
        self.y = -self.size - 20
        self.spawn_y = self.y
        self.angle = 0.0
        self.speed = road_speed
        self.magnetized = False

        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._render_icon(self.surface)
        self.rect = self.surface.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.surface)

    def _render_icon(self, surface):
        sz = self.size
        c = self.color
        cx, cy = sz // 2, sz // 2

        for r_thick in range(3, 0, -1):
            pygame.draw.circle(
                surface,
                (c[0] // r_thick, c[1] // r_thick, c[2] // r_thick),
                (cx, cy), sz // 2 - 2, r_thick,
            )

        if self.type == "shield":
            pygame.draw.polygon(surface, COLOR_WHITE, [
                (cx, cy - 9), (cx + 8, cy - 5), (cx + 6, cy + 5),
                (cx, cy + 9), (cx - 6, cy + 5), (cx - 8, cy - 5),
            ], 2)
        elif self.type == "score_boost":
            pygame.draw.polygon(surface, COLOR_WHITE, [
                (cx, cy - 9), (cx + 3, cy - 2), (cx + 9, cy - 2),
                (cx + 4, cy + 2), (cx + 6, cy + 9), (cx, cy + 5),
                (cx - 6, cy + 9), (cx - 4, cy + 2), (cx - 9, cy - 2), (cx - 3, cy - 2),
            ])
        elif self.type == "slowmo":
            pygame.draw.circle(surface, COLOR_WHITE, (cx, cy), 7, 2)
            pygame.draw.line(surface, COLOR_WHITE, (cx, cy), (cx, cy - 5), 2)
            pygame.draw.line(surface, COLOR_WHITE, (cx, cy), (cx + 4, cy + 2), 2)
        elif self.type == "nitro":
            pygame.draw.polygon(surface, COLOR_WHITE, [
                (cx, cy - 10), (cx + 7, cy + 2), (cx + 3, cy + 2),
                (cx + 5, cy + 10), (cx - 5, cy + 10), (cx - 3, cy + 2), (cx - 7, cy + 2),
            ])
        elif self.type == "extra_life":
            r = 4
            pygame.draw.circle(surface, COLOR_WHITE, (cx - r, cy - 1), r)
            pygame.draw.circle(surface, COLOR_WHITE, (cx + r, cy - 1), r)
            pygame.draw.polygon(surface, COLOR_WHITE, [
                (cx - 2 * r, cy), (cx + 2 * r, cy), (cx, cy + 8),
            ])
        elif self.type == "magnet":
            pygame.draw.arc(surface, COLOR_WHITE, (cx - 10, cy - 8, 20, 16), 0.4, 2.7, 3)
            pygame.draw.rect(surface, COLOR_WHITE, (cx - 4, cy + 4, 8, 6))
        elif self.type == "bomb":
            pygame.draw.circle(surface, COLOR_WHITE, (cx, cy + 2), 9, 2)
            pygame.draw.line(surface, COLOR_HUD_ACCENT, (cx + 5, cy - 8), (cx + 10, cy - 14), 2)
            pygame.draw.circle(surface, (255, 200, 0), (cx + 10, cy - 14), 3)
        elif self.type == "ghost":
            pygame.draw.ellipse(surface, COLOR_WHITE, (cx - 10, cy - 8, 20, 18), 2)
            pygame.draw.circle(surface, (30, 30, 40), (cx - 4, cy - 2), 2)
            pygame.draw.circle(surface, (30, 30, 40), (cx + 4, cy - 2), 2)

    def update(self, road_speed, player_center=None, magnet_active=False):
        if magnet_active and player_center and not self.magnetized:
            px, py = player_center
            dist = math.hypot(px - self.rect.centerx, py - self.rect.centery)
            if dist < MAGNET_RADIUS:
                self.magnetized = True

        if self.magnetized and player_center:
            px, py = player_center
            dx = px - self.rect.centerx
            dy = py - self.rect.centery
            dist = math.hypot(dx, dy) or 1.0
            pull = 9.0
            self.x += (dx / dist) * pull
            self.y += (dy / dist) * pull
            self.spawn_y = self.y
        else:
            self.spawn_y += road_speed
            bob = math.sin(pygame.time.get_ticks() * 0.006) * 5.0
            self.y = self.spawn_y + bob

        self.angle = (self.angle + 2.5) % 360
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface):
        rot_surf = pygame.transform.rotate(self.surface, self.angle)
        rot_rect = rot_surf.get_rect(center=self.rect.center)
        surface.blit(rot_surf, rot_rect)


class PowerUpManager:
    """Spawns, updates, and collects on-road power-ups."""

    def __init__(self):
        self.active_powerups = []
        self.spawn_timer = 0
        self.base_spawn_interval = 300

    def clear(self):
        self.active_powerups.clear()
        self.spawn_timer = 0

    def _occupied_lanes(self):
        occupied = set()
        for pu in self.active_powerups:
            if pu.y < SCREEN_HEIGHT * 0.75:
                occupied.add(pu.lane)
        return occupied

    def _is_type_active(self, pu_type, player):
        if pu_type == "shield":
            return player.shield_active
        if pu_type == "score_boost":
            return player.score_boost_active > 0
        if pu_type == "slowmo":
            return player.slow_mo_active > 0
        if pu_type == "nitro":
            return player.nitro_active > 0
        if pu_type == "magnet":
            return player.magnet_active > 0
        if pu_type == "ghost":
            return player.ghost_active > 0
        return False

    def _pick_type(self, pool, player):
        candidates = [t for t in pool if t in POWERUP_DATA and not self._is_type_active(t, player)]
        if not candidates:
            candidates = [t for t in pool if t in POWERUP_DATA]
        if not candidates:
            return None

        weights = [SPAWN_WEIGHTS.get(t, 10) for t in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    def spawn(self, road, powerup_pool, player):
        lanes = road.lanes_count
        occupied = self._occupied_lanes()
        free_lanes = [l for l in range(lanes) if l not in occupied]
        if not free_lanes:
            return

        pu_type = self._pick_type(powerup_pool, player)
        if not pu_type:
            return

        lane = random.choice(free_lanes)
        pu = PowerUp(lane, road.road_left, road.lane_width, pu_type, road.speed or 4.0)
        self.active_powerups.append(pu)

    def update(self, road_speed, road, level_idx, player, powerup_pool):
        interval = max(180, self.base_spawn_interval - level_idx * 20)
        self.spawn_timer += 1
        if self.spawn_timer >= interval:
            self.spawn_timer = 0
            self.spawn(road, powerup_pool, player)

        player_center = (player.rect.centerx, player.rect.centery)
        magnet_on = player.magnet_active > 0

        for pu in self.active_powerups[:]:
            pu.update(road_speed, player_center, magnet_on)
            if pu.y > SCREEN_HEIGHT + 50:
                self.active_powerups.remove(pu)

    def try_collect(self, player):
        """Return list of power-ups collected this frame."""
        collected = []
        for pu in self.active_powerups[:]:
            if player.rect.colliderect(pu.rect):
                collected.append(pu)
                self.active_powerups.remove(pu)
        return collected

    @staticmethod
    def apply_effect(pu_type, player, max_lives=5):
        """Apply collected power-up to player. Returns effect metadata for VFX."""
        data = POWERUP_DATA[pu_type]
        frames = data["duration_frames"]
        meta = {"type": pu_type, "label": data["label"], "color": data["color"]}

        if pu_type == "shield":
            player.shield_active = True
        elif pu_type == "score_boost":
            player.score_boost_active = frames
        elif pu_type == "slowmo":
            player.slow_mo_active = frames
        elif pu_type == "nitro":
            player.nitro_active = frames
            meta["shake"] = True
        elif pu_type == "extra_life":
            meta["extra_life"] = True
        elif pu_type == "magnet":
            player.magnet_active = frames
        elif pu_type == "bomb":
            meta["bomb"] = True
        elif pu_type == "ghost":
            player.ghost_active = frames
            meta["shake"] = False

        return meta

    def draw(self, surface):
        for pu in self.active_powerups:
            pu.draw(surface)

    @staticmethod
    def get_hud_status(player):
        """Return list of (icon, color, pct, flash) for active timed effects."""
        bars = []
        if player.shield_active:
            bars.append(("SHD", POWERUP_DATA["shield"]["color"], 1.0, False))
        timed = [
            ("2X", "score_boost", player.score_boost_active),
            ("SLO", "slowmo", player.slow_mo_active),
            ("NTR", "nitro", player.nitro_active),
            ("MAG", "magnet", player.magnet_active),
            ("GHO", "ghost", player.ghost_active),
        ]
        for icon, key, remaining in timed:
            if remaining <= 0:
                continue
            total = POWERUP_DATA[key]["duration_frames"]
            pct = remaining / total if total > 0 else 0
            flash = remaining < FPS
            bars.append((icon, POWERUP_DATA[key]["color"], pct, flash))
        return bars

import pygame
import random
import math
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BACKGROUND, COLOR_ROAD, COLOR_ROAD_BORDER, COLOR_LANE_MARKING, COLOR_WHITE
)

class Road:
    def __init__(self):
        # Current active layout (updated dynamically per level)
        self.lanes_count = 3
        self.road_width = 380
        self.road_left = (SCREEN_WIDTH - self.road_width) // 2
        self.road_right = self.road_left + self.road_width
        self.lane_width = self.road_width // self.lanes_count
        self.bg_style = "city"
        
        # Speed & markings
        self.speed = 0.0
        self.parallax_offset = 0.0
        self.dash_offset = 0.0
        self.dash_length = 40
        self.dash_gap = 30
        
        # Themed decorations (obstacles/scenery)
        self.decorations = []
        self.weather_particles = []
        
        # Initialize scenery elements
        self._reset_decorations()

    def set_level_layout(self, config):
        """Re-configures the road layout based on the active level configuration."""
        self.lanes_count = config.get("lanes", 3)
        self.bg_style = config.get("bg_style", "city")
        
        # Calculate road width and position
        if self.lanes_count == 2:
            self.road_width = 280
        elif self.lanes_count == 4:
            self.road_width = 460
        else: # 3
            self.road_width = 380
            
        self.road_left = (SCREEN_WIDTH - self.road_width) // 2
        self.road_right = self.road_left + self.road_width
        self.lane_width = self.road_width // self.lanes_count
        
        self._reset_decorations()
        self.weather_particles.clear()

    def _reset_decorations(self):
        self.decorations.clear()
        # Spawn initial decorations spread vertically
        for y in range(-100, SCREEN_HEIGHT + 200, 160):
            self._spawn_decor_pair(y)

    def _spawn_decor_pair(self, y_pos):
        # We spawn one decoration on the left grass, and one on the right
        left_limit = self.road_left - 40
        right_limit = self.road_right + 40
        
        # Style determines what kind of shape we store
        self.decorations.append({
            "x": left_limit, "y": y_pos, "side": "left", "size": random.randint(20, 35)
        })
        self.decorations.append({
            "x": right_limit, "y": y_pos, "side": "right", "size": random.randint(20, 35)
        })

    def update(self, speed, weather_type=None):
        self.speed = speed
        
        # Parallax background scrolls slower than road (Phase 17)
        self.parallax_offset += self.speed * 0.35
        if self.parallax_offset >= SCREEN_HEIGHT:
            self.parallax_offset %= SCREEN_HEIGHT
        
        # Scroll lane dashes
        self.dash_offset += self.speed
        if self.dash_offset >= (self.dash_length + self.dash_gap):
            self.dash_offset = self.dash_offset % (self.dash_length + self.dash_gap)
            
        # Scroll decorations
        for dec in self.decorations:
            dec["y"] += self.speed
            
        # Wrap decorations
        for dec in self.decorations:
            if dec["y"] > SCREEN_HEIGHT + 60:
                side_decs = [d for d in self.decorations if d["side"] == dec["side"]]
                min_y = min(d["y"] for d in side_decs)
                dec["y"] = min_y - 160
                dec["size"] = random.randint(20, 35)

        # Handle weather particles simulation
        self._update_weather(weather_type)

    def _update_weather(self, weather_type):
        if not weather_type:
            self.weather_particles.clear()
            return
            
        # Spawn new weather particles
        if weather_type == 'rain' and len(self.weather_particles) < 120:
            self.weather_particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(-40, 0),
                "vx": -3.0, # Wind blowing slightly left
                "vy": random.uniform(14, 20),
                "len": random.randint(15, 25)
            })
        elif weather_type == 'sandstorm' and len(self.weather_particles) < 100:
            self.weather_particles.append({
                "x": random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 50),
                "y": random.randint(0, SCREEN_HEIGHT),
                "vx": random.uniform(-15, -8), # Blown hard to the left
                "vy": random.uniform(1, 4),
                "len": random.randint(20, 40)
            })
        elif weather_type == 'snow' and len(self.weather_particles) < 80:
            self.weather_particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(-20, 0),
                "vx": random.uniform(-1.5, 0.5),
                "vy": random.uniform(3, 6),
                "size": random.randint(2, 5),
                "sway": random.uniform(0, 100) # For sinusoidal sway
            })
            
        # Update existing particles
        for p in self.weather_particles[:]:
            p["y"] += p["vy"]
            p["x"] += p.get("vx", 0)
            
            if weather_type == 'snow':
                # Add drift sway
                p["sway"] += 0.05
                p["x"] += math.sin(p["sway"]) * 0.5
                
            # Clean up off-screen
            if p["y"] > SCREEN_HEIGHT + 30 or p["x"] < -40 or p["x"] > SCREEN_WIDTH + 40:
                self.weather_particles.remove(p)

    def _draw_parallax_layer(self, surface, bg):
        """Distant scenery scrolling slower than the road for depth."""
        layer_colors = {
            "city": (18, 18, 28),
            "highway": (12, 14, 20),
            "desert": (52, 38, 24),
            "mountain": (16, 22, 30),
            "night": (8, 8, 14),
            "rain": (14, 16, 22),
            "race": (24, 16, 30),
            "ice": (28, 40, 55),
        }
        far_bg = layer_colors.get(self.bg_style, bg)
        surface.fill(far_bg)
        
        # Distant horizon silhouettes
        horizon_y = int(180 + math.sin(pygame.time.get_ticks() * 0.001) * 6)
        pygame.draw.rect(surface, tuple(max(0, c - 8) for c in far_bg), (0, horizon_y, SCREEN_WIDTH, SCREEN_HEIGHT - horizon_y))
        
        offset = int(self.parallax_offset)
        for band_y in range(-SCREEN_HEIGHT, SCREEN_HEIGHT * 2, 120):
            y = band_y - offset
            if self.bg_style in ("city", "night", "rain"):
                for bx in range(30, SCREEN_WIDTH, 90):
                    h = 60 + (bx % 50)
                    pygame.draw.rect(surface, (12, 14, 22), (bx, y, 40, h))
                    pygame.draw.rect(surface, (0, 80, 140), (bx, y, 40, h), 1)
            elif self.bg_style == "desert":
                for bx in range(20, SCREEN_WIDTH, 110):
                    pygame.draw.ellipse(surface, (45, 32, 20), (bx, y + 40, 80, 30))
            elif self.bg_style == "mountain":
                for bx in range(0, SCREEN_WIDTH, 100):
                    pygame.draw.polygon(surface, (14, 20, 28), [
                        (bx, y + 90), (bx + 50, y + 10), (bx + 100, y + 90)
                    ])
            elif self.bg_style == "ice":
                for bx in range(0, SCREEN_WIDTH, 120):
                    pygame.draw.polygon(surface, (20, 30, 42), [
                        (bx, y + 80), (bx + 60, y + 20), (bx + 120, y + 80)
                    ])

    def draw(self, surface):
        # 1. Background Grass/Sand/Night base color
        bg_colors = {
            "city": (12, 12, 18),
            "highway": (8, 8, 12),
            "desert": (38, 28, 18), # Dusty brown
            "mountain": (10, 14, 18), # Dark slate green
            "night": (5, 5, 8),
            "rain": (10, 12, 16),
            "race": (18, 12, 22),
            "ice": (22, 32, 45) # Snowy icy blue
        }
        bg = bg_colors.get(self.bg_style, (10, 10, 14))
        self._draw_parallax_layer(surface, bg)
        
        # 2. Main Asphalt Road
        road_rect = pygame.Rect(self.road_left, 0, self.road_width, SCREEN_HEIGHT)
        pygame.draw.rect(surface, COLOR_ROAD, road_rect)
        
        # 3. Dynamic road borders with glow
        for thickness in range(4, 1, -1):
            alpha_color = tuple(max(0, c - thickness * 35) for c in COLOR_ROAD_BORDER)
            pygame.draw.line(surface, alpha_color, (self.road_left, 0), (self.road_left, SCREEN_HEIGHT), thickness)
            pygame.draw.line(surface, alpha_color, (self.road_right, 0), (self.road_right, SCREEN_HEIGHT), thickness)
            
        pygame.draw.line(surface, COLOR_ROAD_BORDER, (self.road_left, 0), (self.road_left, SCREEN_HEIGHT), 2)
        pygame.draw.line(surface, COLOR_ROAD_BORDER, (self.road_right, 0), (self.road_right, SCREEN_HEIGHT), 2)

        # 4. Lanes markings
        for i in range(1, self.lanes_count):
            lane_x = self.road_left + i * self.lane_width
            y = -self.dash_length + self.dash_offset
            while y < SCREEN_HEIGHT + self.dash_length:
                pygame.draw.rect(surface, COLOR_LANE_MARKING, (lane_x - 2, y, 4, self.dash_length))
                y += self.dash_length + self.dash_gap

        # 5. Draw roadside scenery decorations (themed side objects)
        self._draw_decorations(surface)

    def _draw_decorations(self, surface):
        for dec in self.decorations:
            x, y, sz = dec["x"], dec["y"], dec["size"]
            
            if self.bg_style == "city" or self.bg_style == "night" or self.bg_style == "rain":
                # Draw neon skyscraper block silhouette
                rect_h = sz * 2.5
                rect_y = y - rect_h // 2
                
                # Draw building facade
                pygame.draw.rect(surface, (20, 20, 30), (x - sz // 2, rect_y, sz, rect_h), border_radius=2)
                # Neon outline
                pygame.draw.rect(surface, (0, 100, 180), (x - sz // 2, rect_y, sz, rect_h), 1, border_radius=2)
                
                # Lit windows inside building
                win_c = (0, 255, 255) if dec["side"] == "left" else (255, 0, 127)
                for wx in [x - sz // 3, x + sz // 6]:
                    for wy in range(int(rect_y + 10), int(rect_y + rect_h - 10), 18):
                        if (wy // 10) % 2 == 0:
                            pygame.draw.rect(surface, win_c, (wx, wy, 4, 4))
                            
            elif self.bg_style == "desert":
                # Draw neon cactus (polygon branches)
                # Trunk
                pygame.draw.rect(surface, (0, 180, 80), (x - 3, y - sz, 6, sz * 1.5), border_radius=2)
                # Left Arm
                pygame.draw.line(surface, (0, 180, 80), (x - 3, y - sz // 3), (x - sz // 2, y - sz // 3), 3)
                pygame.draw.line(surface, (0, 180, 80), (x - sz // 2, y - sz // 3), (x - sz // 2, y - 2 * sz // 3), 3)
                # Right Arm
                pygame.draw.line(surface, (0, 180, 80), (x + 3, y - 2 * sz // 3), (x + sz // 2, y - 2 * sz // 3), 3)
                pygame.draw.line(surface, (0, 180, 80), (x + sz // 2, y - 2 * sz // 3), (x + sz // 2, y - sz), 3)
                
            elif self.bg_style == "mountain" or self.bg_style == "ice":
                # Draw neon pine trees (triangles stacked)
                ty = y + sz
                tree_color = (130, 200, 255) if self.bg_style == "ice" else (0, 229, 255)
                # Base trunk
                pygame.draw.rect(surface, (70, 50, 40), (x - 3, ty, 6, 12))
                # Three tiers of leaves
                pygame.draw.polygon(surface, (15, 35, 30), [(x - sz, ty), (x + sz, ty), (x, ty - sz)])
                pygame.draw.polygon(surface, tree_color, [(x - sz, ty), (x + sz, ty), (x, ty - sz)], 1)
                
                ty -= sz // 2
                pygame.draw.polygon(surface, (15, 35, 30), [(x - sz*0.8, ty), (x + sz*0.8, ty), (x, ty - sz*0.8)])
                pygame.draw.polygon(surface, tree_color, [(x - sz*0.8, ty), (x + sz*0.8, ty), (x, ty - sz*0.8)], 1)
                
            else: # highway / race barriers
                # Draw metallic barrier posts with flashing lights
                pygame.draw.line(surface, (80, 80, 90), (x, y - 10), (x, y + 15), 3)
                pygame.draw.rect(surface, (100, 100, 110), (x - 6, y - 16, 12, 8), border_radius=1)
                
                # Flashing warning light
                flash = (pygame.time.get_ticks() // 200) % 2
                if flash == 0:
                    l_color = (255, 0, 127) if dec["side"] == "left" else (255, 215, 0)
                    pygame.draw.circle(surface, l_color, (x, y - 12), 4)

    def draw_weather_overlay(self, surface):
        """Renders overlay rain drops, snow, or sand dust blowing over the viewport."""
        for p in self.weather_particles:
            if "len" in p: # Rain or Sandstorm streaks
                # Decide color: rain is blue/white, sand is orange
                color = (180, 220, 255, 120) if p["vx"] == -3.0 else (255, 170, 70, 80)
                # Create surface for alpha line
                ls = pygame.Surface((abs(int(p["vx"])) + 1, int(p["vy"])), pygame.SRCALPHA)
                pygame.draw.line(ls, color, (0, 0), (int(p["vx"]), int(p["vy"])), 1)
                surface.blit(ls, (p["x"], p["y"]))
            else: # Snow particles
                pygame.draw.circle(surface, (255, 255, 255, 180), (int(p["x"]), int(p["y"])), p["size"])

    def draw_night_light_overlay(self, surface, player, enemies):
        """Creates transparent cones centered around the headlights of the player & enemies."""
        light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        light_mask.fill((6, 6, 15, 235)) # Very dark indigo opacity
        
        # 1. Player Headlight Cone (Tall glowing V shape pointing up)
        px = player.rect.centerx
        py = player.rect.top
        
        # Clear main headlight beam
        pygame.draw.circle(light_mask, (0, 0, 0, 0), (px, py - 30), 80)
        pygame.draw.polygon(light_mask, (0, 0, 0, 0), [
            (px, py),
            (px - 150, py - 350),
            (px + 150, py - 350)
        ])
        
        # Soft transparency halo boundary
        glow_cone = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(glow_cone, (255, 255, 200, 30), [
            (px, py),
            (px - 165, py - 370),
            (px + 165, py - 370)
        ])
        pygame.draw.circle(glow_cone, (255, 255, 255, 50), (px, py - 30), 90)
        
        # 2. Enemies Headlight Cones (Shorter V shape pointing down)
        for enemy in enemies:
            ex = enemy.rect.centerx
            ey = enemy.rect.bottom
            # Clear headlights
            pygame.draw.circle(light_mask, (0, 0, 0, 0), (ex, ey + 20), 55)
            pygame.draw.polygon(light_mask, (0, 0, 0, 0), [
                (ex, ey),
                (ex - 60, ey + 180),
                (ex + 60, ey + 180)
            ])
            # Glow
            pygame.draw.polygon(glow_cone, (255, 255, 255, 25), [
                (ex, ey),
                (ex - 70, ey + 195),
                (ex + 70, ey + 195)
            ])
            pygame.draw.circle(glow_cone, (255, 255, 255, 40), (ex, ey + 20), 65)

        # Blit clear cut mask
        surface.blit(light_mask, (0, 0))
        # Overlay soft glows
        surface.blit(glow_cone, (0, 0))

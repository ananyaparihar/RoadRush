import pygame
import math
import random
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CAR_WIDTH, CAR_HEIGHT, ROAD_LEFT, ROAD_RIGHT,
    LANE_WIDTH, LANE_COUNT, COLOR_HUD_ACCENT, COLOR_WHITE
)

# Base Enemy Class
class Enemy:
    def __init__(self, lane, road_speed):
        self.lane = lane
        self.width = CAR_WIDTH
        self.height = CAR_HEIGHT
        self.x = ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - self.width) // 2
        self.y = -self.height - 20
        self.vx = 0.0
        self.vy = 0.0
        self.relative_speed = 2.0
        self.color = (0, 255, 128) # Default mint green
        self.is_projectile = False
        
        # Collision properties
        self.surface = None
        self.rect = None
        self.mask = None

    def setup_graphics(self):
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.render_sprite(self.surface)
        self.rect = self.surface.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.surface)

    def render_sprite(self, surface):
        # Default placeholder, overridden by subclasses
        pygame.draw.rect(surface, self.color, (0, 0, self.width, self.height), 2)

    def update(self, road_speed, player_x=None):
        # Move down screen based on road speed relative difference
        screen_speed = max(2.0, road_speed - self.relative_speed)
        self.y += screen_speed
        self.x += self.vx
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface):
        if self.surface:
            surface.blit(self.surface, self.rect)


# Subclasses for Enemy Types

class Sedan(Enemy):
    def __init__(self, lane, road_speed):
        super().__init__(lane, road_speed)
        self.relative_speed = 1.8
        self.color = (0, 255, 128) # Mint green
        self.setup_graphics()

    def render_sprite(self, surface):
        w, h = self.width, self.height
        c = self.color
        # Body
        pygame.draw.polygon(surface, (15, 20, 15), [(4, 4), (w-4, 4), (w-2, h-6), (2, h-6)])
        for thickness in range(3, 0, -1):
            pygame.draw.polygon(surface, (c[0]//thickness, c[1]//thickness, c[2]//thickness), [(4, 4), (w-4, 4), (w-2, h-6), (2, h-6)], thickness)
        # Windshields
        pygame.draw.rect(surface, (10, 30, 20), (8, 20, w - 16, 10), border_radius=2)
        pygame.draw.rect(surface, (10, 30, 20), (8, h - 32, w - 16, 8), border_radius=2)
        pygame.draw.rect(surface, c, (8, 20, w - 16, 10), 1)
        pygame.draw.rect(surface, c, (8, h - 32, w - 16, 8), 1)
        # Headlights
        pygame.draw.circle(surface, (255, 255, 180), (8, 6), 3)
        pygame.draw.circle(surface, (255, 255, 180), (w-8, 6), 3)


class Truck(Enemy):
    def __init__(self, lane, road_speed):
        super().__init__(lane, road_speed)
        # Spans across almost 2 lanes! Centered between lane and lane + 1
        # If lane is 2 (rightmost), shift left so it stays on road
        if lane == LANE_COUNT - 1 or (LANE_COUNT == 4 and lane == 3):
            self.lane = lane - 1
            
        self.width = int(LANE_WIDTH * 1.5)
        self.height = CAR_HEIGHT + 30
        
        # Center between lane and next lane
        self.x = ROAD_LEFT + self.lane * LANE_WIDTH + LANE_WIDTH - self.width // 2
        self.relative_speed = -0.5 # Slow truck, falls backward fast!
        self.color = (255, 128, 0) # Orange
        self.setup_graphics()

    def render_sprite(self, surface):
        w, h = self.width, self.height
        c = self.color
        # Cab & trailer divider
        pygame.draw.rect(surface, (20, 20, 25), (4, 4, w-8, h-8), border_radius=4)
        for thickness in range(3, 0, -1):
            pygame.draw.rect(surface, (c[0]//thickness, c[1]//thickness, c[2]//thickness), (4, 4, w-8, h-8), thickness, border_radius=4)
        # Windshield
        pygame.draw.rect(surface, (10, 40, 50), (10, 22, w - 20, 14))
        pygame.draw.rect(surface, (0, 255, 255), (10, 22, w - 20, 14), 1)
        # Metal cargo ribs
        for y_line in range(45, h - 15, 18):
            pygame.draw.line(surface, (70, 70, 80), (10, y_line), (w - 10, y_line), 3)
        # Hazard flashing amber lights on top
        pygame.draw.circle(surface, (255, 200, 0), (12, 10), 4)
        pygame.draw.circle(surface, (255, 200, 0), (w - 12, 10), 4)


class Motorcycle(Enemy):
    def __init__(self, lane, road_speed):
        super().__init__(lane, road_speed)
        self.width = 24
        self.height = 64
        self.x = ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - self.width) // 2
        self.relative_speed = 3.5 # Fast bike, falls backward very slowly
        self.color = (255, 0, 127) # Hot Magenta
        self.oscillation_timer = random.uniform(0, 100)
        self.setup_graphics()

    def render_sprite(self, surface):
        w, h = self.width, self.height
        c = self.color
        # Sleek bike chassis
        pygame.draw.ellipse(surface, (15, 15, 20), (2, 8, w - 4, h - 16))
        for thickness in range(3, 0, -1):
            pygame.draw.ellipse(surface, (c[0]//thickness, c[1]//thickness, c[2]//thickness), (2, 8, w - 4, h - 16), thickness)
        # Front wheel tire
        pygame.draw.rect(surface, (0, 0, 0), (w//2 - 2, 2, 4, 10), border_radius=1)
        # Rider helmet
        pygame.draw.circle(surface, (0, 255, 255), (w//2, h//2 - 4), 5)
        pygame.draw.circle(surface, (255, 255, 255), (w//2, h//2 - 6), 2) # specular reflection

    def update(self, road_speed, player_x=None):
        super().update(road_speed, player_x)
        # Custom movement pattern: weave left and right in lane
        self.oscillation_timer += 0.05
        # Weave horizontally within the width of the lane (max deflection 25 pixels)
        self.vx = math.sin(self.oscillation_timer) * 1.5
        self.x += self.vx
        
        # Clamp to road borders
        self.x = max(ROAD_LEFT + 10, min(ROAD_RIGHT - self.width - 10, self.x))
        self.rect.x = int(self.x)


class Boulder(Enemy):
    def __init__(self, lane, road_speed):
        super().__init__(lane, road_speed)
        self.width = 44
        self.height = 44
        self.x = ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - self.width) // 2
        self.relative_speed = -1.0 # Heavy, rolling down fast
        self.color = (180, 180, 190) # Granite gray
        
        # Oscillation properties for rolling trajectory
        self.roll_speed = random.uniform(1.5, 3.2)
        self.roll_dir = random.choice([-1, 1])
        self.angle = 0.0
        self.setup_graphics()

    def render_sprite(self, surface):
        w, h = self.width, self.height
        c = self.color
        # Draw a jagged boulder shape
        points = [
            (w//2, 2),
            (w-4, h//4),
            (w-2, 3*h//4),
            (w//2, h-2),
            (4, 3*h//4),
            (2, h//4)
        ]
        pygame.draw.polygon(surface, (30, 25, 25), points)
        for thickness in range(3, 0, -1):
            pygame.draw.polygon(surface, (c[0]//thickness, c[1]//thickness, c[2]//thickness), points, thickness)
        
        # Draw cracks
        pygame.draw.line(surface, (100, 100, 110), (w//2, h//2), (w-10, h//4 + 5), 2)
        pygame.draw.line(surface, (100, 100, 110), (w//2, h//2), (8, 3*h//4 - 5), 2)

    def update(self, road_speed, player_x=None):
        # Bounce off the margins of the road
        self.y += max(2.5, road_speed - self.relative_speed)
        self.x += self.roll_dir * self.roll_speed
        self.angle += 3.0
        
        min_x = ROAD_LEFT + 5
        max_x = ROAD_RIGHT - self.width - 5
        if self.x <= min_x:
            self.x = min_x
            self.roll_dir = 1
        elif self.x >= max_x:
            self.x = max_x
            self.roll_dir = -1
            
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface):
        # Rotate boulder dynamically
        rot_surf = pygame.transform.rotate(self.surface, self.angle)
        rot_rect = rot_surf.get_rect(center=(self.rect.x + self.width // 2, self.rect.y + self.height // 2))
        surface.blit(rot_surf, rot_rect)


class PoliceCar(Enemy):
    def __init__(self, lane, road_speed):
        super().__init__(lane, road_speed)
        self.relative_speed = 2.5
        self.color = (0, 102, 255) # Deep Police Blue
        self.setup_graphics()

    def render_sprite(self, surface):
        w, h = self.width, self.height
        c = self.color
        # Black and white cruiser panels
        pygame.draw.rect(surface, (10, 10, 15), (0, 0, w, h), border_radius=3)
        # White doors
        pygame.draw.rect(surface, (230, 230, 240), (0, 25, 4, h - 50))
        pygame.draw.rect(surface, (230, 230, 240), (w - 4, 25, 4, h - 50))
        # Blue borders
        for thickness in range(2, 0, -1):
            pygame.draw.rect(surface, (0, 102, 255), (0, 0, w, h), thickness, border_radius=3)
        # Cockpit windshields
        pygame.draw.rect(surface, (20, 25, 30), (6, 18, w - 12, 10), border_radius=1)
        pygame.draw.rect(surface, (20, 25, 30), (6, h - 30, w - 12, 8), border_radius=1)
        pygame.draw.rect(surface, (0, 255, 255), (6, 18, w - 12, 10), 1)
        # Sirens (red/blue bar in the center)
        pygame.draw.rect(surface, (50, 50, 60), (w//2 - 12, h//2 - 4, 24, 6))

    def update(self, road_speed, player_x=None):
        super().update(road_speed, player_x)
        # Active AI: tracking player's X coordinate!
        if player_x is not None:
            diff_x = player_x - (self.x + self.width // 2)
            # Slowly nudge towards player horizontally
            self.vx = diff_x * 0.025
            self.x += self.vx
            self.rect.x = int(self.x)

    def draw(self, surface):
        super().draw(surface)
        
        # Draw flashing siren halo above police car
        flash = (pygame.time.get_ticks() // 150) % 2
        siren_color = (255, 0, 50) if flash == 0 else (0, 102, 255)
        
        siren_x = self.rect.centerx
        siren_y = self.rect.centery
        
        # Draw translucent siren light cones
        s_surf = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(s_surf, (*siren_color, 80), (0, 0, 40, 20))
        surface.blit(s_surf, (siren_x - 20, siren_y - 10))


class Bus(Enemy):
    def __init__(self, lane, road_speed):
        super().__init__(lane, road_speed)
        self.width = CAR_WIDTH + 14
        self.height = CAR_HEIGHT + 36
        self.relative_speed = -0.2 # Falls backward fast
        self.color = (255, 200, 0) # Gold Yellow Bus
        self.setup_graphics()

    def render_sprite(self, surface):
        w, h = self.width, self.height
        c = self.color
        # Main bus body
        pygame.draw.rect(surface, (20, 20, 22), (2, 2, w - 4, h - 4), border_radius=5)
        for thickness in range(3, 0, -1):
            pygame.draw.rect(surface, (c[0]//thickness, c[1]//thickness, c[2]//thickness), (2, 2, w - 4, h - 4), thickness, border_radius=5)
        # Grid of windows
        for row in range(5):
            wy = 22 + row * 18
            pygame.draw.rect(surface, (40, 40, 50), (8, wy, 10, 10), border_radius=1)
            pygame.draw.rect(surface, (40, 40, 50), (w - 18, wy, 10, 10), border_radius=1)
            pygame.draw.rect(surface, (0, 255, 255), (8, wy, 10, 10), 1)
            pygame.draw.rect(surface, (0, 255, 255), (w - 18, wy, 10, 10), 1)
        # Front windshield
        pygame.draw.rect(surface, (10, 30, 40), (8, 6, w - 16, 10), border_radius=2)
        pygame.draw.rect(surface, (0, 255, 255), (8, 6, w - 16, 10), 1)


class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.spawn_timer = 0

    def update(self, road_speed, level_config, player_x=None):
        # 1. Update all active hazards
        for enemy in self.enemies[:]:
            # Pass player x-coordinate so that tracking police cars can steer
            enemy.update(road_speed, player_x)
            
            # Clean up off-screen entities
            if enemy.y > SCREEN_HEIGHT + 60 or enemy.x < ROAD_LEFT - 100 or enemy.x > ROAD_RIGHT + 100:
                self.enemies.remove(enemy)

        # Check spawn timers
        self.spawn_timer += 1
        cooldown = level_config.get("spawn_rate", 100)
        
        if self.spawn_timer >= cooldown:
            self.spawn_timer = 0
            self.spawn_enemy(road_speed, level_config)

    def spawn_enemy(self, road_speed, level_config):
        lanes = level_config.get("lanes", 3)
        bg_style = level_config.get("bg_style", "city")
        
        # Calculate road limits locally based on lane counts
        if lanes == 2:
            r_width = 280
        elif lanes == 4:
            r_width = 460
        else:
            r_width = 380
            
        r_left = (SCREEN_WIDTH - r_width) // 2
        r_lane_w = r_width // lanes

        # Find which lanes are currently free at the spawning point
        available_lanes = list(range(lanes))
        for enemy in self.enemies:
            if enemy.y < 160 and enemy.lane in available_lanes:
                available_lanes.remove(enemy.lane)
                
        if not available_lanes:
            return

        # Limit spawn density: don't spawn in all lanes at once to guarantee escape path
        max_simultaneous = 1 if lanes <= 2 else (2 if lanes == 3 else 3)
        num_spawns = random.randint(1, min(len(available_lanes), max_simultaneous))
        if num_spawns >= lanes:
            num_spawns = lanes - 1
            
        lanes_to_spawn = random.sample(available_lanes, num_spawns)
        
        # Pick enemy type pool based on level theme (Phase 16)
        pool = ['sedan']
        if bg_style == 'highway':
            pool = ['sedan', 'truck']
        elif bg_style == 'desert':
            pool = ['sedan', 'motorcycle']
        elif bg_style == 'mountain':
            pool = ['boulder', 'sedan']
        elif bg_style == 'night':
            pool = ['sedan', 'police']
        elif bg_style == 'race':
            pool = ['sedan', 'truck', 'motorcycle', 'bus']
        elif bg_style == 'rain':
            pool = ['sedan', 'truck', 'motorcycle', 'bus']
        elif bg_style == 'ice':
            pool = ['sedan', 'truck', 'motorcycle']

        for lane in lanes_to_spawn:
            enemy_type = random.choice(pool)
            
            # Instantiate corresponding subclass
            if enemy_type == 'sedan':
                self.enemies.append(Sedan(lane, road_speed))
            elif enemy_type == 'truck':
                self.enemies.append(Truck(lane, road_speed))
            elif enemy_type == 'motorcycle':
                self.enemies.append(Motorcycle(lane, road_speed))
            elif enemy_type == 'boulder':
                self.enemies.append(Boulder(lane, road_speed))
            elif enemy_type == 'police':
                self.enemies.append(PoliceCar(lane, road_speed))
            elif enemy_type == 'bus':
                self.enemies.append(Bus(lane, road_speed))

    def draw(self, surface):
        for enemy in self.enemies:
            enemy.draw(surface)

    def clear(self):
        self.enemies.clear()
        self.spawn_timer = 0


import pygame
import math
import random
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_SPEED, PLAYER_ACCEL, PLAYER_DECEL, PLAYER_MAX_TILT,
    CAR_WIDTH, CAR_HEIGHT, ROAD_LEFT, ROAD_RIGHT
)

class Player:
    def __init__(self):
        # Position
        self.x = (SCREEN_WIDTH - CAR_WIDTH) // 2
        self.y = SCREEN_HEIGHT - CAR_HEIGHT - 80
        
        # Physics
        self.vx = 0.0
        self.tilt_angle = 0.0
        self.target_tilt = 0.0
        
        # Power-ups status
        self.shield_active = False
        self.nitro_active = 0
        self.slow_mo_active = 0
        self.score_boost_active = 0
        self.magnet_active = 0
        self.ghost_active = 0
        self.ghost_particles = []
        
        # Procedural base sprite creation
        self.base_surface = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
        self._render_neon_car(self.base_surface)
        
        # Active surface & mask for collisions
        self.surface = self.base_surface.copy()
        self.rect = self.surface.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.surface)
        
        # Particles
        self.exhaust_particles = []

    def _render_neon_car(self, surface):
        """Draws a sleek, futuristic neon-blue cyber-car on the surface."""
        w, h = CAR_WIDTH, CAR_HEIGHT
        
        # Wheels (dark grey with neon hubs)
        wheel_w, wheel_h = 8, 18
        wheel_coords = [
            (2, 10), (w - 2 - wheel_w, 10),
            (2, h - 28), (w - 2 - wheel_w, h - 28)
        ]
        for wx, wy in wheel_coords:
            pygame.draw.rect(surface, (20, 20, 25), (wx, wy, wheel_w, wheel_h), border_radius=3)
            pygame.draw.rect(surface, (0, 180, 255), (wx + 2, wy + 4, wheel_w - 4, wheel_h - 8))
            
        # Main Body (Dark carbon center, glowing borders)
        body_points = [
            (w // 2, 2), (w - 6, 18), (w - 6, h - 18), (w - 2, h - 12),
            (w - 10, h - 4), (10, h - 4), (2, h - 12), (6, h - 18), (6, 18),
        ]
        pygame.draw.polygon(surface, (15, 20, 30), body_points)
        
        for thickness in range(3, 0, -1):
            color = (0, 200 // thickness, 255)
            pygame.draw.polygon(surface, color, body_points, thickness)

        # Cockpit
        cockpit_points = [
            (w // 2, 30), (w - 12, 48), (w - 12, h - 35), (12, h - 35), (12, 48),
        ]
        pygame.draw.polygon(surface, (5, 40, 60), cockpit_points)
        pygame.draw.polygon(surface, (0, 255, 255), cockpit_points, 1)
        pygame.draw.line(surface, (255, 255, 255, 180), (w // 2, 33), (16, 46), 1)

        # Details
        pygame.draw.rect(surface, (0, 100, 150), (w // 2 - 6, h - 30, 12, 8), border_radius=2)
        pygame.draw.rect(surface, (0, 255, 255), (w // 2 - 6, h - 30, 12, 8), 1)

        # Headlights
        pygame.draw.polygon(surface, (255, 255, 150), [(8, 14), (12, 12), (10, 8)])
        pygame.draw.polygon(surface, (255, 255, 150), [(w - 8, 14), (w - 12, 12), (w - 10, 8)])

        # Taillights
        pygame.draw.line(surface, (255, 0, 50), (12, h - 5), (18, h - 5), 2)
        pygame.draw.line(surface, (255, 0, 50), (w - 12, h - 5), (w - 18, h - 5), 2)

    def handle_input(self, slippery=False):
        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        
        # Modify physics based on slippery state (Drift mode)
        accel = PLAYER_ACCEL * 0.35 if slippery else PLAYER_ACCEL
        decel = PLAYER_DECEL * 0.15 if slippery else PLAYER_DECEL
        max_speed = PLAYER_SPEED * 1.35 if self.nitro_active > 0 else PLAYER_SPEED
        
        if move_left and not move_right:
            self.vx -= accel
            if self.vx < -max_speed:
                self.vx = -max_speed
            self.target_tilt = PLAYER_MAX_TILT
        elif move_right and not move_left:
            self.vx += accel
            if self.vx > max_speed:
                self.vx = max_speed
            self.target_tilt = -PLAYER_MAX_TILT
        else:
            # Slower friction deceleration under slippery ice/rain road conditions
            if self.vx > 0:
                self.vx -= decel
                if self.vx < 0:
                    self.vx = 0.0
            elif self.vx < 0:
                self.vx += decel
                if self.vx > 0:
                    self.vx = 0.0
            self.target_tilt = 0.0

    def update(self, road_left, road_right, slippery=False):
        # 1. Update powerup timers
        if self.nitro_active > 0:
            self.nitro_active -= 1
        if self.slow_mo_active > 0:
            self.slow_mo_active -= 1
        if self.score_boost_active > 0:
            self.score_boost_active -= 1
        if self.magnet_active > 0:
            self.magnet_active -= 1
        if self.ghost_active > 0:
            self.ghost_active -= 1
            if random.random() < 0.4:
                self.ghost_particles.append({
                    "x": self.rect.centerx + random.uniform(-12, 12),
                    "y": self.rect.centery + random.uniform(-8, 8),
                    "life": random.randint(12, 22),
                    "size": random.randint(2, 4),
                })
        for gp in self.ghost_particles[:]:
            gp["y"] -= 1.5
            gp["life"] -= 1
            if gp["life"] <= 0:
                self.ghost_particles.remove(gp)
            
        # 2. Update position
        self.x += self.vx
        
        # 3. Clamp player to road boundaries (dynamic boundaries based on road_left/road_right)
        min_x = road_left + 8
        max_x = road_right - CAR_WIDTH - 8
        if self.x < min_x:
            self.x = min_x
            self.vx = 0.0
        elif self.x > max_x:
            self.x = max_x
            self.vx = 0.0
            
        # 4. Update tilt animation (lerp tilt_angle to target_tilt)
        self.tilt_angle += (self.target_tilt - self.tilt_angle) * 0.12
        
        # 5. Rotate base surface & update rect/mask
        if abs(self.tilt_angle) > 0.1:
            self.surface = pygame.transform.rotate(self.base_surface, self.tilt_angle)
            new_rect = self.surface.get_rect()
            new_rect.center = (self.x + CAR_WIDTH // 2, self.y + CAR_HEIGHT // 2)
            self.rect = new_rect
        else:
            self.surface = self.base_surface
            self.rect = self.surface.get_rect(topleft=(self.x, self.y))
            
        self.mask = pygame.mask.from_surface(self.surface)
        
        # 6. Emit exhaust / thruster particles
        lx = self.x + 15
        ly = self.y + CAR_HEIGHT - 5
        rx = self.x + CAR_WIDTH - 15
        ry = self.y + CAR_HEIGHT - 5
        
        # If nitro is active, emit bigger, glowing, faster exhaust particles!
        is_nitro = self.nitro_active > 0
        emit_chance = 0.95 if is_nitro else 0.6
        
        if random.random() < emit_chance:
            for ex, ey in [(lx, ly), (rx, ry)]:
                if is_nitro:
                    # Fire flame colors (Magenta/Pink/Yellow)
                    p_color = random.choice([(255, 0, 127), (255, 150, 0), (255, 255, 255)])
                    vy = random.uniform(8, 14)
                    size = random.randint(4, 8)
                    life = random.randint(15, 25)
                else:
                    p_color = random.choice([(0, 180, 255), (0, 255, 255), (255, 255, 255)])
                    vy = random.uniform(3, 6)
                    size = random.randint(2, 5)
                    life = random.randint(10, 20)
                    
                self.exhaust_particles.append({
                    "x": ex + random.uniform(-2, 2),
                    "y": ey,
                    "vx": random.uniform(-0.6, 0.6) - (self.vx * 0.12),
                    "vy": vy,
                    "color": p_color,
                    "life": life,
                    "size": size
                })
                
        # Update exhaust particles
        for p in self.exhaust_particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self.exhaust_particles.remove(p)

    def is_invincible(self):
        return self.nitro_active > 0

    def draw(self, surface):
        # Ghost trail particles
        for gp in self.ghost_particles:
            alpha = int((gp["life"] / 22.0) * 180)
            gp_surf = pygame.Surface((gp["size"] * 2, gp["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(gp_surf, (255, 255, 255, alpha), (gp["size"], gp["size"]), gp["size"])
            surface.blit(gp_surf, (gp["x"] - gp["size"], gp["y"] - gp["size"]))

        # Draw exhaust particles
        for p in self.exhaust_particles:
            alpha = int((p["life"] / 25.0) * 255)
            alpha = max(0, min(255, alpha))
            p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p["color"], alpha), (p["size"], p["size"]), p["size"])
            surface.blit(p_surf, (p["x"] - p["size"], p["y"] - p["size"]))
            
        # Magnet arc lines
        if self.magnet_active > 0:
            ticks = pygame.time.get_ticks()
            pulse = int(100 + 80 * math.sin(ticks * 0.02))
            for arc_i in range(3):
                arc_surf = pygame.Surface((120, 60), pygame.SRCALPHA)
                pygame.draw.arc(
                    arc_surf, (180, 80, 255, pulse),
                    (10 + arc_i * 8, 5, 100 - arc_i * 16, 50), 0.5, 2.6, 2,
                )
                surface.blit(arc_surf, (self.rect.centerx - 60, self.rect.centery - 50))

        # Draw car sprite (ghost = semi-transparent, flicker when expiring)
        car_surf = self.surface
        if self.ghost_active > 0:
            car_surf = self.surface.copy()
            alpha = 128
            if self.ghost_active < 60 and (self.ghost_active // 8) % 2 == 0:
                alpha = 80
            car_surf.set_alpha(alpha)
        surface.blit(car_surf, self.rect)
        
        # Draw active Shield barrier glow
        if self.shield_active:
            # Pulsing size & transparency
            ticks = pygame.time.get_ticks()
            pulse_rad = int(CAR_HEIGHT // 2 + 8 + 3 * math.sin(ticks * 0.015))
            pulse_alpha = int(120 + 80 * math.sin(ticks * 0.015))
            
            shield_surf = pygame.Surface((pulse_rad * 2, pulse_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0, 255, 255, pulse_alpha // 3), (pulse_rad, pulse_rad), pulse_rad)
            pygame.draw.circle(shield_surf, (0, 255, 255, pulse_alpha), (pulse_rad, pulse_rad), pulse_rad, 2)
            
            # Sub-mesh detailing lines
            pygame.draw.circle(shield_surf, (255, 255, 255, pulse_alpha // 2), (pulse_rad, pulse_rad), pulse_rad - 4, 1)
            
            surface.blit(shield_surf, (self.rect.centerx - pulse_rad, self.rect.centery - pulse_rad))

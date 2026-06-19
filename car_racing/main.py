import pygame
import sys
import os
import random
import math

# Add current dir to path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    CAR_WIDTH, CAR_HEIGHT,
    COLOR_BACKGROUND, COLOR_HUD_TEXT, COLOR_HUD_ACCENT, COLOR_WHITE, COLOR_BLACK
)
from utils.audio import AudioSystem
from game.levels import LEVELS, LevelManager
from game.road import Road
from game.player import Player
from game.powerup import PowerUpManager
from game.enemy import (
    EnemyManager, Sedan, Truck, Motorcycle, Boulder, PoliceCar, Bus
)
from game.hud import HUD


# --- Core Game Coordinator ---

class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("NEON RACER")
        
        # Draw window icon
        try:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.polygon(icon, (0, 255, 255), [(16, 2), (30, 24), (24, 30), (8, 30), (2, 24)])
            pygame.draw.circle(icon, (255, 0, 127), (16, 18), 6)
            pygame.display.set_icon(icon)
        except Exception:
            pass
            
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Audio & Level configs
        self.audio = None
        class DummyAudio:
             def __getattr__(self, name):
                  return lambda *args, **kwargs: None
        self.audio = DummyAudio()
        self.level_manager = LevelManager()
        
        # Core modules
        self.road = Road()
        self.player = Player()
        self.enemy_manager = EnemyManager()
        self.hud = HUD()
        
        # Game States: 'MENU', 'LEVEL_SELECT', 'COUNTDOWN', 'PLAYING', 'PAUSED',
        # 'LEVEL_UP', 'LEVEL_COMPLETE', 'GAME_OVER', 'VICTORY'
        self.state = 'MENU'
        self.selected_menu_lvl = 1
        self.campaign_mode = False
        
        # Scoring & Lives
        self.score = 0.0
        self.lives = 3
        self.max_lives = 5
        self.road_speed = 6.0
        
        # Level Stats tracking
        self.level_start_ticks = 0
        self.level_time_taken = 0.0
        self.enemies_dodged = 0
        self.distance_traveled = 0.0
        self.powerups_collected = 0
        
        # Power-ups
        self.powerup_manager = PowerUpManager()
        self.floating_texts = []
        self.screen_flash_timer = 0
        
        self.flash_level_name_timer = 0
        self.level_up_screen_timer = 0
        self.level_stars_earned = 0
        self.star_reveal_timer = 0
        self.next_level_idx = None
        self.has_unlocked_next = False
        
        # Visual FX lists
        self.particles = []
        self.speed_lines = []
        self.screenshake_timer = 0
        self.screenshake_intensity = 0
        
        # Countdown timing
        self.countdown_frames = 180
        self.last_countdown_sec = 4

    def start_level(self, level_idx, campaign=None, keep_score=False):
        """Loads a specific level layout and resets game loop physics."""
        if campaign is not None:
            self.campaign_mode = campaign
        self.level_manager.current_level_idx = level_idx
        config = self.level_manager.get_current_level_config()
        
        # Configure road layout and speed
        self.road.set_level_layout(config)
        self.road_speed = config["base_speed"]
        
        # Reset scoring and stats (keep score in campaign transitions — Phase 14)
        if not keep_score:
            self.score = 0.0
            self.lives = 3
            self.enemies_dodged = 0
            self.distance_traveled = 0.0
            self.powerups_collected = 0
        else:
            self.enemy_manager.clear()
            self.powerup_manager.clear()
        self.level_start_ticks = pygame.time.get_ticks()
        
        # Reset entity managers
        self.player = Player()
        self.enemy_manager.clear()
        self.powerup_manager.clear()
        self.floating_texts.clear()
        self.screen_flash_timer = 0
        self.particles.clear()
        self.speed_lines.clear()
        
        # Screens & timers
        self.countdown_frames = 180
        self.last_countdown_sec = 4
        self.flash_level_name_timer = 120 # Flash level name for 2 seconds
        
        # State transition
        self.state = 'COUNTDOWN'
       # self.audio.start_engine()
       # self.audio.start_music()

    def _spawn_floating_text(self, text, x, y, color=(255, 255, 255)):
        self.floating_texts.append({
            "text": text, "x": x, "y": y, "color": color, "life": 60, "alpha": 255,
        })

    def _trigger_bomb(self):
        enemies = [e for e in self.enemy_manager.enemies if not e.is_projectile]
        for enemy in enemies:
            self.spawn_explosion(enemy.rect.centerx, enemy.rect.centery, color=(255, 200, 0))
        cleared = len(enemies)
        self.enemy_manager.enemies = [e for e in self.enemy_manager.enemies if e.is_projectile]
        self.score += cleared * 50
        self.screen_flash_timer = 18
        self.screenshake_timer = 20
        self.screenshake_intensity = 10
        #self.audio.play_sound('crash')
        self._spawn_floating_text(f"BOMB! +{cleared * 50}", self.player.rect.centerx, self.player.rect.top - 20, (255, 215, 0))

    def _collect_powerup(self, pu):
        #self.audio.play_sound('powerup')
        self.powerups_collected += 1
        meta = PowerUpManager.apply_effect(pu.type, self.player, self.max_lives)

        if meta.get("extra_life"):
            self.lives = min(self.max_lives, self.lives + 1)
            self._spawn_floating_text("+1 LIFE", self.player.rect.centerx, self.player.rect.top - 10, (255, 80, 100))
        if meta.get("bomb"):
            self._trigger_bomb()
        if meta.get("shake"):
            self.screenshake_timer = 30
            self.screenshake_intensity = 6

        label = f"+{meta['label']}!"
        self._spawn_floating_text(label, self.player.rect.centerx, self.player.rect.top - 30, meta["color"])
        self.spawn_explosion(pu.rect.centerx, pu.rect.centery, color=meta["color"])

    def handle_collision(self, hazard):
        if self.player.is_invincible():
            self.spawn_explosion(hazard.rect.centerx, hazard.rect.centery)
            if hazard in self.enemy_manager.enemies:
                self.enemy_manager.enemies.remove(hazard)
            return

        # If player has active shield, absorb collision and break shield
        if self.player.shield_active:
            self.player.shield_active = False
          #  self.audio.play_sound('shield_break')
            self.spawn_explosion(hazard.rect.centerx, hazard.rect.centery, color=(0, 255, 255))
            
            # Destroy hazard
            if hazard in self.enemy_manager.enemies:
                self.enemy_manager.enemies.remove(hazard)
            return

        # Normal Collision: screen shake + lose a life
        self.screenshake_timer = 25
        self.screenshake_intensity = 8
        self.lives -= 1
       # self.audio.play_sound('crash')
        self.spawn_explosion(hazard.rect.centerx, hazard.rect.centery)
        
        # Remove hazard
        if hazard in self.enemy_manager.enemies:
            self.enemy_manager.enemies.remove(hazard)
            
        # Check game over
        if self.lives <= 0:
            self.state = 'GAME_OVER'
            #self.audio.stop_engine()
            #self.audio.stop_music()
            # Update high score tracker for current level
            self.level_manager.update_high_score(self.level_manager.current_level_idx, self.score)

    def spawn_explosion(self, cx, cy, color=None):
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 9)
            c = color if color else random.choice([(255, 0, 127), (0, 255, 255), (255, 255, 255), (255, 200, 0)])
            self.particles.append({
                "x": cx, "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2.0,
                "color": c,
                "life": random.randint(15, 30),
                "size": random.randint(3, 6)
            })

    def trigger_level_complete(self):
        #self.audio.stop_engine()
        #self.audio.stop_music()
        #self.audio.play_sound('fanfare')
        
        ticks_elapsed = pygame.time.get_ticks() - self.level_start_ticks
        self.level_time_taken = max(1.0, ticks_elapsed / 1000.0)
        
        self.level_manager.update_high_score(self.level_manager.current_level_idx, self.score)
        self.has_unlocked_next = self.level_manager.unlock_next_level()
        self.level_stars_earned = self.level_manager.calc_star_rating(self.score)
        self.star_reveal_timer = 0
        
        # Campaign: brief Level Up transition before next stage (Phase 14)
        if self.campaign_mode and self.has_unlocked_next:
            self.next_level_idx = self.level_manager.current_level_idx + 1
            self.level_up_screen_timer = 180  # ~3 seconds
            self.state = 'LEVEL_UP'
        else:
            self.state = 'LEVEL_COMPLETE'

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.audio.stop_engine()
                self.audio.stop_music()
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.audio.toggle_mute()
                    
                if self.state == 'MENU':
                    if event.key == pygame.K_RETURN:
                        self.state = 'LEVEL_SELECT'
                    elif event.key == pygame.K_c:
                        self.campaign_mode = True
                        self.start_level(1, campaign=True)
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        pygame.quit()
                        sys.exit()
                        
                elif self.state == 'LEVEL_SELECT':
                    max_lvl = len(LEVELS)
                    
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.selected_menu_lvl = max(1, self.selected_menu_lvl - 1)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.selected_menu_lvl = min(max_lvl, self.selected_menu_lvl + 1)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.selected_menu_lvl = max(1, self.selected_menu_lvl - 4)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.selected_menu_lvl = min(max_lvl, self.selected_menu_lvl + 4)
                        
                    elif event.key == pygame.K_RETURN:
                        if self.selected_menu_lvl in self.level_manager.unlocked_levels:
                            self.start_level(self.selected_menu_lvl, campaign=False)
                    elif event.key == pygame.K_c:
                        if self.selected_menu_lvl in self.level_manager.unlocked_levels:
                            self.start_level(self.selected_menu_lvl, campaign=True)
                            
                    elif event.key == pygame.K_r:
                        # Reset Campaign save
                        self.level_manager.reset_progress()
                        self.selected_menu_lvl = 1
                        
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                        
                elif self.state == 'PLAYING':
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        self.state = 'PAUSED'
                        self.audio.stop_engine()
                        
                elif self.state == 'PAUSED':
                    if event.key == pygame.K_p:
                        self.state = 'PLAYING'
                        self.audio.start_engine()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'LEVEL_SELECT'
                        self.audio.stop_engine()
                        self.audio.stop_music()
                        
                elif self.state == 'LEVEL_UP':
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.level_up_screen_timer = 0
                        
                elif self.state == 'LEVEL_COMPLETE':
                    if event.key == pygame.K_RETURN:
                        if self.campaign_mode and self.has_unlocked_next:
                            self.start_level(
                                self.level_manager.current_level_idx + 1,
                                keep_score=True
                            )
                        elif self.has_unlocked_next:
                            self.selected_menu_lvl = self.level_manager.current_level_idx + 1
                            self.start_level(self.selected_menu_lvl, campaign=False)
                        else:
                            self.state = 'VICTORY'
                    elif event.key == pygame.K_r:
                        self.start_level(self.level_manager.current_level_idx, campaign=self.campaign_mode)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'LEVEL_SELECT'
                        self.campaign_mode = False
                        
                elif self.state == 'GAME_OVER':
                    if event.key == pygame.K_RETURN:
                        self.start_level(self.level_manager.current_level_idx)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'LEVEL_SELECT'
                        
                elif self.state == 'VICTORY':
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'

    def update(self):
        # 1. Update basic visual effects (speed lines, particles)
        self.spawn_speed_lines()
        self.update_speed_lines()
        
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.12 # gravity
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

        for ft in self.floating_texts[:]:
            ft["y"] -= 2
            ft["life"] -= 1
            ft["alpha"] = max(0, int(255 * (ft["life"] / 60.0)))
            if ft["life"] <= 0:
                self.floating_texts.remove(ft)

        if self.screen_flash_timer > 0:
            self.screen_flash_timer -= 1
                
        if self.screenshake_timer > 0:
            self.screenshake_timer -= 1
            
        config = self.level_manager.get_current_level_config()
        is_slippery = config.get("slippery", False)
        weather = config.get("weather", None)

        if self.state == 'COUNTDOWN':
            # Slow scrolling road during countdown
            self.road.update(self.road_speed * 0.4, weather)
            self.player.update(self.road.road_left, self.road.road_right, is_slippery)
            
            # Tick count sound
            curr_sec = math.ceil(self.countdown_frames / 60)
            if curr_sec != self.last_countdown_sec and curr_sec > 0:
                self.last_countdown_sec = curr_sec
                self.audio.play_sound('score')
                
            self.countdown_frames -= 1
            if self.countdown_frames <= 0:
                self.state = 'PLAYING'
                self.audio.play_sound('score') # final cue
                
        elif self.state == 'PLAYING':
            # Handle Active Slow-Mo Modifier
            active_speed = self.road_speed
            if self.player.slow_mo_active > 0:
                active_speed = max(3.0, self.road_speed * 0.5)
            if self.player.nitro_active > 0:
                active_speed = min(self.road_speed * 1.5, active_speed * 1.35)
                
            # Update road scrolling
            self.road.update(active_speed, weather)
            
            # Steer player
            self.player.handle_input(is_slippery)
            self.player.update(self.road.road_left, self.road.road_right, is_slippery)
            
            # Increment distance
            self.distance_traveled += active_speed * 0.04
            
            score_multiplier = 2 if self.player.score_boost_active > 0 else 1
            self.score += 0.25 * score_multiplier

            # Handle dodged enemies tracking
            for enemy in self.enemy_manager.enemies:
                if not hasattr(enemy, 'passed_player') or not enemy.passed_player:
                    if enemy.y > self.player.y + CAR_HEIGHT:
                        enemy.passed_player = True
                        if not enemy.is_projectile:
                            self.enemies_dodged += 1

            # Update hazards
            self.enemy_manager.update(active_speed, config, self.player.x + CAR_WIDTH//2)

            if self.score >= config["score_target"]:
                self.trigger_level_complete()

            # Update standard traffic collisions
            for enemy in self.enemy_manager.enemies[:]:
                if self.player.ghost_active > 0:
                    continue
                if self.player.rect.colliderect(enemy.rect):
                    offset_x = enemy.rect.x - self.player.rect.x
                    offset_y = enemy.rect.y - self.player.rect.y
                    if self.player.mask.overlap(enemy.mask, (offset_x, offset_y)):
                        self.handle_collision(enemy)

            # 4. Power-up manager (spawn, magnet pull, collection)
            pool = self.level_manager.get_powerup_pool()
            self.powerup_manager.update(
                active_speed, self.road,
                self.level_manager.current_level_idx, self.player, pool,
            )
            for pu in self.powerup_manager.try_collect(self.player):
                self._collect_powerup(pu)

            # Timers decrements
            if self.flash_level_name_timer > 0:
                self.flash_level_name_timer -= 1
                
        elif self.state == 'LEVEL_UP':
            self.road.update(self.road_speed * 0.25, weather)
            self.level_up_screen_timer -= 1
            if self.level_up_screen_timer <= 0 and self.next_level_idx:
                self.start_level(self.next_level_idx, keep_score=True)
                
        elif self.state == 'LEVEL_COMPLETE':
            self.star_reveal_timer = min(self.star_reveal_timer + 1, 180)
            
        elif self.state == 'GAME_OVER':
            # Slow decelerating scroll
            self.road.update(self.road_speed * 0.12, weather)
            self.road_speed = max(0.0, self.road_speed - 0.25)

    def spawn_speed_lines(self):
        nitro_boost = self.player.nitro_active > 0
        spawn_chance = 0.35 if nitro_boost else 0.15
        if random.random() < spawn_chance:
            lx = random.randint(10, self.road.road_left - 20)
            self.speed_lines.append({
                "x": lx, "y": -60, "w": 2, "h": random.randint(30, 70), "speed": self.road_speed * 1.3
            })
        if random.random() < spawn_chance:
            rx = random.randint(self.road.road_right + 20, SCREEN_WIDTH - 20)
            line_h = random.randint(50, 100) if nitro_boost else random.randint(30, 70)
            self.speed_lines.append({
                "x": rx, "y": -60, "w": 2, "h": line_h, "speed": self.road_speed * (1.8 if nitro_boost else 1.3)
            })

    def update_speed_lines(self):
        for line in self.speed_lines[:]:
            line["y"] += line["speed"]
            if line["y"] > SCREEN_HEIGHT:
                self.speed_lines.remove(line)

    def draw(self):
        # 1. Setup screenshake
        render_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 2. Render road and margins
        self.road.draw(render_surf)
        
        # Speed margins lines
        for line in self.speed_lines:
            pygame.draw.rect(render_surf, (180, 240, 255, 120), (line["x"], line["y"], line["w"], line["h"]))

        # Night level darkness headlight mask overlay
        config = self.level_manager.get_current_level_config()
        is_night = config.get("visibility", None) == "night"
        
        # Draw player & entities
        if self.state not in ('MENU', 'LEVEL_SELECT'):
            self.player.draw(render_surf)
            self.enemy_manager.draw(render_surf)
            
            self.powerup_manager.draw(render_surf)

        # Draw night headlights mask before weather & HUD overlays
        if self.state not in ('MENU', 'LEVEL_SELECT') and is_night:
            self.road.draw_night_light_overlay(render_surf, self.player, self.enemy_manager.enemies)

        # Draw weather overlay (rain, snow, dust)
        if self.state not in ('MENU', 'LEVEL_SELECT'):
            self.road.draw_weather_overlay(render_surf)

        # Slow-mo blue tint overlay
        if self.state == 'PLAYING' and self.player.slow_mo_active > 0:
            slow_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            slow_overlay.fill((40, 80, 200, 45))
            render_surf.blit(slow_overlay, (0, 0))

        # Bomb white screen flash
        if self.screen_flash_timer > 0:
            flash_alpha = min(200, self.screen_flash_timer * 12)
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, flash_alpha))
            render_surf.blit(flash, (0, 0))

        # Floating pickup text
        for ft in self.floating_texts:
            font = self.hud.font_small
            lbl = font.render(ft["text"], True, ft["color"])
            lbl.set_alpha(ft["alpha"])
            render_surf.blit(lbl, (ft["x"] - lbl.get_width() // 2, ft["y"]))

        # Draw particles
        for p in self.particles:
            alpha = int((p["life"] / 30.0) * 255)
            alpha = max(0, min(255, alpha))
            p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p["color"], alpha), (p["size"], p["size"]), p["size"])
            render_surf.blit(p_surf, (p["x"] - p["size"], p["y"] - p["size"]))

        # Draw Score HUD
        if self.state in ('PLAYING', 'PAUSED', 'LEVEL_UP', 'LEVEL_COMPLETE', 'GAME_OVER', 'COUNTDOWN'):
            # Grab power-up remaining frames to render progress bars
            score_mult = 2 if self.player.score_boost_active > 0 else 1
            pu_bars = PowerUpManager.get_hud_status(self.player)
            self.hud.draw(
                render_surf, self.score,
                int(self.level_manager.high_scores.get(str(self.level_manager.current_level_idx), 0)),
                self.lives, self.max_lives,
                self.level_manager.current_level_idx, self.road_speed, 18.0,
                pu_bars, score_mult,
            )

        # Draw state menus
        if self.state == 'MENU':
            self.draw_menu_screen(render_surf)
        elif self.state == 'LEVEL_SELECT':
            self.draw_level_select_screen(render_surf)
        elif self.state == 'COUNTDOWN':
            self.draw_countdown_overlay(render_surf)
        elif self.state == 'PAUSED':
            self.draw_paused_overlay(render_surf)
        elif self.state == 'LEVEL_UP':
            self.draw_level_up_overlay(render_surf)
        elif self.state == 'LEVEL_COMPLETE':
            self.draw_level_complete_overlay(render_surf)
        elif self.state == 'GAME_OVER':
            self.draw_game_over_overlay(render_surf)
        elif self.state == 'VICTORY':
            self.draw_victory_screen(render_surf)

        # Flashing level name at start
        if self.state == 'PLAYING' and self.flash_level_name_timer > 0:
            self.draw_level_intro_flash(render_surf, config["name"])

        # Screenshake viewport offset blit
        shake_x = 0
        shake_y = 0
        if self.screenshake_timer > 0:
            shake_x = random.randint(-self.screenshake_intensity, self.screenshake_intensity)
            shake_y = random.randint(-self.screenshake_intensity, self.screenshake_intensity)
            
        self.screen.fill(COLOR_BACKGROUND)
        self.screen.blit(render_surf, (shake_x, shake_y))
        pygame.display.flip()

    # --- UI Drawing Code ---

    def draw_menu_screen(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (5, 5, 8, 180), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        title_font = self.hud.font_large
        medium_font = self.hud.font_medium
        small_font = self.hud.font_small
        
        logo_color = (0, 240, 255)
        accent_color = COLOR_HUD_ACCENT
        
        logo_text1 = title_font.render("NEON", True, logo_color)
        logo_text2 = title_font.render("RACER", True, accent_color)
        
        cy = SCREEN_HEIGHT // 3 - 60
        surface.blit(logo_text1, ((SCREEN_WIDTH - logo_text1.get_width() - logo_text2.get_width() - 15) // 2, cy))
        surface.blit(logo_text2, ((SCREEN_WIDTH - logo_text1.get_width() - logo_text2.get_width() - 15) // 2 + logo_text1.get_width() + 15, cy))
        
        pygame.draw.line(surface, COLOR_WHITE, (SCREEN_WIDTH // 2 - 120, cy + 55), (SCREEN_WIDTH // 2 + 120, cy + 55), 2)
        pygame.draw.line(surface, logo_color, (SCREEN_WIDTH // 2 - 80, cy + 59), (SCREEN_WIDTH // 2 + 80, cy + 59), 1)

        # Draw preview car
        preview_car = Player()
        preview_car.x = (SCREEN_WIDTH - preview_car.rect.width) // 2
        preview_car.y = SCREEN_HEIGHT // 2 - 30
        preview_car.update(self.road.road_left, self.road.road_right)
        preview_car.draw(surface)

        pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.007))
        enter_color = (pulse, pulse, 255)
        enter_text = medium_font.render("ENTER: Stage Select  |  C: Start Campaign", True, enter_color)
        surface.blit(enter_text, ((SCREEN_WIDTH - enter_text.get_width()) // 2, SCREEN_HEIGHT // 2 + 140))

        ctrl_y = SCREEN_HEIGHT - 170
        ctrl_bg = pygame.Surface((SCREEN_WIDTH - 80, 110), pygame.SRCALPHA)
        pygame.draw.rect(ctrl_bg, (15, 15, 25, 200), (0, 0, SCREEN_WIDTH - 80, 110), border_radius=8)
        pygame.draw.rect(ctrl_bg, (0, 229, 255, 80), (0, 0, SCREEN_WIDTH - 80, 110), 1, border_radius=8)
        surface.blit(ctrl_bg, (40, ctrl_y))
        
        controls = [
            "A / D or LEFT / RIGHT : Move Car",
            "P : Pause Game   |   M : Toggle Mute Sound",
            "ENTER : Select/Restart  |  ESC/Q : Exit"
        ]
        for idx, line in enumerate(controls):
            lbl = small_font.render(line, True, (200, 220, 240))
            surface.blit(lbl, ((SCREEN_WIDTH - lbl.get_width()) // 2, ctrl_y + 15 + idx * 28))

    def draw_level_select_screen(self, surface):
        """Draws a beautiful neon selection grid of stages."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (8, 8, 14, 230), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        title_font = self.hud.font_large
        medium_font = self.hud.font_medium
        small_font = self.hud.font_small
        
        # Title header
        title = title_font.render("SELECT STAGE", True, COLOR_HUD_TEXT)
        surface.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 40))
        pygame.draw.line(surface, COLOR_HUD_TEXT, (SCREEN_WIDTH//2 - 100, 95), (SCREEN_WIDTH//2 + 100, 95), 2)
        
        # Grid dimensions: 2 rows of 4 cards
        card_w, card_h = 110, 110
        gap_x, gap_y = 25, 30
        start_x = (SCREEN_WIDTH - (4 * card_w + 3 * gap_x)) // 2
        start_y = 140
        
        for lvl_id in range(1, 9):
            grid_col = (lvl_id - 1) % 4
            grid_row = (lvl_id - 1) // 4
            
            cx = start_x + grid_col * (card_w + gap_x)
            cy = start_y + grid_row * (card_h + gap_y)
            
            # Check if this level index is unlocked
            unlocked = lvl_id in self.level_manager.unlocked_levels
            selected = lvl_id == self.selected_menu_lvl
            
            # Card background
            card_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            
            if unlocked:
                card_color = (20, 20, 32, 230)
                border_color = (0, 255, 128) if selected else (0, 150, 255)
                text_color = COLOR_WHITE
            else:
                card_color = (15, 15, 20, 180)
                border_color = (50, 50, 60)
                text_color = (100, 100, 110)
                
            pygame.draw.rect(card_bg, card_color, (0, 0, card_w, card_h), border_radius=10)
            
            # Select pulse glow
            border_thickness = 2
            if selected:
                border_thickness = 4
                if unlocked:
                    pulse_alpha = int(120 + 100 * math.sin(pygame.time.get_ticks() * 0.012))
                    pygame.draw.rect(card_bg, (*border_color, pulse_alpha // 3), (0, 0, card_w, card_h), border_radius=10)
                    
            pygame.draw.rect(card_bg, border_color, (0, 0, card_w, card_h), border_thickness, border_radius=10)
            surface.blit(card_bg, (cx, cy))
            
            # Text label
            num_text = self.hud.font_large.render(str(lvl_id), True, text_color)
            surface.blit(num_text, (cx + (card_w - num_text.get_width()) // 2, cy + 25))
            
            # Draw padlock symbol or high score
            if not unlocked:
                # Mini lock triangle
                pygame.draw.rect(surface, (100, 100, 110), (cx + card_w//2 - 6, cy + card_h - 32, 12, 10), border_radius=1)
                pygame.draw.circle(surface, (100, 100, 110), (cx + card_w//2, cy + card_h - 32), 6, 2)
            else:
                score_str = f"HI: {self.level_manager.high_scores.get(str(lvl_id), 0)}"
                sc_lbl = pygame.font.SysFont('consolas', 12, bold=True).render(score_str, True, (0, 229, 255))
                surface.blit(sc_lbl, (cx + (card_w - sc_lbl.get_width())//2, cy + card_h - 25))

        # Selected level details box
        details_y = 440
        db_w, db_h = SCREEN_WIDTH - 80, 160
        pygame.draw.rect(surface, (20, 20, 32, 220), (40, details_y, db_w, db_h), border_radius=8)
        
        cfg = LEVELS[self.selected_menu_lvl]
        unlocked = self.selected_menu_lvl in self.level_manager.unlocked_levels
        
        if unlocked:
            title_color = COLOR_HUD_TEXT
            desc_str = cfg["desc"]
            target_str = f"TARGET: {cfg['score_target']} PTS  |  SPEED: {int(cfg['base_speed'] * 12)} MPH"
        else:
            title_color = (120, 120, 130)
            desc_str = "🔒 This stage is currently locked. Complete previous stages to unlock."
            target_str = "TARGET: ??? PTS"
            
        lvl_title = medium_font.render(f"STAGE {self.selected_menu_lvl}: {cfg['name']}", True, title_color)
        surface.blit(lvl_title, (60, details_y + 15))
        
        target_lbl = small_font.render(target_str, True, (0, 255, 153) if unlocked else (80, 80, 80))
        surface.blit(target_lbl, (60, details_y + 50))
        
        # Wrap description text
        words = desc_str.split(" ")
        lines = [""]
        for w in words:
            if len(lines[-1] + w) < 48:
                lines[-1] += w + " "
            else:
                lines.append(w + " ")
                
        for line_idx, line in enumerate(lines[:3]):
            desc_lbl = small_font.render(line.strip(), True, (180, 180, 200))
            surface.blit(desc_lbl, (60, details_y + 85 + line_idx * 22))

        # Navigation Instructions
        instr_lbl = small_font.render(
            "ENTER: Arcade  |  C: Campaign  |  ESC: Back  |  R: Reset Progress",
            True, (120, 120, 130)
        )
        surface.blit(instr_lbl, ((SCREEN_WIDTH - instr_lbl.get_width()) // 2, SCREEN_HEIGHT - 45))

    def draw_level_intro_flash(self, surface, name):
        """Flashes level details at the top/middle on game start."""
        if self.flash_level_name_timer > 60 or (self.flash_level_name_timer // 8) % 2 == 0:
            font = self.hud.font_large
            # Draw semi-transparent banner
            banner = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
            banner.fill((0, 0, 0, 130))
            surface.blit(banner, (0, SCREEN_HEIGHT // 3 - 35))
            
            lbl = font.render(name.upper(), True, COLOR_HUD_TEXT)
            surface.blit(lbl, ((SCREEN_WIDTH - lbl.get_width()) // 2, SCREEN_HEIGHT // 3 - 20))

    def draw_countdown_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 90), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        sec = math.ceil(self.countdown_frames / 60)
        
        if sec == 3:
            txt, color = "3", (255, 0, 127)
        elif sec == 2:
            txt, color = "2", (255, 215, 0)
        elif sec == 1:
            txt, color = "1", (0, 255, 153)
        else:
            txt, color = "GO!", (0, 229, 255)
            
        c_font = pygame.font.SysFont('consolas', 120, bold=True)
        lbl = c_font.render(txt, True, color)
        cx = (SCREEN_WIDTH - lbl.get_width()) // 2
        cy = (SCREEN_HEIGHT - lbl.get_height()) // 2
        
        lbl_glow = c_font.render(txt, True, COLOR_WHITE)
        for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            surface.blit(lbl_glow, (cx + ox, cy + oy))
            
        surface.blit(lbl, (cx, cy))

    def draw_paused_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (5, 5, 12, 180), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        title_font = self.hud.font_large
        medium_font = self.hud.font_medium
        
        lbl_pause = title_font.render("GAME PAUSED", True, COLOR_HUD_TEXT)
        surface.blit(lbl_pause, ((SCREEN_WIDTH - lbl_pause.get_width()) // 2, SCREEN_HEIGHT // 2 - 80))
        
        lbl_resume = medium_font.render("Press P to Resume", True, COLOR_WHITE)
        lbl_menu = medium_font.render("Press ESC to Select Stage", True, (170, 180, 200))
        
        surface.blit(lbl_resume, ((SCREEN_WIDTH - lbl_resume.get_width()) // 2, SCREEN_HEIGHT // 2 + 10))
        surface.blit(lbl_menu, ((SCREEN_WIDTH - lbl_menu.get_width()) // 2, SCREEN_HEIGHT // 2 + 50))

    def _draw_star(self, surf, cx, cy, active=True, sz=26, slide_offset=0):
        """Draw a single star with optional slide-in offset (Phase 21)."""
        cy += slide_offset
        color = (255, 215, 0) if active else (40, 40, 50)
        points = []
        for angle in range(0, 360, 72):
            r1 = math.radians(angle - 90)
            points.append((cx + sz * math.cos(r1), cy + sz * math.sin(r1)))
            r2 = math.radians(angle - 90 + 36)
            points.append((cx + (sz // 2) * math.cos(r2), cy + (sz // 2) * math.sin(r2)))
        if active:
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, COLOR_WHITE, points, 1)
        else:
            pygame.draw.polygon(surf, color, points, 2)

    def draw_level_up_overlay(self, surface):
        """Brief Level Up transition between campaign stages (Phase 14)."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 160), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        pulse = int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.012))
        title = self.hud.font_large.render("LEVEL UP!", True, (pulse, 255, pulse))
        surface.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, SCREEN_HEIGHT // 3 - 50))
        
        if self.next_level_idx and self.next_level_idx in LEVELS:
            next_cfg = LEVELS[self.next_level_idx]
            name_lbl = self.hud.font_medium.render(next_cfg["name"].upper(), True, COLOR_HUD_TEXT)
            surface.blit(name_lbl, ((SCREEN_WIDTH - name_lbl.get_width()) // 2, SCREEN_HEIGHT // 3 + 10))
            
        score_lbl = self.hud.font_small.render(f"TOTAL SCORE: {int(self.score):06d}", True, COLOR_WHITE)
        surface.blit(score_lbl, ((SCREEN_WIDTH - score_lbl.get_width()) // 2, SCREEN_HEIGHT // 2))
        
        sec_left = max(0, self.level_up_screen_timer // 60)
        hint = self.hud.font_small.render(f"Next stage in {sec_left + 1}s... (ENTER to skip)", True, (140, 150, 170))
        surface.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 100))

    def draw_level_complete_overlay(self, surface):
        """Draws the Level Complete scorecard overlay (stars, time, distance, dodged count)."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (8, 10, 20, 220), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        title_font = self.hud.font_large
        medium_font = self.hud.font_medium
        small_font = self.hud.font_small
        
        lbl_title = title_font.render("STAGE COMPLETED!", True, (0, 255, 128))
        surface.blit(lbl_title, ((SCREEN_WIDTH - lbl_title.get_width()) // 2, SCREEN_HEIGHT // 4 - 40))
        
        pygame.draw.line(surface, (0, 255, 128), (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//4 + 15), (SCREEN_WIDTH//2 + 120, SCREEN_HEIGHT//4 + 15), 2)
        
        # Score-based stars with staggered slide-in reveal (Phase 21)
        star_y = SCREEN_HEIGHT // 4 + 40
        star_x_center = SCREEN_WIDTH // 2
        stars_gained = self.level_stars_earned
        
        star_positions = [
            (star_x_center - 60, star_y, 26, 1),
            (star_x_center, star_y - 15, 32, 2),
            (star_x_center + 60, star_y, 26, 3),
        ]
        for cx, cy, sz, rank in star_positions:
            reveal_frame = (rank - 1) * 50
            if self.star_reveal_timer < reveal_frame:
                continue
            progress = min(1.0, (self.star_reveal_timer - reveal_frame) / 30.0)
            slide = int((1.0 - progress) * -40)
            self._draw_star(surface, cx, cy, active=(stars_gained >= rank), sz=sz, slide_offset=slide)
        
        # 3. Statistics Panel
        panel_y = SCREEN_HEIGHT // 2 - 20
        panel_w = SCREEN_WIDTH - 100
        panel_h = 200
        pygame.draw.rect(surface, (15, 15, 25, 200), (50, panel_y, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(surface, (0, 255, 128, 100), (50, panel_y, panel_w, panel_h), 1, border_radius=8)
        
        cfg = self.level_manager.get_current_level_config()
        stats = [
            f"Score Earned      : {int(self.score):06d}  ({stars_gained}/3 stars)",
            f"Distance Traveled : {int(self.distance_traveled)} meters",
            f"Enemies Evaded    : {self.enemies_dodged}",
            f"Power-ups Grabbed : {self.powerups_collected}",
            f"Time Elapsed      : {self.level_time_taken:.1f} seconds",
            f"Target Was        : {cfg['score_target']} pts",
        ]
        
        for idx, stat in enumerate(stats):
            lbl = small_font.render(stat, True, (200, 220, 240))
            surface.blit(lbl, (80, panel_y + 18 + idx * 28))

        pulse = int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.005))
        if self.campaign_mode and self.has_unlocked_next:
            next_txt = "ENTER: Next Stage (Campaign)"
        elif self.has_unlocked_next:
            next_txt = "ENTER: Next Stage"
        else:
            next_txt = "ENTER: Victory Screen"
        lbl_next = medium_font.render(next_txt, True, (pulse, pulse, pulse))
        lbl_retry = small_font.render("R: Retry Stage", True, (170, 180, 200))
        lbl_back = small_font.render("ESC: Stage Select", True, (130, 130, 140))
        
        surface.blit(lbl_next, ((SCREEN_WIDTH - lbl_next.get_width()) // 2, SCREEN_HEIGHT - 130))
        surface.blit(lbl_retry, ((SCREEN_WIDTH - lbl_retry.get_width()) // 2, SCREEN_HEIGHT - 95))
        surface.blit(lbl_back, ((SCREEN_WIDTH - lbl_back.get_width()) // 2, SCREEN_HEIGHT - 65))

    def draw_game_over_overlay(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (15, 0, 5, 200), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.blit(overlay, (0, 0))
        
        title_font = self.hud.font_large
        medium_font = self.hud.font_medium
        small_font = self.hud.font_small
        
        lbl_go = title_font.render("GAME OVER", True, COLOR_HUD_ACCENT)
        surface.blit(lbl_go, ((SCREEN_WIDTH - lbl_go.get_width()) // 2, SCREEN_HEIGHT // 3 - 30))
        
        pygame.draw.line(surface, COLOR_HUD_ACCENT, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 3 + 25), (SCREEN_WIDTH // 2 + 120, SCREEN_HEIGHT // 3 + 25), 2)

        score_val = int(self.score)
        lbl_score = medium_font.render(f"FINAL SCORE: {score_val:06d}", True, COLOR_WHITE)
        surface.blit(lbl_score, ((SCREEN_WIDTH - lbl_score.get_width()) // 2, SCREEN_HEIGHT // 2 - 20))
        
        hs = int(self.level_manager.high_scores.get(str(self.level_manager.current_level_idx), 0))
        lbl_hs = small_font.render(f"STAGE HIGH SCORE: {hs:06d}", True, (180, 180, 200))
        surface.blit(lbl_hs, ((SCREEN_WIDTH - lbl_hs.get_width()) // 2, SCREEN_HEIGHT // 2 + 25))

        pulse = int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.005))
        lbl_restart = medium_font.render("PRESS ENTER TO RETRY STAGE", True, (pulse, pulse, pulse))
        lbl_menu = small_font.render("Press ESC for Stage Select", True, (140, 140, 160))
        
        surface.blit(lbl_restart, ((SCREEN_WIDTH - lbl_restart.get_width()) // 2, SCREEN_HEIGHT // 2 + 100))
        surface.blit(lbl_menu, ((SCREEN_WIDTH - lbl_menu.get_width()) // 2, SCREEN_HEIGHT // 2 + 140))

    def draw_victory_screen(self, surface):
        """Draws the final victory credit screen upon campaign completion."""
        # Rainbow background flashing
        ticks = pygame.time.get_ticks()
        r = int(15 + 10 * math.sin(ticks * 0.005))
        g = int(25 + 15 * math.sin(ticks * 0.007))
        b = int(35 + 20 * math.sin(ticks * 0.009))
        
        surface.fill((r, g, b))
        
        # Spawn fountain sparks in the center
        if random.random() < 0.2:
            self.spawn_explosion(SCREEN_WIDTH//2, SCREEN_HEIGHT//3, color=random.choice([(0, 255, 255), (255, 0, 127), (255, 215, 0)]))
            
        title_font = self.hud.font_large
        medium_font = self.hud.font_medium
        small_font = self.hud.font_small
        
        # Gold header
        lbl_title = title_font.render("VICTORY!", True, (255, 215, 0))
        lbl_sub = medium_font.render("CHAMPION OF THE GRID", True, COLOR_WHITE)
        
        surface.blit(lbl_title, ((SCREEN_WIDTH - lbl_title.get_width()) // 2, SCREEN_HEIGHT // 4 - 30))
        surface.blit(lbl_sub, ((SCREEN_WIDTH - lbl_sub.get_width()) // 2, SCREEN_HEIGHT // 4 + 25))
        
        pygame.draw.line(surface, (255, 215, 0), (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 4 + 75), (SCREEN_WIDTH // 2 + 140, SCREEN_HEIGHT // 4 + 75), 2)
        
        # Credits panel
        panel_y = SCREEN_HEIGHT // 2 - 30
        panel_w = SCREEN_WIDTH - 100
        panel_h = 160
        pygame.draw.rect(surface, (15, 10, 25, 200), (50, panel_y, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0, 100), (50, panel_y, panel_w, panel_h), 1, border_radius=8)
        
        # Sum overall stars unlocked
        total_stars = 0
        for lvl_id in LEVELS.keys():
            hs = self.level_manager.high_scores.get(str(lvl_id), 0)
            if hs > 0:
                # Add 3 stars as placeholder representation
                total_stars += 3
                
        stats = [
            "All 8 Neon Sectors Defeated!",
            f"Campaign Status : GRID MASTER UNLOCKED",
            f"Overall High Scores saved to save.json",
            "Thank you for playing!"
        ]
        
        for idx, stat in enumerate(stats):
            lbl = small_font.render(stat, True, (200, 220, 240))
            surface.blit(lbl, (80, panel_y + 25 + idx * 30))

        # Return prompt
        pulse = int(180 + 75 * math.sin(ticks * 0.005))
        lbl_enter = medium_font.render("PRESS ENTER TO MAIN MENU", True, (pulse, pulse, pulse))
        surface.blit(lbl_enter, ((SCREEN_WIDTH - lbl_enter.get_width()) // 2, SCREEN_HEIGHT - 130))


if __name__ == "__main__":
    game = GameEngine()
    game.run()

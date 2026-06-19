import pygame
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_HUD_TEXT, COLOR_HUD_ACCENT, COLOR_WHITE, COLOR_BLACK
)

class HUD:
    def __init__(self):
        # Initialize fonts
        try:
            self.font_large = pygame.font.SysFont('consolas', 42, bold=True)
            self.font_medium = pygame.font.SysFont('consolas', 26, bold=True)
            self.font_small = pygame.font.SysFont('consolas', 18, bold=True)
        except Exception:
            self.font_large = pygame.font.SysFont(None, 48)
            self.font_medium = pygame.font.SysFont(None, 30)
            self.font_small = pygame.font.SysFont(None, 20)

    def draw_heart(self, surface, x, y, size=18):
        """Draws a glossy neon-red heart procedurally at (x, y)."""
        glow_color = COLOR_HUD_ACCENT
        inner_color = (255, 50, 100)
        
        r = size // 4
        lc = (x - r, y)
        rc = (x + r, y)
        
        # Draw glow
        for thickness in range(3, 0, -1):
            g_color = tuple(min(255, c + (4 - thickness) * 30) for c in glow_color)
            pygame.draw.circle(surface, g_color, lc, r + thickness)
            pygame.draw.circle(surface, g_color, rc, r + thickness)
            pygame.draw.polygon(surface, g_color, [
                (x - 2 * r - thickness, y + 2),
                (x + 2 * r + thickness, y + 2),
                (x, y + 2 * r + thickness)
            ])
            
        # Draw solid inner heart
        pygame.draw.circle(surface, inner_color, lc, r)
        pygame.draw.circle(surface, inner_color, rc, r)
        pygame.draw.polygon(surface, inner_color, [
            (x - 2 * r, y + 2),
            (x + 2 * r, y + 2),
            (x, y + 2 * r)
        ])
        
        # Specular reflection dot
        pygame.draw.circle(surface, COLOR_WHITE, (lc[0] - 2, lc[1] - 2), 2)

    def draw(self, surface, score, high_score, lives, max_lives, level, speed, max_speed,
             active_powerups=None, score_multiplier=1):
        if active_powerups is None:
            active_powerups = []
        # 1. Semi-transparent glassmorphic top header bar
        header_height = 60
        header_surf = pygame.Surface((SCREEN_WIDTH, header_height), pygame.SRCALPHA)
        pygame.draw.rect(header_surf, (15, 15, 22, 180), (0, 0, SCREEN_WIDTH, header_height))
        # Cyan neon divider line under header
        pygame.draw.line(header_surf, (0, 229, 255, 100), (0, header_height - 1), (SCREEN_WIDTH, header_height - 1), 2)
        surface.blit(header_surf, (0, 0))

        # 2. Render Score (Top Left)
        score_label = self.font_small.render("SCORE", True, COLOR_HUD_TEXT)
        score_val = self.font_medium.render(f"{int(score):06d}", True, COLOR_WHITE)
        surface.blit(score_label, (20, 8))
        surface.blit(score_val, (20, 26))

        # 3. Render High Score (Top Right)
        hs_label = self.font_small.render("HI-SCORE", True, COLOR_HUD_ACCENT)
        hs_val = self.font_medium.render(f"{int(high_score):06d}", True, COLOR_WHITE)
        surface.blit(hs_label, (SCREEN_WIDTH - 20 - hs_label.get_width(), 8))
        surface.blit(hs_val, (SCREEN_WIDTH - 20 - hs_val.get_width(), 26))

        # 4. Render Level / Stage Indicator (Top Center)
        lvl_name = f"STAGE {level}"
        lbl_color = COLOR_HUD_TEXT
        lvl_val = self.font_medium.render(lvl_name, True, lbl_color)
        surface.blit(lvl_val, ((SCREEN_WIDTH - lvl_val.get_width()) // 2, 8))
        
        # Speed numeric display
        speed_mph = int(speed * 12)
        speed_val = self.font_small.render(f"{speed_mph} MPH", True, (0, 255, 153))
        surface.blit(speed_val, ((SCREEN_WIDTH - speed_val.get_width()) // 2, 36))

        # 5. Render Lives Hearts (Left side, just below the header)
        heart_start_x = 30
        heart_y = header_height + 25
        for i in range(max_lives):
            if i < lives:
                self.draw_heart(surface, heart_start_x + i * 28, heart_y, size=20)
            else:
                lc = (heart_start_x + i * 28 - 5, heart_y)
                rc = (heart_start_x + i * 28 + 5, heart_y)
                pygame.draw.circle(surface, (50, 50, 60), lc, 5, 1)
                pygame.draw.circle(surface, (50, 50, 60), rc, 5, 1)
                pygame.draw.polygon(surface, (50, 50, 60), [
                    (heart_start_x + i * 28 - 10, heart_y + 2),
                    (heart_start_x + i * 28 + 10, heart_y + 2),
                    (heart_start_x + i * 28, heart_y + 12)
                ], 1)

        # 6. Render Speedometer Bar (Vertical bar on the right side)
        bar_x = SCREEN_WIDTH - 20
        bar_y = header_height + 20
        bar_w = 8
        bar_h = 100
        
        pygame.draw.rect(surface, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        
        fill_ratio = (speed - 4.0) / (max_speed - 4.0) if max_speed != 4.0 else 0.0
        fill_ratio = max(0.0, min(1.0, fill_ratio))
        fill_h = int(bar_h * fill_ratio)
        
        if fill_h > 0:
            bar_color = (
                int(0 + fill_ratio * 255),
                int(255 - fill_ratio * 128),
                int(153 + fill_ratio * 100)
            )
            bar_color = tuple(max(0, min(255, c)) for c in bar_color)
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y + (bar_h - fill_h), bar_w, fill_h), border_radius=4)
            
        speed_lbl = self.font_small.render("SPD", True, (150, 150, 170))
        surface.blit(speed_lbl, (bar_x - 30, bar_y + bar_h // 2 - 8))

        # 7. Active power-up status bars (icon + drain bar)
        pu_x = 20
        pu_y = header_height + 55
        bar_w_pu = 72
        bar_h_pu = 8
        for icon, color, pct, flash in active_powerups:
            if flash and (pygame.time.get_ticks() // 150) % 2 == 0:
                color = COLOR_WHITE
            icon_lbl = self.font_small.render(icon, True, color)
            surface.blit(icon_lbl, (pu_x, pu_y))
            bar_x = pu_x + 36
            pygame.draw.rect(surface, (30, 30, 35), (bar_x, pu_y + 4, bar_w_pu, bar_h_pu), border_radius=2)
            fill_w = int(bar_w_pu * max(0.0, min(1.0, pct)))
            if fill_w > 0:
                pygame.draw.rect(surface, color, (bar_x, pu_y + 4, fill_w, bar_h_pu), border_radius=2)
            pu_y += 22

        # Score boost badge on HUD
        if score_multiplier > 1:
            badge_color = (255, 215, 0) if (pygame.time.get_ticks() // 200) % 2 == 0 else (255, 255, 200)
            mult_lbl = self.font_medium.render(f"{score_multiplier}X", True, badge_color)
            surface.blit(mult_lbl, (SCREEN_WIDTH // 2 - mult_lbl.get_width() // 2, header_height + 2))

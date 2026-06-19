import os

# Screen Configuration
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
FPS = 60

# Game Speeds (Vertical scrolling)
INITIAL_ROAD_SPEED = 7.0
MAX_ROAD_SPEED = 22.0
SPEED_INCREMENT = 0.5  # Speed increase per level

# Player Physics (Horizontal movement)
PLAYER_SPEED = 7.0
PLAYER_ACCEL = 0.5
PLAYER_DECEL = 0.3
PLAYER_MAX_TILT = 12  # Maximum tilt angle in degrees when turning

# Vehicle Dimensions
CAR_WIDTH = 54
CAR_HEIGHT = 96

# Road Configuration
ROAD_WIDTH = 380
ROAD_LEFT = (SCREEN_WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT

# Score milestones
SCORE_PER_LEVEL = 1000

# File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIGH_SCORE_FILE = os.path.join(BASE_DIR, "high_score.txt")

# Neon Theme Colors (RGB)
COLOR_BACKGROUND = (10, 10, 14)       # Deep space black/dark grey
COLOR_ROAD = (22, 22, 28)             # Dark asphalt gray
COLOR_ROAD_BORDER = (0, 255, 153)     # Vibrant neon green/turquoise
COLOR_LANE_MARKING = (255, 215, 0)    # Warm gold yellow
COLOR_HUD_TEXT = (0, 229, 255)        # Electric neon cyan
COLOR_HUD_ACCENT = (255, 0, 127)      # Neon pink/magenta
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# Sound parameters (synthesized frequencies)
SFX_ENGINE_FREQ = 80
SFX_CRASH_FREQ = 150
SFX_SCORE_FREQ = 880

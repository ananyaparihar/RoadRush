import os
import json

# Progressive power-up unlocks per level (Phase E — Step 7)
LEVEL_POWERUP_POOLS = {
    1: ['score_boost'],
    2: ['score_boost', 'shield'],
    3: ['score_boost', 'shield', 'slowmo', 'ghost'],
    4: ['score_boost', 'shield', 'slowmo', 'nitro', 'ghost'],
    5: ['score_boost', 'shield', 'slowmo', 'nitro', 'extra_life', 'ghost'],
    6: ['score_boost', 'shield', 'slowmo', 'nitro', 'extra_life', 'magnet', 'bomb'],
    7: ['score_boost', 'shield', 'slowmo', 'nitro', 'extra_life', 'magnet', 'bomb', 'ghost'],
    8: ['score_boost', 'shield', 'slowmo', 'nitro', 'extra_life', 'magnet', 'bomb', 'ghost'],
}

LEVELS = {
    1: {
        "name": "City Streets",
        "score_target": 600,
        "base_speed": 6.0,
        "spawn_rate": 100,
        "lanes": 3,
        "bg_style": "city",
        "slippery": False,
        "weather": None,
        "visibility": None,
        "desc": "Learn the basics. 3 lanes, light city traffic."
    },
    2: {
        "name": "Highway Rush",
        "score_target": 1200,
        "base_speed": 8.0,
        "spawn_rate": 80,
        "lanes": 4,
        "bg_style": "highway",
        "slippery": False,
        "weather": None,
        "visibility": None,
        "desc": "Wide 4-lane freeway. Truck hazards introduced."
    },
    3: {
        "name": "Desert Storm",
        "score_target": 1800,
        "base_speed": 9.0,
        "spawn_rate": 65,
        "lanes": 3,
        "bg_style": "desert",
        "slippery": False,
        "weather": "sandstorm",
        "visibility": "sandstorm",
        "desc": "Low visibility sandstorm. Dodge fast desert traffic."
    },
    4: {
        "name": "Mountain Pass",
        "score_target": 2400,
        "base_speed": 10.0,
        "spawn_rate": 60,
        "lanes": 2,
        "bg_style": "mountain",
        "slippery": False,
        "weather": None,
        "visibility": None,
        "desc": "Narrow 2-lane cliffside road. Watch out for falling boulders!"
    },
    5: {
        "name": "Night City",
        "score_target": 3000,
        "base_speed": 11.0,
        "spawn_rate": 50,
        "lanes": 4,
        "bg_style": "night",
        "slippery": False,
        "weather": None,
        "visibility": "night",
        "desc": "Dark city highway. Steer using headlight cones."
    },
    6: {
        "name": "Rainy Highway",
        "score_target": 3600,
        "base_speed": 11.5,
        "spawn_rate": 55,
        "lanes": 3,
        "bg_style": "rain",
        "slippery": True,
        "weather": "rain",
        "visibility": None,
        "desc": "Slippery wet asphalt. Heavy traffic in the rain."
    },
    7: {
        "name": "Neon Race Track",
        "score_target": 4200,
        "base_speed": 13.0,
        "spawn_rate": 45,
        "lanes": 3,
        "bg_style": "race",
        "slippery": False,
        "weather": None,
        "visibility": None,
        "desc": "Professional neon speedway. Opponent cars weave fast."
    },
    8: {
        "name": "Glacier Pass",
        "score_target": 5000,
        "base_speed": 14.0,
        "spawn_rate": 40,
        "lanes": 3,
        "bg_style": "ice",
        "slippery": True,
        "weather": "snow",
        "visibility": "snow",
        "desc": "Extreme ice skidding. Survive the final frozen stretch."
    }
}

SAVE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "save.json")

class LevelManager:
    def __init__(self):
        self.unlocked_levels = [1]
        self.high_scores = {str(lvl): 0 for lvl in LEVELS.keys()}
        self.current_level_idx = 1
        self.load_progress()

    def get_current_level_config(self):
        return LEVELS[self.current_level_idx]

    def get_powerup_pool(self, level_idx=None):
        idx = level_idx if level_idx is not None else self.current_level_idx
        return LEVEL_POWERUP_POOLS.get(idx, LEVEL_POWERUP_POOLS[5])

    def calc_star_rating(self, score, level_idx=None):
        """Return 1–3 stars based on score vs level target (Phase 21)."""
        idx = level_idx if level_idx is not None else self.current_level_idx
        target = LEVELS[idx]["score_target"]
        if score >= target * 1.35:
            return 3
        if score >= target * 1.15:
            return 2
        return 1

    def load_progress(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                    self.unlocked_levels = data.get("unlocked_levels", [1])
                    # High scores dictionary (keys as strings for JSON compatibility)
                    scores = data.get("high_scores", data.get("scores", {}))
                    for k, v in scores.items():
                        if k in self.high_scores:
                            self.high_scores[k] = v
            except Exception as e:
                print(f"Error loading level progress: {e}")
                self.unlocked_levels = [1]

    def save_progress(self):
        try:
            data = {
                "unlocked_levels": self.unlocked_levels,
                "high_scores": self.high_scores
            }
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving level progress: {e}")

    def unlock_next_level(self):
        next_lvl = self.current_level_idx + 1
        if next_lvl in LEVELS:
            if next_lvl not in self.unlocked_levels:
                self.unlocked_levels.append(next_lvl)
                self.unlocked_levels.sort()
                self.save_progress()
            return True
        return False # Completed the last level!

    def update_high_score(self, level_idx, score):
        lvl_str = str(level_idx)
        score_int = int(score)
        if lvl_str in self.high_scores:
            if score_int > self.high_scores[lvl_str]:
                self.high_scores[lvl_str] = score_int
                self.save_progress()
                return True
        return False

    def reset_progress(self):
        self.unlocked_levels = [1]
        self.high_scores = {str(lvl): 0 for lvl in LEVELS.keys()}
        self.current_level_idx = 1
        self.save_progress()

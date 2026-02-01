"""
Global game settings and constants.

This module contains all configurable values for the game.
Changing values here affects the entire game.
"""

import pygame
import os

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "Fractured Causality"

# =============================================================================
# TILE AND GRID SETTINGS
# =============================================================================

TILE_SIZE = 64
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# =============================================================================
# UNIVERSE SETTINGS
# =============================================================================

UNIVERSE_COUNT = 3
UNIVERSE_SWITCH_COOLDOWN = 0.5  # seconds

# Universe type identifiers
UNIVERSE_PRIME = "prime"
UNIVERSE_ECHO = "echo"
UNIVERSE_FRACTURE = "fracture"

# Universe colors (RGB)
UNIVERSE_COLORS = {
    UNIVERSE_PRIME: (100, 150, 255),     # Blue
    UNIVERSE_ECHO: (100, 255, 150),      # Green
    UNIVERSE_FRACTURE: (255, 100, 100),  # Red
}

# Universe background colors (darker versions)
UNIVERSE_BG_COLORS = {
    UNIVERSE_PRIME: (20, 30, 50),
    UNIVERSE_ECHO: (20, 50, 30),
    UNIVERSE_FRACTURE: (50, 20, 20),
}

# =============================================================================
# PLAYER SETTINGS
# =============================================================================

PLAYER_SPEED = 200  # pixels per second
PLAYER_SIZE = (48, 48)
PLAYER_INTERACTION_RANGE = 80

# =============================================================================
# PARADOX SETTINGS
# =============================================================================

PARADOX_MAX = 100
PARADOX_DECAY_RATE = 0.5  # per second when stable
PARADOX_DANGER_THRESHOLD = 75
PARADOX_CRITICAL_THRESHOLD = 50
PARADOX_UNSTABLE_THRESHOLD = 25

# Paradox level thresholds (percentage values)
PARADOX_STABLE = 25       # Below this = stable
PARADOX_UNSTABLE = 50     # 26-50 = unstable
PARADOX_CRITICAL = 75     # 51-75 = critical
PARADOX_COLLAPSE = 100    # 76-100 = collapse/annihilation

# Paradox tier thresholds
PARADOX_TIERS = {
    "stable": (0, 25),
    "unstable": (26, 50),
    "critical": (51, 75),
    "collapse": (76, 99),
    "annihilation": (100, 100),
}

# =============================================================================
# ENTITY PERSISTENCE TYPES
# =============================================================================

PERSISTENCE_ANCHORED = "anchored"    # Exists identically in all universes
PERSISTENCE_VARIANT = "variant"      # Different forms across universes
PERSISTENCE_EXCLUSIVE = "exclusive"  # Only in one universe

# =============================================================================
# COLORS
# =============================================================================

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)

COLOR_PLAYER = (255, 220, 100)
COLOR_WALL = (80, 80, 100)
COLOR_FLOOR = (40, 40, 50)
COLOR_DOOR_LOCKED = (150, 80, 80)
COLOR_DOOR_OPEN = (80, 150, 80)
COLOR_KEY = (255, 215, 0)
COLOR_PORTAL = (200, 100, 255)
COLOR_SWITCH_OFF = (100, 100, 100)
COLOR_SWITCH_ON = (100, 255, 100)

# Universe-specific colors (for UI and rendering)
COLOR_PRIME = (100, 150, 255)     # Blue - Prime universe
COLOR_ECHO = (100, 255, 150)      # Green - Echo universe
COLOR_FRACTURE = (255, 100, 100)  # Red - Fracture universe

# Causal visualization colors
COLOR_CAUSAL_LINE = (255, 200, 100)
COLOR_CAUSAL_ECHO = (100, 200, 255)
COLOR_CAUSAL_INVERSE = (255, 100, 100)
COLOR_PARADOX_GLOW = (255, 50, 50)

# =============================================================================
# UI SETTINGS
# =============================================================================

UI_FONT_SIZE = 24
UI_FONT_SIZE_LARGE = 36
UI_FONT_SIZE_SMALL = 16
UI_PADDING = 10
UI_MARGIN = 20

HUD_HEIGHT = 60
HUD_PARADOX_WIDTH = 200
HUD_PARADOX_HEIGHT = 20

# =============================================================================
# ANIMATION SETTINGS
# =============================================================================

ANIMATION_UNIVERSE_SWITCH_DURATION = 0.3
ANIMATION_CAUSAL_PROPAGATION_SPEED = 500  # pixels per second

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

DEBUG_MODE = False
DEBUG_SHOW_GRID = False
DEBUG_SHOW_COLLISIONS = False
DEBUG_SHOW_CAUSAL_GRAPH = False

# =============================================================================
# KEYBINDINGS
# =============================================================================

KEY_MOVE_UP = [pygame.K_w, pygame.K_UP]
KEY_MOVE_DOWN = [pygame.K_s, pygame.K_DOWN]
KEY_MOVE_LEFT = [pygame.K_a, pygame.K_LEFT]
KEY_MOVE_RIGHT = [pygame.K_d, pygame.K_RIGHT]

# Simpler aliases for input handler
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_SWITCH_UNIVERSE = pygame.K_SPACE

KEY_SWITCH_PRIME = pygame.K_1
KEY_SWITCH_ECHO = pygame.K_2
KEY_SWITCH_FRACTURE = pygame.K_3

KEY_INTERACT = pygame.K_e
KEY_ATTACK = pygame.K_f
KEY_CAUSAL_SIGHT = pygame.K_TAB
KEY_PARADOX_PULSE = pygame.K_SPACE
KEY_PAUSE = pygame.K_ESCAPE

# =============================================================================
# COMBAT SETTINGS
# =============================================================================

PLAYER_MAX_HEALTH = 100
PLAYER_ATTACK_DAMAGE = 25
PLAYER_ATTACK_RANGE = 60
PLAYER_ATTACK_COOLDOWN = 0.5
PLAYER_INVINCIBILITY_TIME = 1.0

ENEMY_BASE_DAMAGE = 10
ENEMY_KNOCKBACK_FORCE = 150

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SAVES_DIR = os.path.join(BASE_DIR, "saves")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

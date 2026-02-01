"""
Paradox Manager - Tracks and applies paradox effects.

Paradox is the consequence of breaking causality. It's both a threat
and a resource - some puzzles require paradox to solve.
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from ..core.settings import (
    PARADOX_MAX, PARADOX_TIERS, PARADOX_DECAY_RATE,
    PARADOX_DANGER_THRESHOLD, PARADOX_CRITICAL_THRESHOLD
)
from ..core.events import EventSystem, GameEvent


class ParadoxTier(Enum):
    """Tiers of paradox intensity."""
    STABLE = "stable"
    UNSTABLE = "unstable"
    CRITICAL = "critical"
    COLLAPSE = "collapse"
    ANNIHILATION = "annihilation"


@dataclass
class ParadoxSource:
    """Tracks a source of paradox."""
    source_id: str
    source_type: str
    amount: float
    timestamp: float
    description: str = ""


class ParadoxManager:
    """
    Manages the paradox system.
    
    Paradox is a measure of causal instability. It increases when:
    - Causal dependencies are broken
    - Entities are orphaned
    - The player creates impossible states
    
    At different thresholds, paradox causes different effects:
    - Visual distortions
    - New traversal options (reality tears)
    - Enemy empowerment
    - Eventually: annihilation (game over)
    
    Paradox is also a resource:
    - Some doors only open at certain paradox levels
    - Some solutions require high paradox
    - The Paradox Pulse ability consumes paradox
    """
    
    def __init__(self):
        """Initialize the paradox manager."""
        self._level: float = 0.0
        self._max_level: float = PARADOX_MAX
        self._current_tier: ParadoxTier = ParadoxTier.STABLE
        
        # Track sources of paradox
        self._sources: List[ParadoxSource] = []
        
        # Time tracking for decay
        self._time_since_last_change: float = 0.0
        self._decay_paused: bool = False
        
        # Effects
        self._reality_tears_active: bool = False
        self._visual_distortion: float = 0.0
        
        # History for visualization
        self._history: List[Tuple[float, float]] = []  # (time, level)
        self._total_time: float = 0.0
    
    @property
    def level(self) -> float:
        """Get the current paradox level."""
        return self._level
    
    @property
    def level_normalized(self) -> float:
        """Get paradox level as 0-1 value."""
        return self._level / self._max_level
    
    @property
    def tier(self) -> ParadoxTier:
        """Get the current paradox tier."""
        return self._current_tier
    
    @property
    def is_dangerous(self) -> bool:
        """Check if paradox is at a dangerous level."""
        return self._level >= PARADOX_CRITICAL_THRESHOLD
    
    @property
    def reality_tears_active(self) -> bool:
        """Check if reality tears are currently active."""
        return self._reality_tears_active
    
    def add_paradox(self, amount: float, source_id: str = "unknown",
                    source_type: str = "unknown", description: str = "") -> float:
        """
        Add paradox to the system.
        
        Args:
            amount: Amount of paradox to add
            source_id: ID of the source entity/event
            source_type: Type of source (e.g., "causal_break", "orphan")
            description: Human-readable description
            
        Returns:
            New paradox level
        """
        old_level = self._level
        self._level = min(self._max_level, self._level + amount)
        
        # Track source
        source = ParadoxSource(
            source_id=source_id,
            source_type=source_type,
            amount=amount,
            timestamp=self._total_time,
            description=description
        )
        self._sources.append(source)
        
        # Keep only recent sources
        if len(self._sources) > 50:
            self._sources = self._sources[-50:]
        
        # Reset decay timer
        self._time_since_last_change = 0.0
        
        # Check for tier change
        self._update_tier()
        
        # Record history
        self._history.append((self._total_time, self._level))
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
        # Emit event
        EventSystem.emit(GameEvent.PARADOX_CHANGED, {
            "old_level": old_level,
            "new_level": self._level,
            "change": amount,
            "source": source_id,
            "tier": self._current_tier.value
        })
        
        # Check for critical thresholds
        if self._level >= PARADOX_MAX:
            EventSystem.emit(GameEvent.PARADOX_ANNIHILATION, {})
        elif self._level >= PARADOX_DANGER_THRESHOLD and old_level < PARADOX_DANGER_THRESHOLD:
            EventSystem.emit(GameEvent.PARADOX_CRITICAL, {
                "level": self._level
            })
        
        return self._level
    
    def reduce_paradox(self, amount: float, reason: str = "decay") -> float:
        """
        Reduce paradox.
        
        Args:
            amount: Amount to reduce
            reason: Why paradox is being reduced
            
        Returns:
            New paradox level
        """
        old_level = self._level
        self._level = max(0, self._level - amount)
        
        self._update_tier()
        
        if old_level != self._level:
            EventSystem.emit(GameEvent.PARADOX_CHANGED, {
                "old_level": old_level,
                "new_level": self._level,
                "change": -amount,
                "source": reason,
                "tier": self._current_tier.value
            })
        
        return self._level
    
    def set_paradox(self, level: float) -> None:
        """Set paradox to a specific level."""
        old_level = self._level
        self._level = max(0, min(self._max_level, level))
        self._update_tier()
        
        EventSystem.emit(GameEvent.PARADOX_CHANGED, {
            "old_level": old_level,
            "new_level": self._level,
            "change": self._level - old_level,
            "source": "set",
            "tier": self._current_tier.value
        })
    
    def _update_tier(self) -> None:
        """Update the current tier based on level."""
        old_tier = self._current_tier
        
        for tier_name, (low, high) in PARADOX_TIERS.items():
            if low <= self._level <= high:
                self._current_tier = ParadoxTier(tier_name)
                break
        
        # Update effects based on tier
        self._reality_tears_active = self._current_tier in (
            ParadoxTier.CRITICAL, ParadoxTier.COLLAPSE
        )
        
        # Calculate visual distortion
        if self._current_tier == ParadoxTier.STABLE:
            self._visual_distortion = 0.0
        elif self._current_tier == ParadoxTier.UNSTABLE:
            self._visual_distortion = 0.2
        elif self._current_tier == ParadoxTier.CRITICAL:
            self._visual_distortion = 0.5
        elif self._current_tier == ParadoxTier.COLLAPSE:
            self._visual_distortion = 0.8
        else:
            self._visual_distortion = 1.0
        
        if old_tier != self._current_tier:
            EventSystem.emit(GameEvent.PARADOX_TIER_CHANGED, {
                "old_tier": old_tier.value,
                "new_tier": self._current_tier.value,
                "level": self._level
            })
    
    def update(self, dt: float) -> None:
        """
        Update paradox (handles decay).
        
        Args:
            dt: Delta time in seconds
        """
        self._total_time += dt
        self._time_since_last_change += dt
        
        # Decay paradox over time if stable
        if not self._decay_paused and self._level > 0:
            # Decay starts after 2 seconds of no changes
            if self._time_since_last_change > 2.0:
                decay = PARADOX_DECAY_RATE * dt
                self.reduce_paradox(decay, "natural_decay")
    
    def pause_decay(self) -> None:
        """Pause paradox decay."""
        self._decay_paused = True
    
    def resume_decay(self) -> None:
        """Resume paradox decay."""
        self._decay_paused = False
    
    def consume_paradox(self, amount: float) -> bool:
        """
        Try to consume paradox for an ability.
        
        Args:
            amount: Amount needed
            
        Returns:
            True if consumed, False if not enough
        """
        if self._level >= amount:
            self.reduce_paradox(amount, "consumed")
            return True
        return False
    
    def get_effects(self) -> Dict[str, any]:
        """
        Get current paradox effects for rendering/gameplay.
        
        Returns:
            Dictionary of active effects
        """
        return {
            "tier": self._current_tier,
            "visual_distortion": self._visual_distortion,
            "reality_tears": self._reality_tears_active,
            "screen_shake": self._current_tier in (ParadoxTier.CRITICAL, ParadoxTier.COLLAPSE),
            "color_shift": self._visual_distortion * 0.3,
            "glitch_intensity": self._visual_distortion
        }
    
    def get_recent_sources(self, count: int = 5) -> List[ParadoxSource]:
        """Get recent paradox sources."""
        return self._sources[-count:]
    
    def get_tier_thresholds(self) -> Dict[ParadoxTier, Tuple[float, float]]:
        """Get tier threshold values."""
        return {
            ParadoxTier(name): (low, high)
            for name, (low, high) in PARADOX_TIERS.items()
        }
    
    def reset(self) -> None:
        """Reset paradox to zero."""
        self._level = 0.0
        self._current_tier = ParadoxTier.STABLE
        self._sources.clear()
        self._time_since_last_change = 0.0
        self._reality_tears_active = False
        self._visual_distortion = 0.0
        self._history.clear()
    
    def serialize(self) -> dict:
        """Serialize for saving."""
        return {
            "level": self._level,
            "sources": [
                {
                    "source_id": s.source_id,
                    "source_type": s.source_type,
                    "amount": s.amount,
                    "timestamp": s.timestamp
                }
                for s in self._sources[-10:]
            ]
        }
    
    def deserialize(self, data: dict) -> None:
        """Deserialize from save data."""
        self._level = data.get("level", 0.0)
        self._update_tier()
        # Sources not fully restored, just level matters

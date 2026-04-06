from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from ..core.settings import (
    PARADOX_MAX, PARADOX_TIERS, PARADOX_DECAY_RATE,
    PARADOX_DANGER_THRESHOLD, PARADOX_CRITICAL_THRESHOLD
)
from ..core.events import EventSystem, GameEvent


class ParadoxTier(Enum):
                                     
    STABLE = "stable"
    UNSTABLE = "unstable"
    CRITICAL = "critical"
    COLLAPSE = "collapse"
    ANNIHILATION = "annihilation"


@dataclass
class ParadoxSource:
                                     
    source_id: str
    source_type: str
    amount: float
    timestamp: float
    description: str = ""


class ParadoxManager:
    
    def __init__(self):
                                             
        self._level: float = 0.0
        self._max_level: float = PARADOX_MAX
        self._current_tier: ParadoxTier = ParadoxTier.STABLE
        
                                  
        self._sources: List[ParadoxSource] = []
        
                                 
        self._time_since_last_change: float = 0.0
        self._decay_paused: bool = False
        
                 
        self._reality_tears_active: bool = False
        self._visual_distortion: float = 0.0
        
                                   
        self._history: List[Tuple[float, float]] = []                 
        self._total_time: float = 0.0
    
    @property
    def level(self) -> float:
                                            
        return self._level
    
    @property
    def level_normalized(self) -> float:
                                             
        return self._level / self._max_level
    
    @property
    def tier(self) -> ParadoxTier:
                                           
        return self._current_tier
    
    @property
    def is_dangerous(self) -> bool:
                                                       
        return self._level >= PARADOX_CRITICAL_THRESHOLD
    
    @property
    def reality_tears_active(self) -> bool:
                                                          
        return self._reality_tears_active
    
    def add_paradox(self, amount: float, source_id: str = "unknown",
                    source_type: str = "unknown", description: str = "") -> float:
           
        old_level = self._level
        self._level = min(self._max_level, self._level + amount)
        
                      
        source = ParadoxSource(
            source_id=source_id,
            source_type=source_type,
            amount=amount,
            timestamp=self._total_time,
            description=description
        )
        self._sources.append(source)
        
                                  
        if len(self._sources) > 50:
            self._sources = self._sources[-50:]
        
                           
        self._time_since_last_change = 0.0
        
                               
        self._update_tier()
        
                        
        self._history.append((self._total_time, self._level))
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
                    
        EventSystem.emit(GameEvent.PARADOX_CHANGED, {
            "level": self._level,
            "old_level": old_level,
            "new_level": self._level,
            "amount": amount,
            "change": amount,
            "source": source_id,
            "tier": self._current_tier.value
        })
        
                                       
        if self._level >= PARADOX_MAX:
            EventSystem.emit(GameEvent.PARADOX_ANNIHILATION, {})
        elif self._level >= PARADOX_DANGER_THRESHOLD and old_level < PARADOX_DANGER_THRESHOLD:
            EventSystem.emit(GameEvent.PARADOX_CRITICAL, {
                "level": self._level
            })
        
        return self._level
    
    def reduce_paradox(self, amount: float, reason: str = "decay") -> float:
           
        old_level = self._level
        self._level = max(0, self._level - amount)
        
        self._update_tier()
        
        if old_level != self._level:
            EventSystem.emit(GameEvent.PARADOX_CHANGED, {
                "level": self._level,
                "old_level": old_level,
                "new_level": self._level,
                "amount": -amount,
                "change": -amount,
                "source": reason,
                "tier": self._current_tier.value
            })
        
        return self._level
    
    def set_paradox(self, level: float) -> None:
                                              
        old_level = self._level
        self._level = max(0, min(self._max_level, level))
        self._update_tier()
        
        EventSystem.emit(GameEvent.PARADOX_CHANGED, {
            "level": self._level,
            "old_level": old_level,
            "new_level": self._level,
            "amount": self._level - old_level,
            "change": self._level - old_level,
            "source": "set",
            "tier": self._current_tier.value
        })
    
    def _update_tier(self) -> None:
                                                     
        old_tier = self._current_tier
        
        for tier_name, (low, high) in PARADOX_TIERS.items():
            if low <= self._level <= high:
                self._current_tier = ParadoxTier(tier_name)
                break
        
                                      
        self._reality_tears_active = self._current_tier in (
            ParadoxTier.CRITICAL, ParadoxTier.COLLAPSE
        )
        
                                     
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
           
        self._total_time += dt
        self._time_since_last_change += dt
        
                                           
        if not self._decay_paused and self._level > 0:
                                                        
            if self._time_since_last_change > 2.0:
                decay = PARADOX_DECAY_RATE * dt
                self.reduce_paradox(decay, "natural_decay")
    
    def pause_decay(self) -> None:
                                  
        self._decay_paused = True
    
    def resume_decay(self) -> None:
                                   
        self._decay_paused = False
    
    def consume_paradox(self, amount: float) -> bool:
           
        if self._level >= amount:
            self.reduce_paradox(amount, "consumed")
            return True
        return False
    
    def get_effects(self) -> Dict[str, any]:
           
        return {
            "tier": self._current_tier,
            "visual_distortion": self._visual_distortion,
            "reality_tears": self._reality_tears_active,
            "screen_shake": self._current_tier in (ParadoxTier.CRITICAL, ParadoxTier.COLLAPSE),
            "color_shift": self._visual_distortion * 0.3,
            "glitch_intensity": self._visual_distortion
        }
    
    def get_recent_sources(self, count: int = 5) -> List[ParadoxSource]:
                                         
        return self._sources[-count:]
    
    def get_tier_thresholds(self) -> Dict[ParadoxTier, Tuple[float, float]]:
                                        
        return {
            ParadoxTier(name): (low, high)
            for name, (low, high) in PARADOX_TIERS.items()
        }
    
    def reset(self) -> None:
                                    
        self._level = 0.0
        self._current_tier = ParadoxTier.STABLE
        self._sources.clear()
        self._time_since_last_change = 0.0
        self._reality_tears_active = False
        self._visual_distortion = 0.0
        self._history.clear()
    
    def serialize(self) -> dict:
                                   
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
                                         
        self._level = data.get("level", 0.0)
        self._update_tier()
                                                        

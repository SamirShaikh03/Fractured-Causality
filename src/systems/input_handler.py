   

import pygame
from typing import Dict, Set, Callable, List
from dataclasses import dataclass
from enum import Enum, auto

from ..core.settings import (
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
    KEY_INTERACT, KEY_ATTACK, KEY_SWITCH_UNIVERSE, KEY_CAUSAL_SIGHT,
    KEY_PARADOX_PULSE, KEY_PAUSE
)
from ..core.events import EventSystem, GameEvent


class InputAction(Enum):
                                     
              
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    
             
    INTERACT = auto()
    ATTACK = auto()
    SWITCH_UNIVERSE = auto()
    CAUSAL_SIGHT = auto()
    PARADOX_PULSE = auto()
    
        
    PAUSE = auto()
    CONFIRM = auto()
    CANCEL = auto()
    
                      
    DEBUG_TOGGLE = auto()


@dataclass
class InputState:
                                      
                        
    move_x: float = 0.0
    move_y: float = 0.0
    
                   
    buttons_held: Set[InputAction] = None
    buttons_pressed: Set[InputAction] = None
    buttons_released: Set[InputAction] = None
    
    def __post_init__(self):
        if self.buttons_held is None:
            self.buttons_held = set()
        if self.buttons_pressed is None:
            self.buttons_pressed = set()
        if self.buttons_released is None:
            self.buttons_released = set()


class InputHandler:
       
    
    def __init__(self):
                                           
                                              
        self._bindings: Dict[InputAction, List[int]] = {
            InputAction.MOVE_UP: [KEY_UP, pygame.K_w],
            InputAction.MOVE_DOWN: [KEY_DOWN, pygame.K_s],
            InputAction.MOVE_LEFT: [KEY_LEFT, pygame.K_a],
            InputAction.MOVE_RIGHT: [KEY_RIGHT, pygame.K_d],
            InputAction.INTERACT: [KEY_INTERACT],
            InputAction.ATTACK: [KEY_ATTACK],
            InputAction.SWITCH_UNIVERSE: [KEY_SWITCH_UNIVERSE],
            InputAction.CAUSAL_SIGHT: [KEY_CAUSAL_SIGHT],
            InputAction.PARADOX_PULSE: [KEY_PARADOX_PULSE],
            InputAction.PAUSE: [KEY_PAUSE],
            InputAction.CONFIRM: [pygame.K_RETURN, pygame.K_SPACE],
            InputAction.CANCEL: [pygame.K_ESCAPE],
            InputAction.DEBUG_TOGGLE: [pygame.K_F3],
        }
        
                                        
        self._key_to_action: Dict[int, InputAction] = {}
        self._rebuild_key_mapping()
        
                       
        self._current_state = InputState()
        self._previous_state = InputState()
        
                                                   
        self._input_buffer: List[InputAction] = []
        self._buffer_duration: float = 0.1           
        self._buffer_timers: Dict[InputAction, float] = {}
        
                       
        self._enabled: bool = True
    
    def _rebuild_key_mapping(self) -> None:
                                                
        self._key_to_action.clear()
        for action, keys in self._bindings.items():
            for key in keys:
                self._key_to_action[key] = action
    
    def bind_key(self, action: InputAction, key: int) -> None:
           
        if key not in self._bindings[action]:
            self._bindings[action].append(key)
            self._rebuild_key_mapping()
    
    def unbind_key(self, action: InputAction, key: int) -> None:
           
        if key in self._bindings[action]:
            self._bindings[action].remove(key)
            self._rebuild_key_mapping()
    
    def update(self, dt: float) -> InputState:
           
        if not self._enabled:
            return InputState()
        
                             
        self._previous_state = InputState(
            move_x=self._current_state.move_x,
            move_y=self._current_state.move_y,
            buttons_held=set(self._current_state.buttons_held),
            buttons_pressed=set(),
            buttons_released=set()
        )
        
                                
        self._current_state.buttons_pressed.clear()
        self._current_state.buttons_released.clear()
        
                            
        keys = pygame.key.get_pressed()
        
                         
        self._current_state.move_x = 0.0
        self._current_state.move_y = 0.0
        
        if self._is_action_held(keys, InputAction.MOVE_LEFT):
            self._current_state.move_x -= 1.0
        if self._is_action_held(keys, InputAction.MOVE_RIGHT):
            self._current_state.move_x += 1.0
        if self._is_action_held(keys, InputAction.MOVE_UP):
            self._current_state.move_y -= 1.0
        if self._is_action_held(keys, InputAction.MOVE_DOWN):
            self._current_state.move_y += 1.0
        
                                     
        if self._current_state.move_x != 0 and self._current_state.move_y != 0:
            self._current_state.move_x *= 0.7071             
            self._current_state.move_y *= 0.7071
        
                             
        for action in InputAction:
            is_held = self._is_action_held(keys, action)
            was_held = action in self._previous_state.buttons_held
            
            if is_held and not was_held:
                              
                self._current_state.buttons_pressed.add(action)
                self._current_state.buttons_held.add(action)
                self._add_to_buffer(action)
                
            elif is_held and was_held:
                            
                self._current_state.buttons_held.add(action)
                
            elif not is_held and was_held:
                               
                self._current_state.buttons_released.add(action)
                self._current_state.buttons_held.discard(action)
        
                                    
        expired = []
        for action, timer in self._buffer_timers.items():
            self._buffer_timers[action] = timer - dt
            if self._buffer_timers[action] <= 0:
                expired.append(action)
        
        for action in expired:
            del self._buffer_timers[action]
            if action in self._input_buffer:
                self._input_buffer.remove(action)
        
        return self._current_state
    
    def _is_action_held(self, keys, action: InputAction) -> bool:
                                                     
        for key in self._bindings.get(action, []):
            if keys[key]:
                return True
        return False
    
    def _add_to_buffer(self, action: InputAction) -> None:
                                                
        if action not in self._input_buffer:
            self._input_buffer.append(action)
            self._buffer_timers[action] = self._buffer_duration
    
    def consume_buffered(self, action: InputAction) -> bool:
           
        if action in self._input_buffer:
            self._input_buffer.remove(action)
            if action in self._buffer_timers:
                del self._buffer_timers[action]
            return True
        return False
    
    def is_pressed(self, action: InputAction) -> bool:
                                                          
        return action in self._current_state.buttons_pressed
    
    def is_held(self, action: InputAction) -> bool:
                                                
        return action in self._current_state.buttons_held
    
    def is_released(self, action: InputAction) -> bool:
                                                           
        return action in self._current_state.buttons_released
    
    def get_movement(self) -> tuple:
                                  
        return (self._current_state.move_x, self._current_state.move_y)
    
    def enable(self) -> None:
                                      
        self._enabled = True
    
    def disable(self) -> None:
                                       
        self._enabled = False
        self._current_state = InputState()
    
    def is_enabled(self) -> bool:
                                        
        return self._enabled

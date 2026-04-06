   

import pygame
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class AnimationFrame:
                                      
    surface: pygame.Surface
    duration: float                       
    offset: Tuple[int, int] = (0, 0)                 
    event: str = None                             


@dataclass
class Animation:
                                
    name: str
    frames: List[AnimationFrame]
    loop: bool = True
    next_animation: str = None                                            
    
    def get_duration(self) -> float:
                                           
        return sum(f.duration for f in self.frames)


class AnimationState(Enum):
                                  
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    ATTACK = "attack"
    HURT = "hurt"
    DEATH = "death"
    INTERACT = "interact"
    SPECIAL = "special"


class AnimationPlayer:
       
    
    def __init__(self):
                                              
                               
        self._animations: Dict[str, Animation] = {}
        
                       
        self._current_animation: Optional[Animation] = None
        self._current_frame_index: int = 0
        self._frame_timer: float = 0.0
        self._is_playing: bool = False
        self._is_finished: bool = False
        
                          
        self.speed: float = 1.0
        
                                  
        self.facing_right: bool = True
        
                   
        self._on_frame: Optional[Callable[[AnimationFrame], None]] = None
        self._on_animation_end: Optional[Callable[[str], None]] = None
    
    def add_animation(self, animation: Animation) -> None:
           
        self._animations[animation.name] = animation
    
    def create_animation(self, name: str, 
                        sprite_sheet: pygame.Surface,
                        frame_count: int,
                        frame_width: int,
                        frame_height: int,
                        frame_duration: float,
                        loop: bool = True,
                        row: int = 0) -> Animation:
           
        frames = []
        
        for i in range(frame_count):
                                             
            rect = pygame.Rect(
                i * frame_width,
                row * frame_height,
                frame_width,
                frame_height
            )
            
            frame_surface = pygame.Surface(
                (frame_width, frame_height),
                pygame.SRCALPHA
            )
            frame_surface.blit(sprite_sheet, (0, 0), rect)
            
            frames.append(AnimationFrame(
                surface=frame_surface,
                duration=frame_duration
            ))
        
        animation = Animation(name=name, frames=frames, loop=loop)
        self.add_animation(animation)
        
        return animation
    
    def create_simple_animation(self, name: str,
                               surfaces: List[pygame.Surface],
                               frame_duration: float,
                               loop: bool = True) -> Animation:
           
        frames = [
            AnimationFrame(surface=s, duration=frame_duration)
            for s in surfaces
        ]
        
        animation = Animation(name=name, frames=frames, loop=loop)
        self.add_animation(animation)
        
        return animation
    
    def play(self, name: str, restart: bool = False) -> bool:
           
        if name not in self._animations:
            return False
        
        animation = self._animations[name]
        
                                                 
        if self._current_animation == animation and not restart:
            return True
        
        self._current_animation = animation
        self._current_frame_index = 0
        self._frame_timer = 0.0
        self._is_playing = True
        self._is_finished = False
        
        return True
    
    def stop(self) -> None:
                                         
        self._is_playing = False
    
    def resume(self) -> None:
                                           
        self._is_playing = True
    
    def update(self, dt: float) -> None:
           
        if not self._is_playing or not self._current_animation:
            return
        
        if self._is_finished:
            return
        
                      
        self._frame_timer += dt * self.speed
        
                           
        frames = self._current_animation.frames
        if self._current_frame_index >= len(frames):
            return
        
        current_frame = frames[self._current_frame_index]
        
                                    
        while self._frame_timer >= current_frame.duration:
            self._frame_timer -= current_frame.duration
            
                                 
            if current_frame.event and self._on_frame:
                self._on_frame(current_frame)
            
                        
            self._current_frame_index += 1
            
            if self._current_frame_index >= len(frames):
                                    
                if self._current_animation.loop:
                    self._current_frame_index = 0
                else:
                    self._is_finished = True
                    self._current_frame_index = len(frames) - 1
                    
                                          
                    if self._on_animation_end:
                        self._on_animation_end(self._current_animation.name)
                    
                                                  
                    if self._current_animation.next_animation:
                        self.play(self._current_animation.next_animation)
                    
                    return
            
            current_frame = frames[self._current_frame_index]
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
           
        if not self._current_animation:
            return None
        
        frames = self._current_animation.frames
        if not frames or self._current_frame_index >= len(frames):
            return None
        
        surface = frames[self._current_frame_index].surface
        
                             
        if not self.facing_right:
            surface = pygame.transform.flip(surface, True, False)
        
        return surface
    
    def get_current_offset(self) -> Tuple[int, int]:
                                                    
        if not self._current_animation:
            return (0, 0)
        
        frames = self._current_animation.frames
        if not frames or self._current_frame_index >= len(frames):
            return (0, 0)
        
        return frames[self._current_frame_index].offset
    
    def is_playing(self, name: str = None) -> bool:
           
        if not self._is_playing:
            return False
        
        if name is None:
            return True
        
        return (self._current_animation and 
                self._current_animation.name == name)
    
    def is_finished(self) -> bool:
                                                     
        return self._is_finished
    
    def set_on_frame(self, callback: Callable[[AnimationFrame], None]) -> None:
                                           
        self._on_frame = callback
    
    def set_on_animation_end(self, callback: Callable[[str], None]) -> None:
                                             
        self._on_animation_end = callback


class AnimationSystem:
       
    
    def __init__(self):
                                              
                                    
        self._templates: Dict[str, Animation] = {}
        
                        
        self._players: List[AnimationPlayer] = []
    
    def create_player(self) -> AnimationPlayer:
           
        player = AnimationPlayer()
        self._players.append(player)
        return player
    
    def remove_player(self, player: AnimationPlayer) -> None:
                                         
        if player in self._players:
            self._players.remove(player)
    
    def register_template(self, animation: Animation) -> None:
           
        self._templates[animation.name] = animation
    
    def get_template(self, name: str) -> Optional[Animation]:
                                        
        return self._templates.get(name)
    
    def update(self, dt: float) -> None:
           
        for player in self._players:
            player.update(dt)
    
    def create_color_flash_frames(self, base_surface: pygame.Surface,
                                  flash_color: Tuple[int, int, int],
                                  frame_count: int = 4) -> List[pygame.Surface]:
           
        frames = []
        
        for i in range(frame_count):
                                              
            if i % 2 == 0:
                frames.append(base_surface.copy())
            else:
                                       
                flash_surface = base_surface.copy()
                flash_surface.fill(flash_color, special_flags=pygame.BLEND_ADD)
                frames.append(flash_surface)
        
        return frames

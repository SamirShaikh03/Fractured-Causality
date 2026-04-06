import pygame
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import time

from ..core.settings import get_ui_font


@dataclass
class DebugValue:
                                   
    name: str
    getter: Callable[[], Any]
    format_str: str = "{}"


class DebugOverlay:
       
    
    def __init__(self):
                                           
        pygame.font.init()
        self._font = get_ui_font(20)
        
               
        self._visible: bool = False
        self._values: Dict[str, DebugValue] = {}
        
                              
        self._frame_times: List[float] = []
        self._max_frame_samples: int = 60
        self._last_frame_time: float = time.time()
        
                            
        self._timers: Dict[str, float] = {}
        self._timer_starts: Dict[str, float] = {}
        
                      
        self._log_messages: List[str] = []
        self._max_log_messages: int = 10
    
    def toggle(self) -> bool:
                                
        self._visible = not self._visible
        return self._visible
    
    def show(self) -> None:
                               
        self._visible = True
    
    def hide(self) -> None:
                               
        self._visible = False
    
    def add_value(self, name: str, getter: Callable[[], Any],
                  format_str: str = "{}") -> None:
           
        self._values[name] = DebugValue(name, getter, format_str)
    
    def remove_value(self, name: str) -> None:
                                   
        if name in self._values:
            del self._values[name]
    
    def start_timer(self, name: str) -> None:
                                        
        self._timer_starts[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> float:
           
        if name in self._timer_starts:
            elapsed = (time.perf_counter() - self._timer_starts[name]) * 1000
            self._timers[name] = elapsed
            return elapsed
        return 0.0
    
    def log(self, message: str) -> None:
                                
        timestamp = time.strftime("%H:%M:%S")
        self._log_messages.append(f"[{timestamp}] {message}")
        
                          
        while len(self._log_messages) > self._max_log_messages:
            self._log_messages.pop(0)
    
    def update(self, dt: float) -> None:
                                       
                           
        current_time = time.time()
        frame_time = current_time - self._last_frame_time
        self._last_frame_time = current_time
        
        self._frame_times.append(frame_time)
        if len(self._frame_times) > self._max_frame_samples:
            self._frame_times.pop(0)
    
    def render(self, surface: pygame.Surface) -> None:
           
        if not self._visible:
            return
        
        x = 10
        y = 10
        line_height = 18
        
                     
        bg_width = 250
        bg_height = (len(self._values) + len(self._timers) + 
                    len(self._log_messages) + 5) * line_height + 20
        
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        surface.blit(bg_surface, (x - 5, y - 5))
        
               
        title = self._font.render("DEBUG OVERLAY", True, (255, 255, 0))
        surface.blit(title, (x, y))
        y += line_height + 5
        
             
        fps = self._calculate_fps()
        fps_color = (0, 255, 0) if fps >= 55 else (255, 255, 0) if fps >= 30 else (255, 0, 0)
        fps_text = self._font.render(f"FPS: {fps:.1f}", True, fps_color)
        surface.blit(fps_text, (x, y))
        y += line_height
        
                    
        avg_frame_time = sum(self._frame_times) / max(1, len(self._frame_times)) * 1000
        ft_text = self._font.render(f"Frame Time: {avg_frame_time:.2f}ms", True, (200, 200, 200))
        surface.blit(ft_text, (x, y))
        y += line_height
        
                   
        pygame.draw.line(surface, (100, 100, 100), (x, y), (x + bg_width - 10, y))
        y += 5
        
                       
        for value in self._values.values():
            try:
                val = value.getter()
                text = f"{value.name}: {value.format_str.format(val)}"
            except Exception as e:
                text = f"{value.name}: ERROR"
            
            label = self._font.render(text, True, (200, 200, 200))
            surface.blit(label, (x, y))
            y += line_height
        
                            
        if self._timers:
            y += 5
            timer_title = self._font.render("Performance:", True, (255, 200, 100))
            surface.blit(timer_title, (x, y))
            y += line_height
            
            for name, elapsed in self._timers.items():
                color = (0, 255, 0) if elapsed < 5 else (255, 255, 0) if elapsed < 16 else (255, 0, 0)
                text = self._font.render(f"  {name}: {elapsed:.2f}ms", True, color)
                surface.blit(text, (x, y))
                y += line_height
        
                      
        if self._log_messages:
            y += 5
            log_title = self._font.render("Log:", True, (100, 200, 255))
            surface.blit(log_title, (x, y))
            y += line_height
            
            for msg in self._log_messages[-5:]:               
                text = self._font.render(msg[:40], True, (180, 180, 180))
                surface.blit(text, (x, y))
                y += line_height
    
    def _calculate_fps(self) -> float:
                                    
        if not self._frame_times:
            return 0.0
        
        avg_frame_time = sum(self._frame_times) / len(self._frame_times)
        if avg_frame_time <= 0:
            return 0.0
        
        return 1.0 / avg_frame_time
    
    def get_fps(self) -> float:
                              
        return self._calculate_fps()
    
    def clear_log(self) -> None:
                                 
        self._log_messages.clear()
    
    def clear_timers(self) -> None:
                                       
        self._timers.clear()
        self._timer_starts.clear()


                                       
_debug_instance: DebugOverlay = None


def get_debug() -> DebugOverlay:
                                                
    global _debug_instance
    if _debug_instance is None:
        _debug_instance = DebugOverlay()
    return _debug_instance


def debug_log(message: str) -> None:
                                             
    get_debug().log(message)


def debug_timer_start(name: str) -> None:
                              
    get_debug().start_timer(name)


def debug_timer_stop(name: str) -> float:
                                                     
    return get_debug().stop_timer(name)

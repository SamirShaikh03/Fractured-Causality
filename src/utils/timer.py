from typing import Callable, Optional, List
from dataclasses import dataclass, field


@dataclass
class Timer:
       
    duration: float
    callback: Optional[Callable] = None
    loop: bool = False
    autostart: bool = True
    
                    
    _time_remaining: float = field(default=0.0, init=False)
    _is_running: bool = field(default=False, init=False)
    _is_complete: bool = field(default=False, init=False)
    
    def __post_init__(self):
        self._time_remaining = self.duration
        if self.autostart:
            self.start()
    
    def start(self) -> None:
                              
        self._is_running = True
        self._is_complete = False
        self._time_remaining = self.duration
    
    def stop(self) -> None:
                             
        self._is_running = False
    
    def pause(self) -> None:
                              
        self._is_running = False
    
    def resume(self) -> None:
                               
        if not self._is_complete:
            self._is_running = True
    
    def reset(self) -> None:
                                               
        self._time_remaining = self.duration
        self._is_complete = False
        self._is_running = False
    
    def update(self, dt: float) -> bool:
           
        if not self._is_running or self._is_complete:
            return False
        
        self._time_remaining -= dt
        
        if self._time_remaining <= 0:
            self._is_complete = True
            self._is_running = False
            
            if self.callback:
                self.callback()
            
            if self.loop:
                self._time_remaining = self.duration + self._time_remaining
                self._is_complete = False
                self._is_running = True
            
            return True
        
        return False
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def is_complete(self) -> bool:
        return self._is_complete
    
    @property
    def time_remaining(self) -> float:
        return max(0, self._time_remaining)
    
    @property
    def progress(self) -> float:
                                              
        if self.duration <= 0:
            return 1.0
        return 1.0 - (self._time_remaining / self.duration)


class Cooldown(Timer):
       
    
    def __init__(self, duration: float):
        super().__init__(duration=duration, autostart=False)
        self._is_complete = True               
    
    def is_ready(self) -> bool:
                                         
        return self._is_complete or not self._is_running
    
    def trigger(self) -> bool:
           
        if self.is_ready():
            self.start()
            self._is_complete = False
            return True
        return False


class TimerManager:
       
    
    def __init__(self):
        self._timers: dict = {}
        self._anonymous_timers: List[Timer] = []
    
    def add(self, name: str, timer: Timer) -> Timer:
           
        self._timers[name] = timer
        return timer
    
    def create(self, name: str, duration: float,
               callback: Callable = None,
               loop: bool = False) -> Timer:
           
        timer = Timer(
            duration=duration,
            callback=callback,
            loop=loop
        )
        return self.add(name, timer)
    
    def create_anonymous(self, duration: float,
                        callback: Callable = None) -> Timer:
           
        timer = Timer(
            duration=duration,
            callback=callback,
            loop=False
        )
        self._anonymous_timers.append(timer)
        return timer
    
    def get(self, name: str) -> Optional[Timer]:
                                  
        return self._timers.get(name)
    
    def remove(self, name: str) -> None:
                                     
        if name in self._timers:
            del self._timers[name]
    
    def update(self, dt: float) -> None:
           
                             
        for timer in self._timers.values():
            timer.update(dt)
        
                                                        
        for timer in self._anonymous_timers[:]:
            timer.update(dt)
            if timer.is_complete and not timer.loop:
                self._anonymous_timers.remove(timer)
    
    def clear(self) -> None:
                               
        self._timers.clear()
        self._anonymous_timers.clear()


def delay(duration: float, callback: Callable) -> Timer:
       
    return Timer(duration=duration, callback=callback)

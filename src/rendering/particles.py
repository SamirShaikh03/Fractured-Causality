"""
Particle System - Lightweight particle effects.

Handles simple particle effects for visual feedback.
"""

import pygame
import random
import math
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class Particle:
    """A single particle."""
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    size: float
    life: float
    max_life: float
    gravity: float = 0.0
    friction: float = 1.0
    fade: bool = True
    shrink: bool = True


@dataclass
class ParticleEmitter:
    """Configuration for a particle emitter."""
    x: float
    y: float
    rate: float  # Particles per second
    color: Tuple[int, int, int]
    color_variance: int = 20
    size_min: float = 2.0
    size_max: float = 6.0
    speed_min: float = 20.0
    speed_max: float = 80.0
    angle_min: float = 0.0  # In radians
    angle_max: float = 2 * math.pi
    life_min: float = 0.5
    life_max: float = 1.5
    gravity: float = 0.0
    friction: float = 0.98
    active: bool = True
    timer: float = 0.0
    duration: float = -1  # -1 = infinite


class ParticleSystem:
    """
    Manages particle effects.
    
    Features:
    - Multiple particle types
    - Emitters for continuous effects
    - Burst effects
    - Efficient batch rendering
    """
    
    def __init__(self, max_particles: int = 1000):
        """
        Initialize the particle system.
        
        Args:
            max_particles: Maximum simultaneous particles
        """
        self.max_particles = max_particles
        self._particles: List[Particle] = []
        self._emitters: List[ParticleEmitter] = []
    
    def spawn(self, x: float, y: float,
              color: Tuple[int, int, int],
              velocity: Tuple[float, float] = (0, 0),
              size: float = 4.0,
              life: float = 1.0,
              gravity: float = 0.0,
              friction: float = 1.0) -> Optional[Particle]:
        """
        Spawn a single particle.
        
        Args:
            x: X position
            y: Y position
            color: Particle color
            velocity: Initial velocity (vx, vy)
            size: Particle size
            life: Lifetime in seconds
            gravity: Gravity acceleration
            friction: Velocity friction
            
        Returns:
            The spawned particle, or None if at limit
        """
        if len(self._particles) >= self.max_particles:
            return None
        
        particle = Particle(
            x=x, y=y,
            vx=velocity[0], vy=velocity[1],
            color=color,
            size=size,
            life=life,
            max_life=life,
            gravity=gravity,
            friction=friction
        )
        
        self._particles.append(particle)
        return particle
    
    def burst(self, x: float, y: float,
              count: int,
              color: Tuple[int, int, int],
              speed_range: Tuple[float, float] = (30, 100),
              size_range: Tuple[float, float] = (2, 6),
              life_range: Tuple[float, float] = (0.3, 1.0),
              angle_range: Tuple[float, float] = (0, 2 * math.pi),
              gravity: float = 100,
              color_variance: int = 20) -> List[Particle]:
        """
        Spawn a burst of particles.
        
        Args:
            x: Center X position
            y: Center Y position
            count: Number of particles
            color: Base color
            speed_range: (min, max) speed
            size_range: (min, max) size
            life_range: (min, max) lifetime
            angle_range: (min, max) angle in radians
            gravity: Gravity for particles
            color_variance: Random color variance
            
        Returns:
            List of spawned particles
        """
        particles = []
        
        for _ in range(count):
            if len(self._particles) >= self.max_particles:
                break
            
            # Random angle and speed
            angle = random.uniform(*angle_range)
            speed = random.uniform(*speed_range)
            
            # Velocity
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # Random color variation
            r = max(0, min(255, color[0] + random.randint(-color_variance, color_variance)))
            g = max(0, min(255, color[1] + random.randint(-color_variance, color_variance)))
            b = max(0, min(255, color[2] + random.randint(-color_variance, color_variance)))
            
            particle = Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                vx=vx,
                vy=vy,
                color=(r, g, b),
                size=random.uniform(*size_range),
                life=random.uniform(*life_range),
                max_life=random.uniform(*life_range),
                gravity=gravity,
                friction=0.98
            )
            
            self._particles.append(particle)
            particles.append(particle)
        
        return particles
    
    def create_emitter(self, x: float, y: float,
                      rate: float,
                      color: Tuple[int, int, int],
                      **kwargs) -> ParticleEmitter:
        """
        Create a particle emitter.
        
        Args:
            x: Emitter X position
            y: Emitter Y position
            rate: Particles per second
            color: Base particle color
            **kwargs: Additional emitter settings
            
        Returns:
            The created emitter
        """
        emitter = ParticleEmitter(
            x=x, y=y,
            rate=rate,
            color=color,
            **kwargs
        )
        
        self._emitters.append(emitter)
        return emitter
    
    def remove_emitter(self, emitter: ParticleEmitter) -> None:
        """Remove an emitter."""
        if emitter in self._emitters:
            self._emitters.remove(emitter)
    
    def update(self, dt: float) -> None:
        """
        Update all particles and emitters.
        
        Args:
            dt: Delta time
        """
        # Update particles
        for particle in self._particles[:]:
            # Physics
            particle.vy += particle.gravity * dt
            particle.vx *= particle.friction
            particle.vy *= particle.friction
            
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            
            # Lifetime
            particle.life -= dt
            
            if particle.life <= 0:
                self._particles.remove(particle)
        
        # Update emitters
        for emitter in self._emitters[:]:
            if not emitter.active:
                continue
            
            # Check duration
            if emitter.duration > 0:
                emitter.duration -= dt
                if emitter.duration <= 0:
                    self._emitters.remove(emitter)
                    continue
            
            # Spawn particles
            emitter.timer += dt
            spawn_interval = 1.0 / emitter.rate if emitter.rate > 0 else float('inf')
            
            while emitter.timer >= spawn_interval:
                emitter.timer -= spawn_interval
                self._spawn_from_emitter(emitter)
    
    def _spawn_from_emitter(self, emitter: ParticleEmitter) -> None:
        """Spawn a particle from an emitter."""
        if len(self._particles) >= self.max_particles:
            return
        
        # Random values
        angle = random.uniform(emitter.angle_min, emitter.angle_max)
        speed = random.uniform(emitter.speed_min, emitter.speed_max)
        size = random.uniform(emitter.size_min, emitter.size_max)
        life = random.uniform(emitter.life_min, emitter.life_max)
        
        # Color with variance
        v = emitter.color_variance
        color = (
            max(0, min(255, emitter.color[0] + random.randint(-v, v))),
            max(0, min(255, emitter.color[1] + random.randint(-v, v))),
            max(0, min(255, emitter.color[2] + random.randint(-v, v)))
        )
        
        particle = Particle(
            x=emitter.x + random.uniform(-3, 3),
            y=emitter.y + random.uniform(-3, 3),
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed,
            color=color,
            size=size,
            life=life,
            max_life=life,
            gravity=emitter.gravity,
            friction=emitter.friction
        )
        
        self._particles.append(particle)
    
    def render(self, surface: pygame.Surface,
               camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Render all particles.
        
        Args:
            surface: Target surface
            camera_offset: Camera offset
        """
        ox, oy = camera_offset
        
        for particle in self._particles:
            # Calculate alpha based on life
            if particle.fade:
                alpha = int(255 * (particle.life / particle.max_life))
            else:
                alpha = 255
            
            # Calculate size
            if particle.shrink:
                size = particle.size * (particle.life / particle.max_life)
            else:
                size = particle.size
            
            size = max(1, int(size))
            
            # Screen position
            screen_x = int(particle.x - ox)
            screen_y = int(particle.y - oy)
            
            # Skip if off screen
            if (screen_x < -size or screen_x > surface.get_width() + size or
                screen_y < -size or screen_y > surface.get_height() + size):
                continue
            
            # Draw particle
            if alpha >= 250:
                # Full opacity - simple draw
                pygame.draw.circle(
                    surface,
                    particle.color,
                    (screen_x, screen_y),
                    size
                )
            else:
                # With alpha - need surface
                particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surface,
                    (*particle.color, alpha),
                    (size, size),
                    size
                )
                surface.blit(particle_surface, (screen_x - size, screen_y - size))
    
    def emit(self, x: float, y: float,
             count: int = 10,
             color: Tuple[int, int, int] = (255, 255, 255),
             speed: float = 80.0,
             lifetime: float = 0.8,
             size_range: Tuple[float, float] = (2, 6),
             gravity: float = 80,
             color_variance: int = 20) -> List[Particle]:
        """
        Emit a burst of particles (convenience wrapper).
        
        Args:
            x: Center X position
            y: Center Y position
            count: Number of particles
            color: Base color
            speed: Max speed of particles
            lifetime: Max lifetime of particles
            size_range: (min, max) size
            gravity: Gravity for particles
            color_variance: Random color variance
            
        Returns:
            List of spawned particles
        """
        return self.burst(
            x, y, count, color,
            speed_range=(speed * 0.3, speed),
            size_range=size_range,
            life_range=(lifetime * 0.3, lifetime),
            gravity=gravity,
            color_variance=color_variance
        )

    def clear(self) -> None:
        """Clear all particles and emitters."""
        self._particles.clear()
        self._emitters.clear()
    
    @property
    def particle_count(self) -> int:
        """Get current particle count."""
        return len(self._particles)
    
    @property
    def emitter_count(self) -> int:
        """Get current emitter count."""
        return len(self._emitters)

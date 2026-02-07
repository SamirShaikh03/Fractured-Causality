"""
Causal Sight Overlay - Visual overlay for causal sight ability.

Shows causal connections between entities when active.
"""

import pygame
import math
from typing import List, Tuple, Dict, Optional

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ..multiverse.causal_node import CausalNode, CausalOperator
from ..multiverse.causal_graph import CausalGraph


class CausalConnection:
    """Visual representation of a causal connection."""
    
    def __init__(self, source_pos: Tuple[float, float],
                 target_pos: Tuple[float, float],
                 operator: CausalOperator,
                 strength: float = 1.0):
        self.source_pos = source_pos
        self.target_pos = target_pos
        self.operator = operator
        self.strength = strength
        self.pulse: float = 0.0


class CausalSightOverlay:
    """
    Overlay that visualizes causal connections.
    
    When the player activates Causal Sight, this overlay:
    - Draws lines between causally connected entities
    - Colors lines based on the causal operator
    - Animates the flow of causality
    - Shows causal node information
    """
    
    def __init__(self):
        """Initialize the causal sight overlay."""
        pygame.font.init()
        self._font = pygame.font.Font(None, 18)
        
        # State
        self._active: bool = False
        self._fade: float = 0.0
        
        # Connections to render
        self._connections: List[CausalConnection] = []
        
        # Entity positions (updated each frame)
        self._entity_positions: Dict[str, Tuple[float, float]] = {}
        
        # Animation
        self._time: float = 0.0
        
        # Colors for different operators
        self._operator_colors: Dict[CausalOperator, Tuple[int, int, int]] = {
            CausalOperator.ECHO: (80, 200, 255),      # Cyan
            CausalOperator.INVERSE: (255, 100, 100),  # Red
            CausalOperator.CONDITIONAL: (200, 200, 80),  # Yellow
            CausalOperator.EXCLUSIVE: (200, 80, 200),  # Purple
            CausalOperator.CASCADE: (255, 180, 80),   # Orange
            CausalOperator.EXISTENCE: (80, 255, 150), # Green
        }
    
    def activate(self) -> None:
        """Activate causal sight."""
        self._active = True
    
    def deactivate(self) -> None:
        """Deactivate causal sight."""
        self._active = False
    
    def toggle(self) -> bool:
        """Toggle causal sight state."""
        self._active = not self._active
        return self._active
    
    def is_active(self) -> bool:
        """Check if causal sight is active."""
        return self._active
    
    def update_entity_position(self, entity_id: str, 
                               position: Tuple[float, float]) -> None:
        """
        Update an entity's position for rendering.
        
        Args:
            entity_id: Entity ID
            position: Screen position
        """
        self._entity_positions[entity_id] = position
    
    def set_connections_from_graph(self, causal_graph: CausalGraph,
                                   camera_offset: Tuple[int, int]) -> None:
        """
        Build connection list from causal graph.
        
        Args:
            causal_graph: The causal graph
            camera_offset: Camera offset for world-to-screen conversion
        """
        self._connections.clear()
        
        for node_id, node in causal_graph.nodes.items():
            source_pos = self._entity_positions.get(node_id)
            if not source_pos:
                continue
            
            for dep in node.dependencies:
                target_pos = self._entity_positions.get(dep.target_id)
                if not target_pos:
                    continue
                
                connection = CausalConnection(
                    source_pos=source_pos,
                    target_pos=target_pos,
                    operator=dep.operator,
                    strength=1.0
                )
                self._connections.append(connection)
    
    def update(self, dt: float) -> None:
        """
        Update overlay animations.
        
        Args:
            dt: Delta time
        """
        self._time += dt
        
        # Fade in/out
        if self._active:
            self._fade = min(1.0, self._fade + dt * 3.0)
        else:
            self._fade = max(0.0, self._fade - dt * 3.0)
        
        # Update connection pulses
        for conn in self._connections:
            conn.pulse += dt * 2.0
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the causal sight overlay.
        
        Args:
            surface: Target surface
        """
        if self._fade <= 0:
            return
        
        # Create overlay surface with alpha
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Darken background slightly
        bg_alpha = int(100 * self._fade)
        overlay.fill((0, 0, 40, bg_alpha))
        
        # Draw connections
        for connection in self._connections:
            self._draw_connection(overlay, connection)
        
        # Draw entity highlights
        for entity_id, pos in self._entity_positions.items():
            self._draw_entity_highlight(overlay, pos, entity_id)
        
        # Vignette effect
        self._draw_vignette(overlay)
        
        surface.blit(overlay, (0, 0))
    
    def _draw_connection(self, surface: pygame.Surface,
                        connection: CausalConnection) -> None:
        """Draw a causal connection line."""
        color = self._operator_colors.get(
            connection.operator, 
            (150, 150, 150)
        )
        
        # Apply fade
        alpha = int(200 * self._fade)
        
        source = connection.source_pos
        target = connection.target_pos
        
        # Calculate line direction
        dx = target[0] - source[0]
        dy = target[1] - source[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
        # Normalize
        dx /= length
        dy /= length
        
        # Draw animated dots along the line
        num_dots = max(3, int(length / 30))
        
        for i in range(num_dots):
            t = (i / num_dots + connection.pulse * 0.1) % 1.0
            
            x = source[0] + dx * length * t
            y = source[1] + dy * length * t
            
            # Size varies along the path
            size = int(3 + 2 * math.sin(t * math.pi))
            
            # Create dot with alpha
            pygame.draw.circle(
                surface, 
                (*color, alpha),
                (int(x), int(y)),
                size
            )
        
        # Draw thin connecting line
        pygame.draw.line(
            surface,
            (*color, alpha // 2),
            (int(source[0]), int(source[1])),
            (int(target[0]), int(target[1])),
            1
        )
        
        # Draw arrow at target
        arrow_size = 8
        angle = math.atan2(dy, dx)
        
        arrow_points = [
            (
                int(target[0] - 10 * dx),
                int(target[1] - 10 * dy)
            ),
            (
                int(target[0] - 10 * dx + arrow_size * math.cos(angle + 2.5)),
                int(target[1] - 10 * dy + arrow_size * math.sin(angle + 2.5))
            ),
            (
                int(target[0] - 10 * dx + arrow_size * math.cos(angle - 2.5)),
                int(target[1] - 10 * dy + arrow_size * math.sin(angle - 2.5))
            )
        ]
        pygame.draw.polygon(surface, (*color, alpha), arrow_points)
    
    def _draw_entity_highlight(self, surface: pygame.Surface,
                               position: Tuple[float, float],
                               entity_id: str) -> None:
        """Draw highlight around a causal entity."""
        x, y = int(position[0]), int(position[1])
        
        # Pulsing ring
        pulse = abs(math.sin(self._time * 2)) * 0.3 + 0.7
        radius = int(20 * pulse)
        alpha = int(150 * self._fade * pulse)
        
        pygame.draw.circle(
            surface,
            (180, 180, 255, alpha),
            (x, y),
            radius,
            2
        )
        
        # Entity ID label (for debugging/info)
        if self._fade > 0.5:
            # Shortened ID for display
            short_id = entity_id[:10] if len(entity_id) > 10 else entity_id
            label = self._font.render(short_id, True, (180, 180, 255))
            label.set_alpha(int(255 * self._fade))
            surface.blit(label, (x - label.get_width() // 2, y + 25))
    
    def _draw_vignette(self, surface: pygame.Surface) -> None:
        """Draw vignette effect around edges."""
        # Simple gradient vignette
        alpha = int(80 * self._fade)
        
        # Corner gradients
        corner_size = 200
        for corner in [(0, 0), (SCREEN_WIDTH, 0), 
                       (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT)]:
            for r in range(corner_size, 0, -10):
                ring_alpha = int(alpha * (1 - r / corner_size))
                pygame.draw.circle(
                    surface,
                    (0, 0, 40, ring_alpha),
                    corner,
                    r,
                    10
                )
    
    def render_legend(self, surface: pygame.Surface) -> None:
        """Render operator legend."""
        if self._fade < 0.5:
            return
        
        x, y = 20, SCREEN_HEIGHT - 150
        line_height = 20
        
        # Background
        legend_bg = pygame.Rect(x - 5, y - 5, 150, 130)
        pygame.draw.rect(surface, (20, 20, 40, int(200 * self._fade)),
                        legend_bg, border_radius=5)
        pygame.draw.rect(surface, (100, 100, 150, int(150 * self._fade)),
                        legend_bg, 1, border_radius=5)
        
        # Title
        title = self._font.render("CAUSAL OPERATORS", True, (200, 200, 255))
        title.set_alpha(int(255 * self._fade))
        surface.blit(title, (x, y))
        y += line_height + 5
        
        # Operators
        for operator, color in self._operator_colors.items():
            # Color dot
            pygame.draw.circle(surface, (*color, int(255 * self._fade)),
                             (x + 6, y + 6), 5)
            
            # Label
            label = self._font.render(operator.name, True, (180, 180, 180))
            label.set_alpha(int(255 * self._fade))
            surface.blit(label, (x + 18, y))
            
            y += line_height

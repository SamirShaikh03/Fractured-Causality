   

import pygame
import math
from typing import List, Tuple, Dict

from ..core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, get_ui_font
from ..multiverse.causal_node import CausalOperator
from ..multiverse.causal_graph import CausalGraph


class CausalConnection:
                                                       
    
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
       
    
    def __init__(self):
                                                  
        pygame.font.init()
        self._font = get_ui_font(18)
        
               
        self._active: bool = False
        self._fade: float = 0.0
        
                               
        self._connections: List[CausalConnection] = []
        
                                               
        self._entity_positions: Dict[str, Tuple[float, float]] = {}
        
                   
        self._time: float = 0.0
        
                                        
        self._operator_colors: Dict[CausalOperator, Tuple[int, int, int]] = {
            CausalOperator.ECHO: (80, 200, 255),            
            CausalOperator.INVERSE: (255, 100, 100),       
            CausalOperator.CONDITIONAL: (200, 200, 80),          
            CausalOperator.EXCLUSIVE: (200, 80, 200),          
            CausalOperator.CASCADE: (255, 180, 80),           
            CausalOperator.EXISTENCE: (80, 255, 150),        
        }

                                                                         
        self._overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    def activate(self) -> None:
                                    
        self._active = True
    
    def deactivate(self) -> None:
                                      
        self._active = False
    
    def toggle(self) -> bool:
                                        
        self._active = not self._active
        return self._active
    
    def is_active(self) -> bool:
                                              
        return self._active
    
    def update_entity_position(self, entity_id: str, 
                               position: Tuple[float, float]) -> None:
           
        self._entity_positions[entity_id] = position

    def clear_entity_positions(self) -> None:
                                                                                
        self._entity_positions.clear()
    
    def set_connections_from_graph(self, causal_graph: CausalGraph,
                                   camera_offset: Tuple[int, int]) -> None:
           
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
           
        self._time += dt
        
                     
        if self._active:
            self._fade = min(1.0, self._fade + dt * 3.0)
        else:
            self._fade = max(0.0, self._fade - dt * 3.0)
        
                                  
        for conn in self._connections:
            conn.pulse += dt * 2.0
    
    def render(self, surface: pygame.Surface) -> None:
           
        if self._fade <= 0:
            return

        overlay = self._overlay_surface
        overlay.fill((0, 0, 0, 0))
        
                                    
        bg_alpha = int(100 * self._fade)
        overlay.fill((0, 0, 40, bg_alpha))
        
                          
        for connection in self._connections:
            self._draw_connection(overlay, connection)
        
                                
        for entity_id, pos in self._entity_positions.items():
            self._draw_entity_highlight(overlay, pos, entity_id)
        
                         
        self._draw_vignette(overlay)
        
        surface.blit(overlay, (0, 0))
    
    def _draw_connection(self, surface: pygame.Surface,
                        connection: CausalConnection) -> None:
                                            
        color = self._operator_colors.get(
            connection.operator, 
            (150, 150, 150)
        )
        
                    
        alpha = int(200 * self._fade)
        
        source = connection.source_pos
        target = connection.target_pos
        
                                  
        dx = target[0] - source[0]
        dy = target[1] - source[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
                   
        dx /= length
        dy /= length
        
                                           
        num_dots = max(3, int(length / 30))
        
        for i in range(num_dots):
            t = (i / num_dots + connection.pulse * 0.1) % 1.0
            
            x = source[0] + dx * length * t
            y = source[1] + dy * length * t
            
                                        
            size = int(3 + 2 * math.sin(t * math.pi))
            
                                   
            pygame.draw.circle(
                surface, 
                (*color, alpha),
                (int(x), int(y)),
                size
            )
        
                                   
        pygame.draw.line(
            surface,
            (*color, alpha // 2),
            (int(source[0]), int(source[1])),
            (int(target[0]), int(target[1])),
            1
        )
        
                              
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
                                                    
        x, y = int(position[0]), int(position[1])
        
                      
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
        
                                              
        if self._fade > 0.5:
                                      
            short_id = entity_id[:10] if len(entity_id) > 10 else entity_id
            label = self._font.render(short_id, True, (180, 180, 255))
            label.set_alpha(int(255 * self._fade))
            surface.blit(label, (x - label.get_width() // 2, y + 25))
    
    def _draw_vignette(self, surface: pygame.Surface) -> None:
                                                
                                  
        alpha = int(80 * self._fade)
        
                          
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
                                     
        if self._fade < 0.5:
            return
        
        x, y = 20, SCREEN_HEIGHT - 150
        line_height = 20
        
                    
        legend_bg = pygame.Rect(x - 5, y - 5, 150, 130)
        pygame.draw.rect(surface, (20, 20, 40, int(200 * self._fade)),
                        legend_bg, border_radius=5)
        pygame.draw.rect(surface, (100, 100, 150, int(150 * self._fade)),
                        legend_bg, 1, border_radius=5)
        
               
        title = self._font.render("CAUSAL OPERATORS", True, (200, 200, 255))
        title.set_alpha(int(255 * self._fade))
        surface.blit(title, (x, y))
        y += line_height + 5
        
                   
        for operator, color in self._operator_colors.items():
                       
            pygame.draw.circle(surface, (*color, int(255 * self._fade)),
                             (x + 6, y + 6), 5)
            
                   
            label = self._font.render(operator.name, True, (180, 180, 180))
            label.set_alpha(int(255 * self._fade))
            surface.blit(label, (x + 18, y))
            
            y += line_height

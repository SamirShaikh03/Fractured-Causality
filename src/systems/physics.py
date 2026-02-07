"""
Physics System - Handles collision detection and resolution.

Provides tile-based and entity collision detection.
"""

import pygame
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..core.settings import TILE_SIZE
from ..multiverse.universe import Universe, TileType
from ..entities.entity import Entity


@dataclass
class CollisionResult:
    """Result of a collision check."""
    collided: bool = False
    tile_type: TileType = None
    entity: Entity = None
    normal: Tuple[float, float] = (0, 0)
    penetration: float = 0.0


class PhysicsSystem:
    """
    Handles all physics and collision detection.
    
    Features:
    - Tile-based collision
    - Entity-entity collision
    - AABB collision detection
    - Collision resolution
    """
    
    def __init__(self):
        """Initialize the physics system."""
        self._gravity: float = 0.0  # Top-down game, no gravity
    
    def check_tile_collision(self, x: float, y: float,
                            width: float, height: float,
                            universe: Universe) -> List[CollisionResult]:
        """
        Check collision against tiles.
        
        Args:
            x: Entity X position
            y: Entity Y position
            width: Entity width
            height: Entity height
            universe: Current universe
            
        Returns:
            List of collision results
        """
        results = []
        
        if not universe or not universe.tilemap:
            return results
        
        # Get tile bounds to check
        left_tile = max(0, int(x / TILE_SIZE))
        right_tile = min(universe.width - 1, int((x + width) / TILE_SIZE))
        top_tile = max(0, int(y / TILE_SIZE))
        bottom_tile = min(universe.height - 1, int((y + height) / TILE_SIZE))
        
        entity_rect = pygame.Rect(x, y, width, height)
        
        for ty in range(top_tile, bottom_tile + 1):
            for tx in range(left_tile, right_tile + 1):
                tile_type = universe.tilemap.get_tile(tx, ty)
                
                # Check if tile is solid
                if tile_type in [TileType.WALL, TileType.PIT]:
                    tile_rect = pygame.Rect(
                        tx * TILE_SIZE, ty * TILE_SIZE,
                        TILE_SIZE, TILE_SIZE
                    )
                    
                    if entity_rect.colliderect(tile_rect):
                        # Calculate collision normal and penetration
                        result = CollisionResult(
                            collided=True,
                            tile_type=tile_type
                        )
                        
                        # Determine collision direction
                        dx = (entity_rect.centerx - tile_rect.centerx)
                        dy = (entity_rect.centery - tile_rect.centery)
                        
                        if abs(dx) > abs(dy):
                            result.normal = (1 if dx > 0 else -1, 0)
                            result.penetration = (TILE_SIZE / 2 + width / 2) - abs(dx)
                        else:
                            result.normal = (0, 1 if dy > 0 else -1)
                            result.penetration = (TILE_SIZE / 2 + height / 2) - abs(dy)
                        
                        results.append(result)
        
        return results
    
    def check_entity_collision(self, entity: Entity,
                               other_entities: List[Entity]) -> List[CollisionResult]:
        """
        Check collision against other entities.
        
        Args:
            entity: The entity to check
            other_entities: List of other entities
            
        Returns:
            List of collision results
        """
        results = []
        
        entity_rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
        
        for other in other_entities:
            if other is entity:
                continue
            
            if not other.solid or not other.exists:
                continue
            
            other_rect = pygame.Rect(other.x, other.y, other.width, other.height)
            
            if entity_rect.colliderect(other_rect):
                result = CollisionResult(
                    collided=True,
                    entity=other
                )
                
                # Calculate collision normal
                dx = entity_rect.centerx - other_rect.centerx
                dy = entity_rect.centery - other_rect.centery
                
                if abs(dx) > abs(dy):
                    result.normal = (1 if dx > 0 else -1, 0)
                    result.penetration = (other.width / 2 + entity.width / 2) - abs(dx)
                else:
                    result.normal = (0, 1 if dy > 0 else -1)
                    result.penetration = (other.height / 2 + entity.height / 2) - abs(dy)
                
                results.append(result)
        
        return results
    
    def resolve_collision(self, entity: Entity,
                         collision: CollisionResult) -> Tuple[float, float]:
        """
        Resolve a collision by moving the entity out of penetration.
        
        Args:
            entity: The entity to resolve
            collision: The collision to resolve
            
        Returns:
            New position (x, y)
        """
        if not collision.collided:
            return (entity.x, entity.y)
        
        new_x = entity.x + collision.normal[0] * collision.penetration
        new_y = entity.y + collision.normal[1] * collision.penetration
        
        return (new_x, new_y)
    
    def move_and_slide(self, entity: Entity, velocity: Tuple[float, float],
                       universe: Universe, other_entities: List[Entity],
                       dt: float) -> Tuple[float, float]:
        """
        Move an entity and slide along obstacles.
        
        Args:
            entity: The entity to move
            velocity: Movement velocity (x, y)
            universe: Current universe
            other_entities: Other entities to check
            dt: Delta time
            
        Returns:
            Final position (x, y)
        """
        vx, vy = velocity
        
        # Move horizontally first
        new_x = entity.x + vx * dt
        entity.x = new_x
        
        # Check horizontal collisions
        h_collisions = self.check_tile_collision(
            new_x, entity.y, entity.width, entity.height, universe
        )
        h_collisions.extend(self.check_entity_collision(entity, other_entities))
        
        for collision in h_collisions:
            if collision.normal[0] != 0:
                new_x, _ = self.resolve_collision(entity, collision)
                entity.x = new_x
        
        # Move vertically
        new_y = entity.y + vy * dt
        entity.y = new_y
        
        # Check vertical collisions
        v_collisions = self.check_tile_collision(
            entity.x, new_y, entity.width, entity.height, universe
        )
        v_collisions.extend(self.check_entity_collision(entity, other_entities))
        
        for collision in v_collisions:
            if collision.normal[1] != 0:
                _, new_y = self.resolve_collision(entity, collision)
                entity.y = new_y
        
        return (entity.x, entity.y)
    
    def is_position_valid(self, x: float, y: float,
                         width: float, height: float,
                         universe: Universe,
                         other_entities: List[Entity] = None) -> bool:
        """
        Check if a position is valid (no collisions).
        
        Args:
            x: X position
            y: Y position
            width: Width
            height: Height
            universe: Current universe
            other_entities: Other entities to check
            
        Returns:
            True if position is valid
        """
        # Check tile collisions
        tile_collisions = self.check_tile_collision(x, y, width, height, universe)
        for collision in tile_collisions:
            if collision.tile_type == TileType.WALL:
                return False
        
        # Check entity collisions
        if other_entities:
            dummy = Entity.__new__(Entity)
            dummy.x = x
            dummy.y = y
            dummy.width = width
            dummy.height = height
            dummy.solid = True
            dummy.exists = True
            
            entity_collisions = self.check_entity_collision(dummy, other_entities)
            if entity_collisions:
                return False
        
        return True
    
    def raycast(self, start: Tuple[float, float],
                direction: Tuple[float, float],
                max_distance: float,
                universe: Universe) -> Optional[Tuple[float, float, TileType]]:
        """
        Cast a ray and find first intersection.
        
        Args:
            start: Starting position
            direction: Direction vector (normalized)
            max_distance: Maximum ray distance
            universe: Current universe
            
        Returns:
            (hit_x, hit_y, tile_type) or None
        """
        # Simple ray marching
        step = TILE_SIZE / 4
        distance = 0
        
        x, y = start
        dx, dy = direction
        
        while distance < max_distance:
            # Check current position
            tile_x = int(x / TILE_SIZE)
            tile_y = int(y / TILE_SIZE)
            
            if 0 <= tile_x < universe.width and 0 <= tile_y < universe.height:
                tile_type = universe.tilemap.get_tile(tile_x, tile_y)
                
                if tile_type == TileType.WALL:
                    return (x, y, tile_type)
            
            # Step forward
            x += dx * step
            y += dy * step
            distance += step
        
        return None
    
    def check_overlap(self, rect1: pygame.Rect, rect2: pygame.Rect) -> bool:
        """Check if two rectangles overlap."""
        return rect1.colliderect(rect2)
    
    def get_tile_at(self, x: float, y: float, universe: Universe) -> TileType:
        """Get the tile type at a world position."""
        tile_x = int(x / TILE_SIZE)
        tile_y = int(y / TILE_SIZE)
        
        if 0 <= tile_x < universe.width and 0 <= tile_y < universe.height:
            return universe.tilemap.get_tile(tile_x, tile_y)
        
        return TileType.WALL  # Out of bounds = wall

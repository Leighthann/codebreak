import random
import pygame
import math

class Resource:
    """Collectible resource that players can pick up."""
    
    def __init__(self, x, y, resource_type, amount=1, sprite=None):
        self.x = x
        self.y = y
        self.type = resource_type  # "code_fragments", "energy_cores", "data_shards"
        self.amount = amount
        self.sprite = sprite  # Optional sprite image
        self.width = 24
        self.height = 24
        
        # Visual properties
        self.pulse_timer = 0
        self.float_offset = 0
        self.base_y = y
        
        # Color coding by type
        self.colors = {
            "code_fragments": (0, 255, 255),      # Cyan
            "energy_cores": (255, 215, 0),        # Gold
            "data_shards": (255, 41, 117)         # Neon Pink
        }
        self.base_color = self.colors.get(resource_type, (255, 255, 255))
    
    def update(self, dt):
        """Update resource animation."""
        # Pulsing effect
        self.pulse_timer += dt * 5
        
        # Floating effect
        self.float_offset = math.sin(self.pulse_timer) * 3
        
    def draw(self, surface, camera_system=None):
        """Draw the resource with animated effects."""
        # Calculate screen position
        if camera_system:
            screen_x, screen_y = camera_system.apply(self.x, self.y + self.float_offset)
        else:
            screen_x = self.x
            screen_y = self.y + self.float_offset
        
        # If sprite is available, use it
        if self.sprite:
            # Apply floating offset and draw sprite
            sprite_x = int(screen_x)
            sprite_y = int(screen_y)
            
            # Pulsing scale effect
            pulse_scale = 1 + 0.1 * math.sin(self.pulse_timer)
            
            # Scale sprite for pulse effect
            scaled_width = int(self.sprite.get_width() * pulse_scale)
            scaled_height = int(self.sprite.get_height() * pulse_scale)
            scaled_sprite = pygame.transform.scale(self.sprite, (scaled_width, scaled_height))
            
            # Center the scaled sprite
            sprite_x -= (scaled_width - self.width) // 2
            sprite_y -= (scaled_height - self.height) // 2
            
            # Draw glow behind sprite
            glow_radius = int(self.width // 2 * pulse_scale) + 4
            glow_color = tuple(int(c * 0.3) for c in self.base_color)
            pygame.draw.circle(surface, glow_color, 
                             (int(screen_x + self.width // 2), 
                              int(screen_y + self.height // 2)), 
                             glow_radius)
            
            # Draw the sprite
            surface.blit(scaled_sprite, (sprite_x, sprite_y))
        else:
            # Fallback to procedural graphics if no sprite
            # Pulsing glow effect
            pulse_scale = 1 + 0.2 * math.sin(self.pulse_timer)
            glow_radius = int(self.width // 2 * pulse_scale)
            
            # Draw outer glow
            glow_color = tuple(int(c * 0.5) for c in self.base_color)
            pygame.draw.circle(surface, glow_color, 
                             (int(screen_x + self.width // 2), 
                              int(screen_y + self.height // 2)), 
                             glow_radius + 4)
            
            # Draw main resource shape based on type
            center_x = int(screen_x + self.width // 2)
            center_y = int(screen_y + self.height // 2)
            
            if self.type == "code_fragments":
                # Draw as a diamond/square
                points = [
                    (center_x, center_y - glow_radius),
                    (center_x + glow_radius, center_y),
                    (center_x, center_y + glow_radius),
                    (center_x - glow_radius, center_y)
                ]
                pygame.draw.polygon(surface, self.base_color, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 2)
                
            elif self.type == "energy_cores":
                # Draw as a circle
                pygame.draw.circle(surface, self.base_color, 
                                 (center_x, center_y), glow_radius)
                pygame.draw.circle(surface, (255, 255, 255), 
                                 (center_x, center_y), glow_radius, 2)
                # Inner glow
                pygame.draw.circle(surface, (255, 255, 255), 
                                 (center_x, center_y), glow_radius // 2)
                
            elif self.type == "data_shards":
                # Draw as a triangle
                points = [
                    (center_x, center_y - glow_radius),
                    (center_x + glow_radius, center_y + glow_radius // 2),
                    (center_x - glow_radius, center_y + glow_radius // 2)
                ]
                pygame.draw.polygon(surface, self.base_color, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 2)
    
    def get_rect(self):
        """Get collision rectangle for the resource."""
        return pygame.Rect(self.x, self.y, self.width, self.height)


class WorldObject:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type  # "console", "crate", "terminal", "debris"
        self.width = 32
        self.height = 32
        self.block_height = 32  # Actual 3D height of blocks
        self.interactable = type in ["console", "terminal"]
    
    def draw(self, surface, sprite=None):
        """Draw the object on the surface with true 3D effect."""
        if sprite:
            # Draw with provided sprite
            surface.blit(sprite, (self.x, self.y))
        else:
            # Get base color for the object type
            base_color = {
                "console": (0, 255, 255),  # Cyan
                "crate": (139, 69, 19),    # Brown
                "terminal": (0, 255, 0),   # Green
                "debris": (128, 128, 128)  # Gray
            }.get(self.type, (255, 255, 255))
            
            # Calculate lighter and darker shades for 3D effect
            def adjust_color(color, factor):
                return tuple(min(255, max(0, int(c * factor))) for c in color)
            
            lighter_color = adjust_color(base_color, 1.2)  # 20% lighter
            darker_color = adjust_color(base_color, 0.7)   # 30% darker
            
            # Calculate all faces of the 3D block
            front_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            
            # Top face points
            top_points = [
                (self.x, self.y),  # Front-left
                (self.x + self.width, self.y),  # Front-right
                (self.x + self.width, self.y - self.block_height),  # Back-right
                (self.x, self.y - self.block_height)  # Back-left
            ]
            
            # Left face points
            left_points = [
                (self.x, self.y),  # Front-top
                (self.x, self.y + self.height),  # Front-bottom
                (self.x, self.y + self.height - self.block_height),  # Back-bottom
                (self.x, self.y - self.block_height)  # Back-top
            ]
            
            # Draw faces in correct order (back to front)
            # Top face (lighter)
            pygame.draw.polygon(surface, lighter_color, top_points)
            
            # Left face (medium)
            pygame.draw.polygon(surface, darker_color, left_points)
            
            # Front face (normal)
            pygame.draw.rect(surface, base_color, front_rect)
    
    def collides_with(self, rect):
        """Check if object collides with a rectangle."""
        # Create collision rectangle for the solid block
        object_rect = pygame.Rect(
            self.x, 
            self.y,  # Use base y position for collision
            self.width, 
            self.height  # Use base height for collision
        )
        return object_rect.colliderect(rect)

    def get_height_at(self, x, y):
        """Get the height of the block at the given position."""
        if (self.x <= x <= self.x + self.width and 
            self.y <= y <= self.y + self.height):
            return self.block_height
        return 0

# Keep the original WorldObjects class for backward compatibility
class WorldObjects:
    def __init__(self):
        self.objects = []

    def generate_objects(self, world_map):
        """Randomly place objects in biomes."""
        for y in range(len(world_map)):
            for x in range(len(world_map[y])):
                biome = world_map[y][x]
                if biome == "forest" and random.random() < 0.1:  # 10% chance to spawn a tree
                    self.objects.append(("tree", x, y))
                elif biome == "desert" and random.random() < 0.05:  # 5% chance for cactus
                    self.objects.append(("cactus", x, y))
                elif biome == "mountain" and random.random() < 0.05:  # 5% chance for rock
                    self.objects.append(("rock", x, y))

    def draw_objects(self, screen, tile_size):
        """Render the objects in the world."""
        for obj, x, y in self.objects:
            if obj == "tree":
                pygame.draw.circle(screen, (34, 139, 34), (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2), 10)
            elif obj == "cactus":
                pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(x * tile_size + 8, y * tile_size + 8, 16, 24))
            elif obj == "rock":
                pygame.draw.circle(screen, (139, 137, 137), (x * tile_size + tile_size // 2, y * tile_size + tile_size // 2), 12)

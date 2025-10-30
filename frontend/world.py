import pygame
import random
from worldObject import WorldObject

class WorldGenerator:
    def __init__(self, width, height, tile_size):
        # World dimensions
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.block_height = 32  # Actual 3D height of blocks
        
        # Map representation
        self.map = []
        self.objects = []
        self.block_data = []  # Store block metadata for animations
        
        # Grid dimensions
        self.grid_width = width // tile_size
        self.grid_height = height // tile_size
        
        # Appearance
        self.bg_color = (10, 10, 25)  # Dark blue background
        self.grid_color = (30, 30, 60)  # Slightly lighter grid lines
        
        # Neon color palette for blocks
        self.neon_colors = [
            (0, 195, 255),    # NEON_BLUE
            (57, 255, 20),    # NEON_GREEN
            (255, 41, 117),   # NEON_PINK
            (191, 64, 191),   # NEON_PURPLE
            (255, 255, 0),    # YELLOW
            (0, 255, 255)     # CYAN
        ]
        
        # Animated background elements
        self.grid_offset_y = 0
        self.data_streams = []
        self.animation_timer = 0
        self.init_background_effects()
        
        # Generate world
        self.generate_map()
        self.place_objects()
    
    def init_background_effects(self):
        """Initialize animated background effects."""
        # Neon colors for data streams
        neon_colors = [
            (0, 195, 255),    # NEON_BLUE
            (57, 255, 20),    # NEON_GREEN
            (255, 41, 117)    # NEON_PINK
        ]
        
        # Create data streams
        for _ in range(10):
            self.data_streams.append({
                'x': random.randint(0, self.width),
                'y': random.randint(-500, 0),
                'speed': random.uniform(2, 5),
                'color': random.choice(neon_colors)
            })

    def generate_map(self):
        """Generate a grid-based map with cyberpunk data node blocks."""
        # Initialize empty map
        self.map = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.block_data = []  # Store metadata for each block
        
        # Add random obstacles (1 = obstacle, 0 = empty)
        obstacle_chance = 0.1  # Reduced from 15% to 10% for better movement
        blocks_created = 0
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Keep the center area clear for player spawn
                center_x = self.grid_width // 2
                center_y = self.grid_height // 2
                distance_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                
                # Increased clear area from 5 to 8 for better starting space
                if distance_from_center > 8 and random.random() < obstacle_chance:
                    self.map[y][x] = 1
                    blocks_created += 1
                    
                    # Assign cyberpunk properties to each block
                    block_color = random.choice(self.neon_colors)
                    self.block_data.append({
                        'x': x,
                        'y': y,
                        'color': block_color,
                        'pulse_offset': random.uniform(0, 360),  # For pulsing animation
                        'pulse_speed': random.uniform(0.02, 0.05),
                        'size': random.choice([1, 2, 3]),  # Small, medium, large nodes
                        'has_particles': random.random() < 0.3  # 30% have floating particles
                    })
        
        print(f"Generated {blocks_created} cyberpunk data blocks in world")

    def place_objects(self):
        """Place objects in the world."""
        # Clear existing objects
        self.objects = []
        
        # Types of objects with their probabilities
        object_types = ["console", "crate", "terminal", "debris"]
        probabilities = [0.2, 0.5, 0.2, 0.1]  # Sum must be 1.0
        
        # Number of objects to place
        num_objects = random.randint(10, 20)
        
        # Place objects
        for _ in range(num_objects):
            # Random position
            x = random.randint(1, self.grid_width - 2) * self.tile_size
            y = random.randint(1, self.grid_height - 2) * self.tile_size
            
            # Random type
            obj_type = random.choices(object_types, weights=probabilities, k=1)[0]
            
            # Create object
            new_object = WorldObject(x, y, obj_type)
            self.objects.append(new_object)

    def draw_map(self, surface):
        """Draw the world map with cyberpunk-styled 3D data node blocks."""
        # Fill background
        surface.fill(self.bg_color)
        
        # Draw animated background effects
        self.draw_animated_background(surface)
        
        # Update animation timer
        self.animation_timer += 1
        
        # Draw grid lines with slight glow
        for x in range(0, self.width, self.tile_size):
            pygame.draw.line(surface, self.grid_color, (x, 0), (x, self.height))
        for y in range(0, self.height, self.tile_size):
            pygame.draw.line(surface, self.grid_color, (0, y), (self.width, y))
        
        # Draw cyberpunk data node blocks
        # Draw from back to front to handle overlapping correctly
        for block in self.block_data:
            x = block['x']
            y = block['y']
            
            # Base coordinates
            base_x = x * self.tile_size
            base_y = y * self.tile_size
            
            # Calculate pulsing effect
            import math
            pulse_phase = (self.animation_timer * block['pulse_speed'] + block['pulse_offset']) % 360
            pulse_intensity = (math.sin(math.radians(pulse_phase)) + 1) / 2  # 0 to 1
            
            # Get base color and create lighter/darker variants
            base_color = block['color']
            
            # Create color variants for 3D effect
            top_color = tuple(min(255, int(c * (0.9 + pulse_intensity * 0.3))) for c in base_color)
            left_color = tuple(max(0, int(c * 0.6)) for c in base_color)
            front_color = tuple(max(0, int(c * 0.8)) for c in base_color)
            outline_color = tuple(min(255, int(c * 1.2)) for c in base_color)
            
            # Calculate all faces of the 3D block
            front_rect = pygame.Rect(base_x, base_y, self.tile_size, self.tile_size)
            
            # Top face points (drawn as a polygon)
            top_points = [
                (base_x, base_y),  # Front-left
                (base_x + self.tile_size, base_y),  # Front-right
                (base_x + self.tile_size, base_y - self.block_height),  # Back-right
                (base_x, base_y - self.block_height)  # Back-left
            ]
            
            # Left face points
            left_points = [
                (base_x, base_y),  # Front-top
                (base_x, base_y + self.tile_size),  # Front-bottom
                (base_x, base_y + self.tile_size - self.block_height),  # Back-bottom
                (base_x, base_y - self.block_height)  # Back-top
            ]
            
            # Draw glow effect behind block
            glow_size = int(10 + pulse_intensity * 15)
            glow_surf = pygame.Surface((self.tile_size + glow_size * 2, self.tile_size + glow_size * 2), pygame.SRCALPHA)
            for i in range(glow_size, 0, -1):
                alpha = int((pulse_intensity * 30) * (1 - i / glow_size))
                pygame.draw.rect(glow_surf, (*base_color, alpha), 
                               (glow_size - i, glow_size - i, self.tile_size + i*2, self.tile_size + i*2),
                               border_radius=5)
            surface.blit(glow_surf, (base_x - glow_size, base_y - glow_size))
            
            # Draw faces in correct order (back to front)
            # Top face
            pygame.draw.polygon(surface, top_color, top_points)
            pygame.draw.polygon(surface, outline_color, top_points, 2)
            
            # Left face
            pygame.draw.polygon(surface, left_color, left_points)
            pygame.draw.polygon(surface, outline_color, left_points, 2)
            
            # Front face
            pygame.draw.rect(surface, front_color, front_rect)
            pygame.draw.rect(surface, outline_color, front_rect, 3)
            
            # Draw data node indicator in center of top face
            node_center_x = base_x + self.tile_size // 2
            node_center_y = base_y - self.block_height // 2
            node_radius = 2 + block['size']
            
            # Pulsing node with glow
            node_glow_radius = node_radius + int(pulse_intensity * 5)
            for r in range(node_glow_radius, node_radius, -1):
                alpha = int(100 * (1 - (r - node_radius) / (node_glow_radius - node_radius)))
                pygame.draw.circle(surface, (*base_color, alpha) if len(base_color) == 3 else base_color, 
                                 (node_center_x, node_center_y), r)
            pygame.draw.circle(surface, (255, 255, 255), (node_center_x, node_center_y), node_radius)
            pygame.draw.circle(surface, outline_color, (node_center_x, node_center_y), node_radius + 1, 1)
            
            # Draw floating particles for some blocks
            if block['has_particles']:
                for i in range(3):
                    particle_offset = (self.animation_timer * 0.5 + i * 120) % 360
                    particle_y = base_y - self.block_height - 10 - (particle_offset / 360) * 20
                    particle_alpha = int(255 * (1 - particle_offset / 360))
                    if particle_alpha > 0:
                        particle_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                        pygame.draw.circle(particle_surf, (*base_color, particle_alpha), (2, 2), 2)
                        surface.blit(particle_surf, (node_center_x - 2, int(particle_y)))
        
        # Draw world objects (consoles, crates, terminals, debris)
        for obj in self.objects:
            obj.draw(surface)
    
    def draw_animated_background(self, surface):
        """Draw animated background effects (moving grid and data streams)."""
        # Animate grid offset
        self.grid_offset_y = (self.grid_offset_y + 1) % self.tile_size
        
        # Draw subtle moving vertical lines for depth
        for x in range(0, self.width, self.tile_size * 2):
            alpha_value = 20
            color = (30, 30, 60 + alpha_value)
            pygame.draw.line(surface, color, (x, 0), (x, self.height), 1)
        
        # Update and draw data streams
        for stream in self.data_streams:
            stream['y'] += stream['speed']
            if stream['y'] > self.height:
                stream['y'] = -50
                stream['x'] = random.randint(0, self.width)
            
            # Draw stream as a glowing line
            pygame.draw.line(surface, stream['color'], 
                           (stream['x'], stream['y']), 
                           (stream['x'], stream['y'] + 30), 2)
    
    def draw_menu_background(self, surface, screen_width, screen_height):
        """Draw animated cyberpunk background for menu screens."""
        # Fill background
        surface.fill(self.bg_color)
        
        # Animate grid offset
        self.grid_offset_y = (self.grid_offset_y + 1) % self.tile_size
        
        # Draw moving grid lines
        for x in range(0, screen_width, self.tile_size):
            pygame.draw.line(surface, (30, 30, 60), (x, 0), (x, screen_height), 1)
        
        for y in range(-self.tile_size, screen_height + self.tile_size, self.tile_size):
            y_pos = (y + self.grid_offset_y) % (screen_height + self.tile_size)
            alpha = int(100 * (1 - y_pos / screen_height))
            pygame.draw.line(surface, (30, 30, min(60 + alpha, 255)), (0, y_pos), (screen_width, y_pos), 1)
        
        # Update and draw data streams
        for stream in self.data_streams:
            stream['y'] += stream['speed']
            if stream['y'] > screen_height:
                stream['y'] = -50
                stream['x'] = random.randint(0, screen_width)
            
            # Draw stream as a line
            pygame.draw.line(surface, stream['color'], 
                           (stream['x'], stream['y']), 
                           (stream['x'], stream['y'] + 30), 2)

    def is_valid_position(self, x, y):
        """Check if a position is valid (not colliding with obstacles)."""
        # Convert to grid coordinates for the corners of the player
        # Check all four corners of the player's collision box
        player_size = 32  # Assuming player size is 32x32
        corners = [
            (x, y),  # Top-left
            (x + player_size, y),  # Top-right
            (x, y + player_size),  # Bottom-left
            (x + player_size, y + player_size)  # Bottom-right
        ]
        
        for corner_x, corner_y in corners:
            grid_x = corner_x // self.tile_size
            grid_y = corner_y // self.tile_size
            
            # Check bounds
            if (grid_x < 0 or grid_x >= self.grid_width or 
                grid_y < 0 or grid_y >= self.grid_height):
                return False
            
            # If any corner intersects with a block, position is invalid
            if self.map[grid_y][grid_x] == 1:
                return False
        
        return True

    def get_block_height(self, x, y):
        """Get the height of the block at the given position."""
        grid_x = x // self.tile_size
        grid_y = y // self.tile_size
        
        if (0 <= grid_x < self.grid_width and 
            0 <= grid_y < self.grid_height and 
            self.map[grid_y][grid_x] == 1):
            return self.block_height
        return 0


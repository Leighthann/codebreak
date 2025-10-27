# crafting.py
import pygame
from typing import Dict, List, Optional, Callable

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
NEON_BLUE = (0, 195, 255)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 41, 117)


class CraftingRecipe:
    """Represents a crafting recipe for an item."""
    
    def __init__(self, name: str, description: str, requirements: Dict[str, int], 
                 effect: Dict[str, any], icon_color: tuple = WHITE):
        self.name = name
        self.description = description
        self.requirements = requirements  # e.g., {"code_fragments": 5, "energy_cores": 2}
        self.effect = effect  # e.g., {"type": "shield", "duration": 10, "amount": 50}
        self.icon_color = icon_color


class CraftingSystem:
    """Handles all crafting-related functionality."""
    
    def __init__(self, font_sm, font_md):
        self.font_sm = font_sm
        self.font_md = font_md
        self.show_crafting = False
        
        # Define crafting recipes
        self.recipes = [
            CraftingRecipe(
                name="Data Shield",
                description="Temporary shield that absorbs damage",
                requirements={"code_fragments": 5, "energy_cores": 2},
                effect={"type": "shield", "duration": 10, "amount": 50},
                icon_color=CYAN
            ),
            CraftingRecipe(
                name="Hack Tool",
                description="Confuses nearby enemies briefly",
                requirements={"code_fragments": 3, "data_shards": 4},
                effect={"type": "confuse", "duration": 5, "radius": 150},
                icon_color=NEON_GREEN
            ),
            CraftingRecipe(
                name="Energy Sword",
                description="Powerful melee weapon",
                requirements={"energy_cores": 3, "data_shards": 3},
                effect={"type": "weapon", "damage": 30, "duration": 15},
                icon_color=NEON_BLUE
            )
        ]
    
    def toggle_menu(self) -> bool:
        """Toggle crafting menu visibility. Returns new state."""
        self.show_crafting = not self.show_crafting
        return self.show_crafting
    
    def close_menu(self):
        """Close the crafting menu."""
        self.show_crafting = False
    
    def is_menu_open(self) -> bool:
        """Check if crafting menu is currently open."""
        return self.show_crafting
    
    def can_craft(self, recipe: CraftingRecipe, player_resources: Dict[str, int]) -> bool:
        """Check if player has enough resources to craft an item."""
        for resource, amount in recipe.requirements.items():
            if player_resources.get(resource, 0) < amount:
                return False
        return True
    
    def craft_item(self, recipe_index: int, player, 
                   on_success: Optional[Callable] = None,
                   on_failure: Optional[Callable] = None) -> bool:
        """
        Attempt to craft an item.
        
        Args:
            recipe_index: Index of the recipe to craft
            player: Player object with resources and inventory
            on_success: Callback function called on successful crafting
            on_failure: Callback function called on failed crafting
            
        Returns:
            True if crafting was successful, False otherwise
        """
        if recipe_index < 0 or recipe_index >= len(self.recipes):
            return False
        
        recipe = self.recipes[recipe_index]
        
        # Check if player has enough resources
        if not self.can_craft(recipe, player.resources):
            if on_failure:
                on_failure(recipe, "Not enough resources!")
            return False
        
        # Deduct resources
        for resource, amount in recipe.requirements.items():
            player.resources[resource] -= amount
        
        # Create the crafted item
        crafted_item = {
            "name": recipe.name.lower().replace(" ", "_"),
            "display_name": recipe.name,
            "description": recipe.description,
            "effect": recipe.effect.copy(),
            "icon_color": recipe.icon_color
        }
        
        # Add to player's crafted items
        if not hasattr(player, 'crafted_items'):
            player.crafted_items = []
        player.crafted_items.append(crafted_item)
        
        # Auto-equip if no tool is equipped
        if not player.equipped_tool:
            player.equipped_tool = crafted_item
        
        if on_success:
            on_success(recipe, crafted_item)
        
        return True
    
    def get_recipe_cost_text(self, recipe: CraftingRecipe, player_resources: Dict[str, int]) -> List[tuple]:
        """
        Get formatted cost text for a recipe with color coding.
        
        Returns:
            List of tuples: [(text, color), ...]
        """
        cost_parts = []
        for i, (resource, amount) in enumerate(recipe.requirements.items()):
            player_amount = player_resources.get(resource, 0)
            has_enough = player_amount >= amount
            color = GREEN if has_enough else RED
            
            # Format resource name nicely
            resource_name = resource.replace("_", " ").title()
            text = f"{resource_name}: {player_amount}/{amount}"
            
            cost_parts.append((text, color))
        
        return cost_parts
    
    def draw_crafting_ui(self, surface: pygame.Surface, screen_width: int, screen_height: int,
                        player_resources: Dict[str, int]):
        """Draw the crafting menu UI."""
        if not self.show_crafting:
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        # Crafting menu panel
        panel_width = 600
        panel_height = 500
        panel_x = screen_width // 2 - panel_width // 2
        panel_y = screen_height // 2 - panel_height // 2
        
        # Draw panel background
        pygame.draw.rect(surface, (20, 20, 40), 
                        (panel_x, panel_y, panel_width, panel_height),
                        border_radius=10)
        pygame.draw.rect(surface, NEON_BLUE, 
                        (panel_x, panel_y, panel_width, panel_height), 3,
                        border_radius=10)
        
        # Title
        title_surf = self.font_md.render("CRAFTING MENU", True, NEON_BLUE)
        title_rect = title_surf.get_rect(centerx=screen_width // 2, y=panel_y + 20)
        surface.blit(title_surf, title_rect)
        
        # Instructions
        instructions = [
            "Press 1-3 to craft items",
            "Press C or ESC to close",
            "Press E to use equipped tool"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surf = self.font_sm.render(instruction, True, GRAY)
            inst_rect = inst_surf.get_rect(centerx=screen_width // 2, 
                                          y=panel_y + 60 + i * 20)
            surface.blit(inst_surf, inst_rect)
        
        # Draw recipes
        recipe_y_start = panel_y + 140
        recipe_spacing = 100
        
        for i, recipe in enumerate(self.recipes):
            recipe_y = recipe_y_start + i * recipe_spacing
            
            # Recipe box
            box_rect = pygame.Rect(panel_x + 30, recipe_y, panel_width - 60, 80)
            can_craft = self.can_craft(recipe, player_resources)
            box_color = NEON_GREEN if can_craft else GRAY
            
            pygame.draw.rect(surface, (30, 30, 50), box_rect, border_radius=5)
            pygame.draw.rect(surface, box_color, box_rect, 2, border_radius=5)
            
            # Recipe number
            num_surf = self.font_md.render(f"{i + 1}", True, WHITE)
            num_rect = num_surf.get_rect(midleft=(box_rect.x + 15, box_rect.centery))
            surface.blit(num_surf, num_rect)
            
            # Recipe name
            name_surf = self.font_md.render(recipe.name, True, recipe.icon_color)
            name_rect = name_surf.get_rect(midleft=(box_rect.x + 50, box_rect.y + 15))
            surface.blit(name_surf, name_rect)
            
            # Recipe description
            desc_surf = self.font_sm.render(recipe.description, True, GRAY)
            desc_rect = desc_surf.get_rect(midleft=(box_rect.x + 50, box_rect.y + 35))
            surface.blit(desc_surf, desc_rect)
            
            # Requirements
            cost_parts = self.get_recipe_cost_text(recipe, player_resources)
            cost_x = box_rect.x + 50
            for j, (cost_text, cost_color) in enumerate(cost_parts):
                cost_surf = self.font_sm.render(cost_text, True, cost_color)
                cost_rect = cost_surf.get_rect(midleft=(cost_x, box_rect.y + 55 + j * 15))
                surface.blit(cost_surf, cost_rect)
                cost_x += cost_surf.get_width() + 20
    
    def handle_crafting_input(self, event: pygame.event.Event, player,
                             sound_callback: Optional[Callable] = None,
                             effect_callback: Optional[Callable] = None) -> bool:
        """
        Handle keyboard input for crafting.
        
        Args:
            event: Pygame event
            player: Player object
            sound_callback: Function to call for playing sounds
            effect_callback: Function to call for visual effects
            
        Returns:
            True if event was handled, False otherwise
        """
        if not self.show_crafting:
            return False
        
        if event.type == pygame.KEYDOWN:
            # Crafting selection (1-3 keys)
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                craft_index = event.key - pygame.K_1
                
                def on_success(recipe, item):
                    if sound_callback:
                        sound_callback("level_up")
                    if effect_callback:
                        effect_callback(
                            "text", player.x, player.y - 30,
                            text=f"Crafted {recipe.name}!",
                            color=NEON_GREEN,
                            size=20,
                            duration=2.0
                        )
                
                def on_failure(recipe, message):
                    if sound_callback:
                        sound_callback("hit")
                    if effect_callback:
                        effect_callback(
                            "text", player.x, player.y - 30,
                            text=message,
                            color=RED,
                            size=20,
                            duration=2.0
                        )
                
                self.craft_item(craft_index, player, on_success, on_failure)
                return True
            
            # Close menu
            elif event.key in [pygame.K_c, pygame.K_ESCAPE]:
                self.close_menu()
                if sound_callback:
                    sound_callback("menu_select")
                return True
        
        return False
    
    def get_equipped_tool_name(self, player) -> Optional[str]:
        """Get the name of the currently equipped tool."""
        if hasattr(player, 'equipped_tool') and player.equipped_tool:
            return player.equipped_tool.get('display_name', 'Unknown Tool')
        return None
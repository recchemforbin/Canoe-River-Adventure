import pygame
import pygame_gui
import random
import json
import os

# Initialize pygame and pygame_gui
pygame.init()

# Game settings
screen_width, screen_height = 800, 600
water_width = 400  # Width of the river (water)
ground_width = (screen_width - water_width) // 2  # Ground on left and right
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Canoeing River Adventure")

# Pygame GUI manager
manager = pygame_gui.UIManager((screen_width, screen_height))

# Create input for player name
name_input_rect = pygame.Rect((screen_width // 2 - 150, screen_height // 2 - 50), (300, 50))
name_input = pygame_gui.elements.UITextEntryLine(relative_rect=name_input_rect, manager=manager)
submit_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((screen_width // 2 - 75, screen_height // 2 + 10), (150, 50)), 
                                             text='Submit', manager=manager)

player_name = ""

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Initial ground color (changes each level)
ground_color = GREEN

# Time and Clock
clock = pygame.time.Clock()
last_obstacle_time = pygame.time.get_ticks()

# Level settings
time_to_advance = 20000  # 20 seconds to pass the level
level_start_time = pygame.time.get_ticks()
current_level = 1
max_speed_increase = 5
speed_increment_interval = 2000  # Speed up every 2 seconds
last_speed_increase_time = level_start_time

# Water flow simulation
water_lines = []

# Leaderboard file
leaderboard_file = "leaderboard.json"

# Game state management
game_started = False
input_active = True

# ** New ** Score
score = 0
score_increment = 10  # Points per second

# Define SpriteSheet class
class SpriteSheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_image(self, frame, width, height, scale, color_key):
        # Extract the frame from the sprite sheet
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (frame * width, 0, width, height))
        image = pygame.transform.scale(image, (width * scale, height * scale))
        image.set_colorkey(color_key)  # Make the background color transparent
        return image

# Load the player sprite sheet
canoe_sprite_sheet = SpriteSheet('player_canoe_spritesheet.png')

# Load multiple frames for animation (assuming 4 frames in the sprite sheet)
player_frames = [
    canoe_sprite_sheet.get_image(i, 50, 100, 1, (0, 0, 0))  # 64x32 pixel frame, scale 2x, black is transparent
    for i in range(2)  # Assuming 2 frames of animation
]

# Player settings
player_frame_index = 0
player_image = player_frames[player_frame_index]
player_x, player_y = (screen_width - player_image.get_width()) // 2, screen_height - 100
player_speed = 5
player_animation_speed = 50  # Time between frames in milliseconds
last_animation_time = pygame.time.get_ticks()

# Obstacle settings
obstacle_width, obstacle_height = 40, 40
obstacle_speed = 5
obstacles = []
obstacle_spawn_time = 1000  # in milliseconds

# Load the enemy sprite sheet
enemy_sprite_sheet = SpriteSheet('enemy_spritesheet.png')

# Load multiple frames for animation (assuming 3 frames in the sprite sheet)
enemy_frames = [
    enemy_sprite_sheet.get_image(i, 50, 100, 1, (0, 0, 0))  # Assuming each frame is 40x40
    for i in range(2)  # Assuming 2 frames of animation
]

# Function to create a water line
def create_water_line():
    line_x = random.randint(ground_width, screen_width - ground_width)
    line_y = -10
    return pygame.Rect(line_x, line_y, 5, 10)

# Function to create an obstacle
def create_obstacle():
    x = random.randint(ground_width, screen_width - ground_width - obstacle_width)
    y = -obstacle_height
    return pygame.Rect(x, y, obstacle_width, obstacle_height)

# Function to display health
def display_health(health):
    font = pygame.font.SysFont(None, 36)
    health_text = font.render(f"Health: {health}", True, WHITE)
    screen.blit(health_text, (10, 10))

# Function to display score
def display_score():
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 50))

# Function to check collisions
def check_collision(player_rect, obstacles):
    global health
    for obstacle in obstacles:
        if player_rect.colliderect(obstacle):
            health -= 20
            obstacles.remove(obstacle)

# Function to reset level
def reset_level():
    global obstacle_speed, player_x, player_y, health, level_start_time, obstacles, water_lines, last_obstacle_time
    obstacle_speed = 5 + current_level  # Increase speed based on level
    player_x, player_y = (screen_width - player_image.get_width()) // 2, screen_height - 100
    health = 100
    level_start_time = pygame.time.get_ticks()
    obstacles.clear()
    water_lines.clear()
    last_obstacle_time = pygame.time.get_ticks()

# Function to change level appearance
def change_level_appearance():
    global ground_color
    ground_color = [random.randint(0, 255) for _ in range(3)]  # Randomize ground color each level

# Function to save leaderboard with score
def save_leaderboard(player_name, level, score):
    # Load existing leaderboard
    if os.path.exists(leaderboard_file):
        with open(leaderboard_file, 'r') as f:
            leaderboard = json.load(f)
    else:
        leaderboard = {}

    # Update leaderboard with player name, highest level, and score
    leaderboard[player_name] = {
        "level": level,
        "score": score
    }

    # Save leaderboard to file
    with open(leaderboard_file, 'w') as f:
        json.dump(leaderboard, f)

# Function to display leaderboard
def display_leaderboard():
    if os.path.exists(leaderboard_file):
        with open(leaderboard_file, 'r') as f:
            leaderboard = json.load(f)
        
        font = pygame.font.SysFont(None, 36)
        screen.fill(BLUE)
        title = font.render("Leaderboard", True, WHITE)
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, 20))

        # Sort leaderboard by score in descending order
        sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1]["score"], reverse=True)

        y_offset = 80
        for i, (name, data) in enumerate(sorted_leaderboard[:10]):  # Show top 10 by score
            text = font.render(f"{i+1}. {name}: Level {data['level']} - Score {data['score']}", True, WHITE)
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, y_offset))
            y_offset += 40
        
        pygame.display.flip()
        pygame.time.wait(5000)  # Display for 5 seconds

# Main game loop
running = True
health = 100

while running:
    time_delta = clock.tick(60) / 1000.0

    screen.fill(BLUE)  # Background color (water)

    # Handle input pop-up and game start
    events = pygame.event.get()  # Get all events at once
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        manager.process_events(event)  # Process GUI events

        # Fix deprecation: check event.type instead of user_type
        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == submit_button:
            player_name = name_input.get_text()  # Get player's name from the input
            input_active = False  # Stop the name input
            game_started = True  # Start the game

    manager.update(time_delta)
    
    if input_active:
        manager.draw_ui(screen)  # Draw UI elements for name input

    if game_started and not input_active:
        # Draw ground on both sides
        pygame.draw.rect(screen, ground_color, (0, 0, ground_width, screen_height))  # Left ground
        pygame.draw.rect(screen, ground_color, (screen_width - ground_width, 0, ground_width, screen_height))  # Right ground

        # Handle player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > ground_width:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < screen_width - ground_width - player_image.get_width():
            player_x += player_speed

        # Animate the player (Canoe)
        current_time = pygame.time.get_ticks()
        if current_time - last_animation_time > player_animation_speed:
            player_frame_index = (player_frame_index + 1) % len(player_frames)
            player_image = player_frames[player_frame_index]
            last_animation_time = current_time

        screen.blit(player_image, (player_x, player_y))  # Draw the player sprite

        # Spawn obstacles
        if pygame.time.get_ticks() - last_obstacle_time > obstacle_spawn_time:
            obstacles.append(create_obstacle())
            last_obstacle_time = pygame.time.get_ticks()

        # Move and draw obstacles
        for obstacle in obstacles[:]:
            obstacle.y += obstacle_speed
            if obstacle.y > screen_height:
                obstacles.remove(obstacle)
            else:
                screen.blit(random.choice(enemy_frames), obstacle.topleft)  # Draw enemy sprite

        # Collision check
        player_rect = pygame.Rect(player_x, player_y, player_image.get_width(), player_image.get_height())
        check_collision(player_rect, obstacles)

        # Display health and score
        display_health(health)
        display_score()

        # Increase speed periodically
        if pygame.time.get_ticks() - last_speed_increase_time > speed_increment_interval:
            obstacle_speed = min(obstacle_speed + 1, max_speed_increase)
            last_speed_increase_time = pygame.time.get_ticks()

        # Check health
        if health <= 0:
            save_leaderboard(player_name, current_level, score)
            display_leaderboard()
            reset_level()
            input_active = True  # Back to input screen

        # Increase score over time
        score += score_increment * time_delta

        # Check if level time has passed
        if pygame.time.get_ticks() - level_start_time > time_to_advance:
            current_level += 1
            change_level_appearance()
            reset_level()

    # Update the display
    pygame.display.flip()

pygame.quit()

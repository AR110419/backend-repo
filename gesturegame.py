import logging
import pygame
import random

logging.basicConfig(level=logging.INFO)
print("arun")
# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Hand Gesture Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)

# Load images
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (800, 600))
character = pygame.image.load("character.png")
character = pygame.transform.scale(character, (120, 120))
asteroid_img = pygame.image.load("asteroid.png")
asteroid_img = pygame.transform.scale(asteroid_img, (100, 100))

# List to store falling asteroids
asteroids = []
ast_speed = 8  # Speed of falling asteroids
char_x = 340  # Initial position of the character
char_y = 480  # Fixed character position (Y-axis)
char_speed = 20  # Speed of character movement
running = True
score = 0

def spawn_asteroid():
    """Spawn a falling asteroid at a random X position."""
    x = random.randint(50, 750)
    asteroids.append([x, 0])

def detect_hand_movement(hand_landmarks):
    """Detect hand movement and update character position."""
    global char_x
    index_tip = hand_landmarks[8]
    x = int(index_tip.x * 800)  # Map hand position to screen width
    if x < 400:
        char_x -= char_speed  # Move left
    else:
        char_x += char_speed  # Move right

def start_game():
    global running
    logging.info("Hand gesture game started.")
    spawn_asteroid()
    while running:
        screen.blit(background, (0, 0))
        for asteroid in asteroids[:]:
            asteroid[1] += ast_speed
            screen.blit(asteroid_img, (asteroid[0], asteroid[1]))
            if asteroid[1] > 480 and char_x < asteroid[0] < char_x + 120:
                show_game_over()
                running = False
            if asteroid[1] > 600:
                asteroids.remove(asteroid)
                score += 1

        if random.random() < 0.05:
            spawn_asteroid()

        screen.blit(character, (char_x, char_y))
        score_text = font.render(f"Score: {score}", True, (255, 0, 0))
        screen.blit(score_text, (650, 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.update()
        clock.tick(30)

def show_game_over():
    """Display Game Over message in the center of the screen."""
    font = pygame.font.SysFont("Arial", 72, bold=True)
    text = font.render("GAME OVER", True, (255, 255, 255))
    text_rect = text.get_rect(center=(400, 300))
    pygame.draw.rect(screen, (255, 0, 0), (200, 250, 400, 100))  # Red box
    screen.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(3000)  # Pause for 3 seconds before closing

def terminate_game():
    global running
    logging.info("Hand gesture game terminated.")
    running = False
    pygame.quit()

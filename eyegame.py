import logging
import pygame
import random

logging.basicConfig(level=logging.INFO)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Eye Tracking Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)

# Load images
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (800, 600))
character = pygame.image.load("character.png")
character = pygame.transform.scale(character, (120, 120))
balloon_img = pygame.image.load("balloon.png")
balloon_img = pygame.transform.scale(balloon_img, (150, 170))

# Initialize game variables
balloons = [{"x": random.randint(100, 700), "y": 600} for _ in range(5)]
running = True
score = 0

def spawn_balloon():
    """Spawn a balloon at a random position."""
    balloons.append({"x": random.randint(100, 700), "y": 600})

def detect_eye_movement(eye_landmarks):
    """Detect eye movement and update game state."""
    global score
    x, y = eye_landmarks
    for balloon in balloons[:]:
        balloon_rect = pygame.Rect(balloon["x"], balloon["y"], 150, 170)
        if balloon_rect.collidepoint(x, y):
            balloons.remove(balloon)
            spawn_balloon()
            score += 1

def start_game():
    global running
    logging.info("Eye tracking game started.")
    while running:
        screen.blit(background, (0, 0))
        for balloon in balloons:
            screen.blit(balloon_img, (balloon["x"], balloon["y"]))
            balloon["y"] -= 2
            if balloon["y"] < -70:
                balloon["y"] = 600
                balloon["x"] = random.randint(100, 700)

        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.update()
        clock.tick(30)

def terminate_game():
    global running
    logging.info("Eye tracking game terminated.")
    running = False
    pygame.quit()

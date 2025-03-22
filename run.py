import os
import sys
import pygame

# -------------------------------------------------------------------
# Set environment variables to avoid ALSA and Pulse errors
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")  # Use dummy audio to bypass ALSA errors
os.environ.setdefault("PULSE_RUNTIME_PATH", "/tmp/pulse")  # Provide a temporary Pulse runtime path

# Ensure XDG_RUNTIME_DIR is set to a valid directory
if 'XDG_RUNTIME_DIR' not in os.environ or not os.path.isdir(os.environ['XDG_RUNTIME_DIR']):
    runtime_dir = f"/tmp/runtime-{os.getlogin()}"
    os.environ['XDG_RUNTIME_DIR'] = runtime_dir
    if not os.path.isdir(runtime_dir):
        os.makedirs(runtime_dir, exist_ok=True)
    print(f"Set XDG_RUNTIME_DIR to {runtime_dir}")

# -------------------------------------------------------------------
# Initialize Pygame with display and font modules
pygame.display.init()
pygame.font.init()

# Attempt to initialize the mixer; if it fails, disable audio
try:
    pygame.mixer.init()
except Exception as e:
    print("Warning: Audio initialization failed, continuing without audio:", e)
    pygame.mixer.quit()

# -------------------------------------------------------------------
# Try loading system fonts; fall back to a default font if necessary
try:
    fonts = pygame.font.get_fonts()
    if not fonts:
        raise Exception("No system fonts found.")
except Exception as e:
    print("Warning: System fonts could not be loaded; using default fallback:", e)
    fonts = ["arial"]

# -------------------------------------------------------------------
# Set up a basic game window
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Multi-Tracking Game")

# Create a simple menu for selecting the game type
font = pygame.font.SysFont(fonts[0], 28)
menu_items = [
    "1. Eye Tracking Game",
    "2. Hand Tracking Game",
    "3. Gesture Tracking Game",
    "Press Q to Quit"
]

def draw_menu(selected_text):
    screen.fill((30, 30, 30))
    y_offset = 100
    for item in menu_items:
        text_surface = font.render(item, True, (255, 255, 255))
        screen.blit(text_surface, (50, y_offset))
        y_offset += 50
    selected_surface = font.render(f"Selected: {selected_text}", True, (0, 255, 0))
    screen.blit(selected_surface, (50, y_offset + 20))
    pygame.display.flip()

def main():
    clock = pygame.time.Clock()
    current_game = "None"
    print("INFO: Multi-Tracking Game service is live 🎉")
    print("INFO: Starting program: eye_tracking_game")
    running = True
    
    while running:
        # Display the menu with the current selection
        draw_menu(current_game)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_1:
                    current_game = "Eye Tracking Game"
                    print("INFO: Starting Eye Tracking Game...")
                elif event.key == pygame.K_2:
                    current_game = "Hand Tracking Game"
                    print("INFO: Starting Hand Tracking Game...")
                elif event.key == pygame.K_3:
                    current_game = "Gesture Tracking Game"
                    print("INFO: Starting Gesture Tracking Game...")
                    
        clock.tick(30)

    pygame.quit()

if __name__ == '__main__':
    main()

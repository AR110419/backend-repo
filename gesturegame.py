import cv2
import mediapipe as mp
import pygame
import random
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse

app = FastAPI()

# Initialize MediaPipe Hands for hand tracking
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))  # Set game window size
pygame.display.set_caption("Hand Gesture Dodge Game")  # Set game title
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)  # Set font for text display

# Load background image
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (800, 600))

# Load character image
character = pygame.image.load("character.png")
character = pygame.transform.scale(character, (120, 120))  # Increased character size
char_x = 340  # Adjusted initial position for larger character
char_y = 480  # Fixed character position (Y-axis)
char_speed = 20  # Speed of character movement

# Load asteroid image
asteroid_img = pygame.image.load("asteroid.png")  # Load asteroid sprite
asteroid_img = pygame.transform.scale(asteroid_img, (100, 100))  # Increased asteroid size

# List to store falling asteroids
asteroids = []
ast_speed = 8  # Speed of falling asteroids

# Scoring system
score = 0

def spawn_asteroid():
    """Spawn a falling asteroid at a random X position."""
    x = random.randint(50, 750)
    asteroids.append([x, 0])

def detect_hand_movement(hand_landmarks):
    """Detect hand movement and update character position."""
    global char_x
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    x = int(index_tip.x * 800)  # Map hand position to screen width
    if x < 400:
        char_x -= char_speed  # Move left
    else:
        char_x += char_speed  # Move right

def show_game_over():
    """Display Game Over message in the center of the screen."""
    game_over_font = pygame.font.SysFont("Arial", 72, bold=True)
    text = game_over_font.render("GAME OVER", True, (255, 255, 255))
    text_rect = text.get_rect(center=(400, 300))
    pygame.draw.rect(screen, (255, 0, 0), (200, 250, 400, 100))  # Red box
    screen.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(3000)  # Pause for 3 seconds before closing

@app.get("/video_feed")
async def video_feed():
    global char_x, score, asteroids
    cap = cv2.VideoCapture(0)
    while True:
        screen.blit(background, (0, 0))  # Draw background image
        
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # Flip frame horizontally for mirror effect
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB for MediaPipe
        results = hands.process(rgb_frame)  # Process hand tracking
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                detect_hand_movement(hand_landmarks)
        
        char_x = max(0, min(680, char_x))  # Adjusted for larger character
        
        for asteroid in asteroids[:]:
            asteroid[1] += ast_speed  # Move asteroid downwards
            screen.blit(asteroid_img, (asteroid[0], asteroid[1]))  # Draw asteroid
            
            if asteroid[1] > 480 and char_x < asteroid[0] < char_x + 120:
                show_game_over()
                cap.release()
                cv2.destroyAllWindows()
                pygame.quit()
                return
            
            if asteroid[1] > 600:
                asteroids.remove(asteroid)
                score += 1  # Increase score when avoiding asteroid
        
        if random.random() < 0.05:
            spawn_asteroid()
        
        screen.blit(character, (char_x, char_y))
        
        score_text = font.render(f"Score: {score}", True, (255, 0, 0))
        screen.blit(score_text, (650, 20))
        
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        
        pygame.display.update()  # Refresh game display
        clock.tick(30)  # Limit frame rate to 30 FPS
        await asyncio.sleep(0.01)

@app.get("/")
async def index():
    html_content = """
    <html>
        <head>
            <title>Hand Gesture Dodge Game</title>
        </head>
        <body style="background-color: #222; color: #fff; text-align: center;">
            <h1>Hand Gesture Dodge Game</h1>
            <img src="/video_feed" width="800" height="600" style="border: 2px solid #fff;"/>
            <p>Use your hand gestures to move the character and dodge the falling asteroids!</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hand_gesture_dodge_game_server:app", host="0.0.0.0", port=8000, reload=True)

import cv2
import mediapipe as mp
import random
import pygame
import numpy as np
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse

# Initialize FastAPI
app = FastAPI()

# Initialize Pygame (ensure your environment supports a display or use a dummy driver)
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eye Tracking Balloon Game")
clock = pygame.time.Clock()

# Load balloon image and resize it
balloon_img = pygame.image.load("balloon.png")
balloon_img = pygame.transform.scale(balloon_img, (150, 170))
balloons = [{"x": random.randint(100, 700), "y": 600} for _ in range(5)]

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, 
                                  min_tracking_confidence=0.5)

# Open webcam
cap = cv2.VideoCapture(0)

# Game variables
score = 0  # Player score
SENSITIVITY = 1.5  # Increase sensitivity for smaller eye movements

def get_eye_position(face_landmarks, width, height):
    """
    Get the eye position based on detected face landmarks.
    Uses the average of the left and right eye lower landmarks for tracking.
    """
    left_eye = face_landmarks.landmark[145]  # Left eye lower point
    right_eye = face_landmarks.landmark[374] # Right eye lower point
    eye_x = (left_eye.x + right_eye.x) / 2
    eye_y = (left_eye.y + right_eye.y) / 2
    # Amplify and center the movement based on sensitivity
    eye_x = int((eye_x - 0.5) * width * SENSITIVITY + (width // 2))
    eye_y = int((eye_y - 0.5) * height * SENSITIVITY + (height // 2))
    return max(0, min(eye_x, width)), max(0, min(eye_y, height))

async def game_frames():
    """
    Async generator that processes video capture, updates game state,
    renders the game using Pygame, and streams the game screen as JPEG images.
    """
    global score, balloons
    while True:
        # Fill the background (Sky Blue)
        screen.fill((135, 206, 250))
        
        # Capture a frame from the webcam for eye tracking
        success, frame = cap.read()
        if success:
            frame = cv2.flip(frame, 1)  # Mirror image for natural interaction
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    eye_x, eye_y = get_eye_position(face_landmarks, WIDTH, HEIGHT)
                    # Visual indicator of eye tracking (Red dot)
                    pygame.draw.circle(screen, (255, 0, 0), (eye_x, eye_y), 10)
                    
                    # Check collision with each balloon
                    for balloon in balloons[:]:
                        balloon_rect = pygame.Rect(balloon["x"], balloon["y"], 150, 170)
                        if balloon_rect.collidepoint(eye_x, eye_y):
                            balloons.remove(balloon)
                            balloons.append({"x": random.randint(100, 700), "y": 600})
                            score += 1
        
        # Update and draw balloons
        for balloon in balloons:
            screen.blit(balloon_img, (balloon["x"], balloon["y"]))
            balloon["y"] -= 2  # Move balloon upward
            if balloon["y"] < -170:
                balloon["y"] = 600
                balloon["x"] = random.randint(100, 700)
        
        # Display the current score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        
        # Process Pygame events to allow graceful exit (if running locally)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                cap.release()
                cv2.destroyAllWindows()
                return
        
        pygame.display.update()
        clock.tick(30)
        
        # Convert the Pygame surface to a format suitable for streaming:
        # Get the surface pixels as an array (shape: [width, height, 3])
        frame_array = pygame.surfarray.array3d(screen)
        # Transpose the array to get shape (height, width, 3)
        frame_array = np.transpose(frame_array, (1, 0, 2))
        # Convert from RGB to BGR (OpenCV format)
        frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
        
        ret, buffer = cv2.imencode('.jpg', frame_array)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        await asyncio.sleep(0.01)

@app.get("/video_feed")
async def video_feed():
    """
    Streams the game output as a continuous MJPEG stream.
    """
    return StreamingResponse(game_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
async def index():
    """
    Serves a basic HTML page that embeds the video stream.
    """
    html_content = """
    <html>
        <head>
            <title>Eye Controlled Balloon Game</title>
        </head>
        <body style="background-color: #222; color: #fff; text-align: center;">
            <h1>Eye Controlled Balloon Game</h1>
            <img src="/video_feed" width="800" height="600" style="border: 2px solid #fff;"/>
            <p>Use your eye movements to hit the balloons and boost your score.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eyegame:app", host="0.0.0.0", port=8000, reload=True)

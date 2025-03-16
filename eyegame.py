import cv2
import mediapipe as mp
import random
import pygame

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eye Tracking Balloon Game")
clock = pygame.time.Clock()

# Load balloon image
balloon_img = pygame.image.load("balloon.png")
balloon_img = pygame.transform.scale(balloon_img, (150, 170))
balloons = [{"x": random.randint(100, 700), "y": 600} for _ in range(5)]

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Open webcam
cap = cv2.VideoCapture(0)

# Font for displaying score
font = pygame.font.Font(None, 36)
score = 0  # Score variable

# Eye sensitivity multiplier
SENSITIVITY = 1.5  # Increase this value to make small eye movements more responsive

def get_eye_position(face_landmarks, width, height):
    """Get the position of the eye based on face landmarks and amplify movement."""
    left_eye = face_landmarks.landmark[145]  # Left eye lower point
    right_eye = face_landmarks.landmark[374] # Right eye lower point
    
    # Compute eye center position
    eye_x = (left_eye.x + right_eye.x) / 2
    eye_y = (left_eye.y + right_eye.y) / 2
    
    # Apply sensitivity scaling
    eye_x = int((eye_x - 0.5) * width * SENSITIVITY + (width // 2))
    eye_y = int((eye_y - 0.5) * height * SENSITIVITY + (height // 2))
    
    return max(0, min(eye_x, width)), max(0, min(eye_y, height))  # Ensure it stays within bounds

running = True
while running:
    screen.fill((135, 206, 250))  # Sky Blue Background
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            eye_x, eye_y = get_eye_position(face_landmarks, WIDTH, HEIGHT)
            pygame.draw.circle(screen, (255, 0, 0), (eye_x, eye_y), 10)  # Red dot for eye tracking

            for balloon in balloons[:]:  # Iterate over a copy to modify original list
                balloon_rect = pygame.Rect(balloon["x"], balloon["y"], 150, 170)  # Use balloon size
                if balloon_rect.collidepoint(eye_x, eye_y):  # Collision Detection
                    balloons.remove(balloon)
                    balloons.append({"x": random.randint(100, 700), "y": 600})  # Spawn new balloon
                    score += 1  # Increase score

    # Draw balloons and move them upwards
    for balloon in balloons:
        screen.blit(balloon_img, (balloon["x"], balloon["y"]))
        balloon["y"] -= 2  # Move balloon upwards
        if balloon["y"] < -70:
            balloon["y"] = 600
            balloon["x"] = random.randint(100, 700)

    # Display Score
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))  # Draw score at top-left corner

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.update()
    clock.tick(30)

cap.release()
cv2.destroyAllWindows()
pygame.quit()

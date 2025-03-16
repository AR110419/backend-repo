import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse

app = FastAPI()

# Initialize Mediapipe Hands and Drawing
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)

# Initialize video capture
cap = cv2.VideoCapture(0)

# Get the screen dimensions for mapping
screen_width, screen_height = pyautogui.size()
prev_x, prev_y = pyautogui.position()
smoothing_factor = 0.3  # Adjust to smooth cursor movement
last_action_time = time.time()  # To debounce actions

async def generate_frames():
    global prev_x, prev_y, last_action_time
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
    
        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Draw hand landmarks on frame
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                # Get necessary landmark references
                index_tip = landmarks[8]
                middle_tip = landmarks[12]
                ring_tip = landmarks[16]
                pinky_tip = landmarks[20]
                thumb_tip = landmarks[4]
                palm_base = landmarks[0]

                # Map index tip coordinates to screen coordinates
                cx, cy = int(index_tip.x * screen_width), int(index_tip.y * screen_height)
                new_x = prev_x + (cx - prev_x) * smoothing_factor
                new_y = prev_y + (cy - prev_y) * smoothing_factor
                prev_x, prev_y = new_x, new_y

                current_time = time.time()
                fingers = [index_tip, middle_tip, ring_tip, pinky_tip]

                # Gesture 1: Increase Brightness if all finger tips are above the palm
                if all(f.y < palm_base.y for f in fingers) and (current_time - last_action_time > 0.5):
                    print("🔆 Increasing Brightness")
                    pyautogui.hotkey('volumeup')
                    last_action_time = current_time

                # Gesture 2: Decrease Brightness if all finger tips are below the palm
                elif all(f.y > palm_base.y for f in fingers) and (current_time - last_action_time > 0.5):
                    print("🔅 Decreasing Brightness")
                    pyautogui.hotkey('volumedown')
                    last_action_time = current_time

                # Gesture 3: Move cursor if index and middle finger are above the palm
                elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y:
                    print(f"🎯 Moving Cursor to ({new_x}, {new_y})")
                    pyautogui.moveTo(new_x, new_y, duration=0.05)

                # Gesture 4: Swipe Page if index and middle are above while ring is below the palm
                elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y and ring_tip.y > palm_base.y and (current_time - last_action_time > 0.5):
                    print("📄 Swiping Page")
                    pyautogui.hotkey('ctrl', 'right')
                    last_action_time = current_time

                # Gesture 5: Take Screenshot if middle, ring, and pinky are above while index is below the palm
                elif all(f.y < palm_base.y for f in [middle_tip, ring_tip, pinky_tip]) and index_tip.y > palm_base.y and (current_time - last_action_time > 0.5):
                    print("📸 Taking Screenshot")
                    pyautogui.screenshot().save(f'screenshot_{int(time.time())}.png')
                    last_action_time = current_time

                # Gesture 6: Double Click when index and middle tips are vertically close
                elif abs(index_tip.y - middle_tip.y) < 0.02 and (current_time - last_action_time > 0.5):
                    print("🖱️ Double Click")
                    pyautogui.doubleClick()
                    last_action_time = current_time

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        await asyncio.sleep(0.01)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/")
async def index():
    html_content = """
    <html>
        <head>
            <title>Hand Gesture Control</title>
        </head>
        <body style="background-color: #222; color: #fff; text-align: center;">
            <h1>Hand Gesture Control</h1>
            <img src="/video_feed" width="640" height="480" style="border: 2px solid #fff;"/>
            <p>Use hand gestures to control brightness, swipe pages, take screenshots, and double click.</p>
            <p>Close the window or press 'q' if running locally to exit.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hand:app", host="0.0.0.0", port=8000, reload=True)

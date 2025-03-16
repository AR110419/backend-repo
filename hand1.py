import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import os
import platform
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse

app = FastAPI()

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)

# Capture Webcam
cap = cv2.VideoCapture(0)

# Get Screen Size
screen_width, screen_height = pyautogui.size()
prev_x, prev_y = pyautogui.position()
smoothing_factor = 0.3  # Adjust for smoother cursor movement
DEBOUNCE_TIME = 0.3  # Reduced debounce time from 0.5 to 0.3 seconds
last_action_time = time.time()

def change_brightness(increase=True):
    """ Adjust screen brightness based on OS """
    if platform.system() == "Windows":
        cmd = 'powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{})'
        brightness = 80 if increase else 20
        os.system(cmd.format(brightness))
    elif platform.system() == "Darwin":  # MacOS
        os.system("osascript -e 'tell application \"System Events\" to key code 144 using {command down}'" if increase else "osascript -e 'tell application \"System Events\" to key code 145 using {command down}'")
    else:
        print("⚠️ Brightness control not supported for this OS!")

async def generate_frames():
    global prev_x, prev_y, last_action_time
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                index_tip = landmarks[8]
                middle_tip = landmarks[12]
                ring_tip = landmarks[16]
                pinky_tip = landmarks[20]
                thumb_tip = landmarks[4]
                palm_base = landmarks[0]

                cx, cy = int(index_tip.x * screen_width), int(index_tip.y * screen_height)
                new_x = prev_x + (cx - prev_x) * smoothing_factor
                new_y = prev_y + (cy - prev_y) * smoothing_factor
                prev_x, prev_y = new_x, new_y

                fingers = [index_tip, middle_tip, ring_tip, pinky_tip]
                current_time = time.time()

                if sum(f.y < palm_base.y for f in fingers) >= 3 and (current_time - last_action_time > DEBOUNCE_TIME):
                    print("🔆 Increasing Brightness")
                    change_brightness(True)
                    last_action_time = current_time

                elif sum(f.y > palm_base.y for f in fingers) >= 3 and (current_time - last_action_time > DEBOUNCE_TIME):
                    print("🔅 Decreasing Brightness")
                    change_brightness(False)
                    last_action_time = current_time

                elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y:
                    print(f"🎯 Moving Cursor to ({new_x}, {new_y})")
                    pyautogui.moveTo(new_x, new_y, duration=0.05)

                elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y and ring_tip.y > palm_base.y and (current_time - last_action_time > DEBOUNCE_TIME):
                    print("📄 Scrolling Page")
                    pyautogui.scroll(-10)
                    last_action_time = current_time

                elif all(f.y < palm_base.y for f in [middle_tip, ring_tip, pinky_tip]) and index_tip.y > palm_base.y and (current_time - last_action_time > DEBOUNCE_TIME):
                    print("📸 Taking Screenshot")
                    pyautogui.screenshot().save(f'screenshot_{int(time.time())}.png')
                    last_action_time = current_time

                elif abs(index_tip.y - middle_tip.y) < 0.015 and abs(index_tip.x - thumb_tip.x) < 0.015 and (current_time - last_action_time > DEBOUNCE_TIME):
                    print("🖱️ Double Click")
                    pyautogui.doubleClick()
                    last_action_time = current_time

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
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hand1:app", host="0.0.0.0", port=8000, reload=True)

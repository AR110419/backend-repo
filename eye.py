import cv2
import mediapipe as mp
import pyautogui
import asyncio
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Initialize video capture and mediapipe face mesh
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()  # get the full screen size

async def generate_frames():
    """
    Capture frames from the webcam, process them using MediaPipe for facial landmarks,
    control the mouse with eye movements, and stream the result.
    """
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        landmark_points = output.multi_face_landmarks
        frame_height, frame_width, _ = frame.shape

        if landmark_points:
            landmarks = landmark_points[0].landmark
            # Process landmarks for eye tracking (indices 474 to 477)
            for idx, landmark in enumerate(landmarks[474:478]):
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)
                cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)
                if idx == 1:
                    screen_x = (screen_w / frame_width) * x
                    screen_y = (screen_h / frame_height) * y
                    pyautogui.moveTo(screen_x, screen_y)
            # Blink detection using landmarks 145 and 159 for left eye
            left = [landmarks[145], landmarks[159]]
            for landmark in left:
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)
                cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            if (left[0].y - left[1].y) < 0.007:
                pyautogui.click()
                await asyncio.sleep(1)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        await asyncio.sleep(0.01)

@app.get("/video_feed")
async def video_feed():
    """
    HTTP endpoint that streams the processed video feed.
    """
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
async def index():
    """
    Basic HTML interface for the eye tracking demo.
    """
    html_content = """
    <html>
        <head>
            <title>Eye Controlled Mouse Demo</title>
        </head>
        <body style="background-color: #222; color: #fff; text-align: center;">
            <h1>Eye Controlled Mouse Demo</h1>
            <img src="/video_feed" width="640" height="480" style="border: 2px solid #fff;"/>
            <p>Look at the webcam and use your eye movements (blink to click).</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def start_tracking():
    logging.info("Eye tracking started.")
    uvicorn.run("eye:app", host="0.0.0.0", port=8001, reload=True)

def terminate_tracking():
    logging.info("Eye tracking terminated.")
    cam.release()
    cv2.destroyAllWindows()

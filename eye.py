import cv2
import mediapipe as mp
import pyautogui
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse

app = FastAPI()

# Initialize video capture and mediapipe face mesh
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()  # get the full screen size

async def generate_frames():
    """
    This async generator captures frames from the webcam, processes them using mediapipe
    for facial landmarks, uses landmark results to control the mouse pointer via pyautogui,
    and encodes the frame to JPEG bytes to stream as a multipart response.
    """
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        # Flip frame horizontally for a mirror effect
        frame = cv2.flip(frame, 1)
        # Convert the frame to RGB for mediapipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        landmark_points = output.multi_face_landmarks
        frame_height, frame_width, _ = frame.shape

        if landmark_points:
            landmarks = landmark_points[0].landmark
            # Process landmarks 474 to 477 (commonly for eye tracking)
            for idx, landmark in enumerate(landmarks[474:478]):
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)
                cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)
                if idx == 1:
                    # Map the point to full screen dimensions and control mouse pointer
                    screen_x = (screen_w / frame_width) * x
                    screen_y = (screen_h / frame_height) * y
                    pyautogui.moveTo(screen_x, screen_y)
            # Detect blink using two landmark points for the left eye (145 and 159)
            left = [landmarks[145], landmarks[159]]
            for landmark in left:
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)
                cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            # If the difference in y coordinates is small, interpret it as a blink (click action)
            if (left[0].y - left[1].y) < 0.007:
                pyautogui.click()
                # Pause for a second to avoid multiple rapid clicks
                await asyncio.sleep(1)
        
        # Encode the processed frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        # Yield frame in a multipart format
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        # Short sleep to allow other async operations
        await asyncio.sleep(0.01)

@app.get("/video_feed")
async def video_feed():
    """
    HTTP endpoint that streams the video feed.
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/")
async def index():
    """
    Basic HTML page to display the video feed.
    """
    html_content = """
    <html>
        <head>
            <title>Eye Controlled Mouse Demo</title>
        </head>
        <body style="background-color: #222; color: #fff; text-align: center;">
            <h1>Eye Controlled Mouse Demo</h1>
            <img src="/video_feed" width="640" height="480" style="border: 2px solid #fff;"/>
            <p>Look at the webcam and use your eye movements (and blink to click).</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eye:app", host="0.0.0.0", port=8000, reload=True)

import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

# Initialize Mediapipe Hands for hand tracking
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)

# Capture webcam (set up once)
cap = cv2.VideoCapture(0)
prev_x, prev_y = pyautogui.position()
smoothing_factor = 0.3  # Smoothing factor for cursor movement
DEBOUNCE_TIME = 0.3  # Seconds for debouncing
last_action_time = time.time()
running = True

def _process_frame(frame):
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    return frame, results

def _handle_hand_tracking(results):
    global prev_x, prev_y, last_action_time
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            # Map hand position (assumed frame width = 800) to screen X coordinate
            cx = int(index_tip.x * 800)
            new_x = prev_x + (cx - prev_x) * smoothing_factor
            # Update X coordinate; Y remains unchanged for simplicity
            prev_x, prev_y = new_x, prev_y
            pyautogui.moveTo(new_x, prev_y, duration=0.05)

async def _tracking_loop():
    global running
    while running:
        ret, frame = cap.read()
        if not ret:
            break
        processed_frame, results = _process_frame(frame)
        _handle_hand_tracking(results)
        await asyncio.sleep(0.01)

def start_tracking():
    logging.info("Hand tracking (hand1) started.")
    global running
    running = True
    loop = asyncio.get_event_loop()
    loop.create_task(_tracking_loop())

def terminate_tracking():
    global cap, running
    logging.info("Hand tracking (hand1) terminated.")
    running = False
    cap.release()
    cv2.destroyAllWindows()

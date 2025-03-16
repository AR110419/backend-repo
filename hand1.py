import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import os
import platform

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

while cap.isOpened():
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

            # Get necessary landmarks
            index_tip = landmarks[8]
            middle_tip = landmarks[12]
            ring_tip = landmarks[16]
            pinky_tip = landmarks[20]
            thumb_tip = landmarks[4]
            palm_base = landmarks[0]

            # Convert hand coordinates to screen coordinates
            cx, cy = int(index_tip.x * screen_width), int(index_tip.y * screen_height)

            # Smooth cursor movement
            new_x = prev_x + (cx - prev_x) * smoothing_factor
            new_y = prev_y + (cy - prev_y) * smoothing_factor
            prev_x, prev_y = new_x, new_y

            fingers = [index_tip, middle_tip, ring_tip, pinky_tip]
            current_time = time.time()

            # Gesture recognition with debouncing
            if sum(f.y < palm_base.y for f in fingers) >= 3 and (current_time - last_action_time > DEBOUNCE_TIME):
                print("🔆 Increasing Brightness")
                change_brightness(True)  # Increase brightness
                last_action_time = current_time

            elif sum(f.y > palm_base.y for f in fingers) >= 3 and (current_time - last_action_time > DEBOUNCE_TIME):
                print("🔅 Decreasing Brightness")
                change_brightness(False)  # Decrease brightness
                last_action_time = current_time

            elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y:
                print(f"🎯 Moving Cursor to ({new_x}, {new_y})")
                pyautogui.moveTo(new_x, new_y, duration=0.05)  # Faster cursor movement

            elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y and ring_tip.y > palm_base.y and (current_time - last_action_time > DEBOUNCE_TIME):
                print("📄 Scrolling Page")
                pyautogui.scroll(-10)  # Increased scroll step from -5 to -10
                last_action_time = current_time

            elif all(f.y < palm_base.y for f in [middle_tip, ring_tip, pinky_tip]) and index_tip.y > palm_base.y and (current_time - last_action_time > DEBOUNCE_TIME):
                print("📸 Taking Screenshot")
                pyautogui.screenshot().save(f'screenshot_{int(time.time())}.png')
                last_action_time = current_time

            elif abs(index_tip.y - middle_tip.y) < 0.015 and abs(index_tip.x - thumb_tip.x) < 0.015 and (current_time - last_action_time > DEBOUNCE_TIME):
                print("🖱️ Double Click")
                pyautogui.doubleClick()
                last_action_time = current_time

    cv2.imshow('Hand Gesture Control', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

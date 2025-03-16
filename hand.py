import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)
cap = cv2.VideoCapture(0)

screen_width, screen_height = pyautogui.size()
prev_x, prev_y = pyautogui.position()
smoothing_factor = 0.3  # Adjust for smoother cursor movement
last_action_time = time.time()  # Prevent repeated actions in a short time

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
            if all(f.y < palm_base.y for f in fingers) and (current_time - last_action_time > 0.5):
                print("🔆 Increasing Brightness")
                pyautogui.hotkey('volumeup')  # Adjust for OS-specific brightness control
                last_action_time = current_time

            elif all(f.y > palm_base.y for f in fingers) and (current_time - last_action_time > 0.5):
                print("🔅 Decreasing Brightness")
                pyautogui.hotkey('volumedown')  # Adjust for OS-specific brightness control
                last_action_time = current_time

            elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y:
                print(f"🎯 Moving Cursor to ({new_x}, {new_y})")
                pyautogui.moveTo(new_x, new_y, duration=0.05)  # Faster cursor movement

            elif index_tip.y < palm_base.y and middle_tip.y < palm_base.y and ring_tip.y > palm_base.y and (current_time - last_action_time > 0.5):
                print("📄 Swiping Page")
                pyautogui.hotkey('ctrl', 'right')  # Swipe right
                last_action_time = current_time

            elif all(f.y < palm_base.y for f in [middle_tip, ring_tip, pinky_tip]) and index_tip.y > palm_base.y and (current_time - last_action_time > 0.5):
                print("📸 Taking Screenshot")
                pyautogui.screenshot().save(f'screenshot_{int(time.time())}.png')
                last_action_time = current_time

            elif abs(index_tip.y - middle_tip.y) < 0.02 and (current_time - last_action_time > 0.5):
                print("🖱️ Double Click")
                pyautogui.doubleClick()
                last_action_time = current_time

    cv2.imshow('Hand Gesture Control', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

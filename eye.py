import cv2 #capturing nd processing video
import mediapipe as mp #facial landmark
import pyautogui #controls mouse

cam = cv2.VideoCapture(0) # capturing the video from index 0 which will be the first appearing video
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True) #initialize mediapipe
# we need to scale out the cursor for the whole screen rather than being limited just to the frame
# for scaling it, we need to know the screen size which can be known by the mentioned line:
screen_w, screen_h = pyautogui.size() #screen width nd height
while True:
    _, frame = cam.read() # command to read the video
    frame = cv2.flip(frame, 1) # flip code 1 is for flipping the image frame vertically
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # command to convert the colour of the image captured
    output = face_mesh.process(rgb_frame) # op will be the processed rgb frame(extrct facial land mark)
    landmark_points = output.multi_face_landmarks
    frame_height, frame_width, _ = frame.shape # getting the height and width of the frame from the shape func
    if landmark_points: #cursor movement
        landmarks = landmark_points[0].landmark
        for id, landmark in enumerate(landmarks[474:478]): # identifying the eyes of the face by using that specific index rather than detecting the whole face
            # the landmark points will be given as a ratio i.e. between 0 and 1, so we need to multiply with the frame width and height
            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)
            # converting the points into integer from decimal because we need to draw a circle, so we need int values
            cv2.circle(frame, (x,y), 3, (0, 0, 255))
            if id == 1:
                screen_x = screen_w / frame_width * x
                screen_y = screen_h / frame_height * y
                pyautogui.moveTo(screen_x, screen_y) #movement of cursor

        left = [landmarks[145], landmarks[159]] #eyelid blink
        for landmark in left:
            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)
            # converting the points into integer from decimal because we need to draw a circle, so we need int values
            cv2.circle(frame, (x, y), 3, (0, 255, 255))
        if (left[0].y - left[1].y) < 0.007:
            pyautogui.click()
            pyautogui.sleep(1)
            # print('click')
    # print(landmark_points)
    # prints the landmarks points detected for the face when getting captured

    cv2.imshow('Eye controlled mouse', frame)
    cv2.waitKey(1) # waiting for a delay of 1 sec
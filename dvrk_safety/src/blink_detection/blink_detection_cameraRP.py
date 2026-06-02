import numpy as np
import cv2 as cv
cap = cv.VideoCapture(Test_4.mp4)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)  # Lower resolution for faster processing
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv.CAP_PROP_FPS, 1)  # Lower frame rate to reduce processing load






if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    # Display the resulting frame
    cv.imshow('frame', gray)

    width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv.CAP_PROP_FPS)
    print(width)
    print(height)
    print(fps)

    if cv.waitKey(1) == ord('q'):
        break
# When everything done, release the capture
cap.release()
cv.destroyAllWindows()
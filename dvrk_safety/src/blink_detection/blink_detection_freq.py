import cv2
import numpy as np
import math

def frequency_analysis(roi):
    # Apply 2D Fourier Transform
    f_transform = np.fft.fft2(roi)
    
    # Shift zero frequency components to the center
    f_transform_shifted = np.fft.fftshift(f_transform)
    
    # Compute magnitude spectrum
    magnitude_spectrum = np.log(np.abs(f_transform_shifted) + 1)

    return magnitude_spectrum

# Function to detect blinks using frequency domain analysis
def detect_blink(frequency_spectrum, threshold=100):
    # Calculate the average magnitude in the frequency spectrum
    average_magnitude = np.mean(frequency_spectrum)

    # Detect blink if the average magnitude is below the threshold
    return average_magnitude < threshold


# tuplifies things for opencv
def tup(p):
    return (int(p[0]), int(p[1]));

# returns the center of the box
def getCenter(box):
    x = box[0];
    y = box[1];
    x += box[2] / 2.0;
    y += box[3] / 2.0;
    return [x,y];

# rescales image by percent
def rescale(img, scale):
    h,w = img.shape[:2];
    h = int(h*scale);
    w = int(w*scale);
    return cv2.resize(img, (w,h));

# load video
cap = cv2.VideoCapture("Test_4.mp4");
#cap = cv2.VideoCapture(2)
scale = 0.5;


# font stuff
font = cv2.FONT_HERSHEY_SIMPLEX;
org = (50, 50);
fontScale = 1;
font_color = (0, 0, 0);
thickness = 2;

# set up tracker
tracker = cv2.legacy.TrackerCSRT_create(); # I'm using OpenCV 3.4
backup = cv2.legacy.TrackerCSRT_create();

# grab the first frame
ret, frame = cap.read();
frame = rescale(frame, scale);

# init tracker
box = cv2.selectROI(frame, False);
tracker.init(frame, box);
backup.init(frame, box);
cv2.destroyAllWindows();

# set center bounds
width = 75;
height = 60;

# save numbers
file_index = 0;

# blink counter
blinks = 0;
blink_thresh = 80;
blink_trigger = True;
x1 = 0
x2 = 300
y1 = 0
y2 = 300

# show video
done = False;
while not done:
    # get frame
    ret, frame = cap.read();
    if not ret:
        break;
    frame = rescale(frame, scale);

    # choose a color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV);
    h,s,v = cv2.split(hsv);
    channel = s;

    # Extract eye region (you may need to fine-tune the coordinates)
    eye_roi = frame[y1:y2, x1:x2]  # Change: Extract eye region from the frame
    cv2.imshow("Eye Region", eye_roi)
    cv2.waitKey(0)  # Wait until a key is pressed to continue
    cv2.destroyAllWindows()


    # Perform frequency domain analysis
    frequency_spectrum = frequency_analysis(eye_roi)  # Change: Analyze frequency components

    # Detect blink based on frequency domain analysis
    is_blink = detect_blink(frequency_spectrum)  # Change: Determine if a blink has occurred

    # show
    cv2.imshow("Frame", frame);
    key = cv2.waitKey(1);

    # check keypress
    done = key == ord('q');
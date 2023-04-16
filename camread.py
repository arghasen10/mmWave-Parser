import time

import cv2

# Create an object to read
# from camera
video = cv2.VideoCapture(2)
startime = time.time()
# We need to check if camera
# is opened previously or not
if video.isOpened() == False:
    print("Error reading video file")

# We need to set resolutions.
# so, convert them from float to integer.
frame_width = int(video.get(3))
frame_height = int(video.get(4))

size = (frame_width, frame_height)

# Below VideoWriter object will create
# a frame of above defined The output
# is stored in 'filename.avi' file.
filename = "videodata/"
filename += time.strftime("%Y%m%d_%H%M%S")
filename += ".avi"
result = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*"MJPG"), 30, size)

while True:
    ret, frame = video.read()
    currenttime = time.time()
    if ret == True:
        if currenttime - startime > 360:
            # video.release()
            # result.release()
            # time.sleep(1)
            filename = "videodata/"
            filename += time.strftime("%Y%m%d_%H%M%S")
            filename += ".avi"
            result = cv2.VideoWriter(
                filename, cv2.VideoWriter_fourcc(*"MJPG"), 30, size
            )
            startime = time.time()
        timenow = time.strftime("%m/%d/%Y, %H:%M:%S")
        # Write the frame into the
        # file 'filename.avi'
        cv2.putText(
            frame,
            timenow,
            (50, 50),
            cv2.FONT_HERSHEY_COMPLEX,
            1,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
        result.write(frame)

        # Display the frame
        # saved in the file

        cv2.imshow("Frame", frame)

        # Press S on keyboard
        # to stop the process
        if cv2.waitKey(30) & 0xFF == ord("s"):
            break

    # Break the loop
    else:
        break

video.release()
result.release()

# Closes all the frames
cv2.destroyAllWindows()

print("The video was successfully saved")

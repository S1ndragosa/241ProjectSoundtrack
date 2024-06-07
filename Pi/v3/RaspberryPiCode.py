import cv2
import requests
import time

# URL of the Flask server
url = "ip address here"

cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame")
        break

    img_name = "opencv_frame.png"
    cv2.imwrite(img_name, frame)
    print("{} written!".format(img_name))

    # Send the image to the Flask server
    with open(img_name, 'rb') as f:
        files = {'file': (img_name, f, 'image/png')}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            print(response.json())
        else:
            print("Failed to upload file. Status code:", response.status_code)
            print("Response:", response.text)
    
    # Wait for a short period before capturing the next frame
    time.sleep(4)  # Adjust the sleep time as needed

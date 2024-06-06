# app.py
from flask import Flask, request, jsonify
import os
import cv2
from deepface import DeepFace
import argparse
import threading

import io
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy.util as util
import json
import random
import threading
from statistics import mode, StatisticsError

# import the necessary packages
import numpy as np

# base directory for he project
base_dir = "Base directory goes here"

#intialise flask application
app = Flask(__name__)
# set upload folder path 
UPLOAD_FOLDER = os.path.join(base_dir, "uploads")
#Configure the flask to use the specified upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define paths for the models and prototxt files
faceProto = os.path.join(base_dir, "opencv_face_detector.pbtxt")
faceModel = os.path.join(base_dir, "opencv_face_detector_uint8.pb")
ageProto = os.path.join(base_dir, "age_deploy.prototxt")
ageModel = os.path.join(base_dir, "age_net.caffemodel")
genderProto = os.path.join(base_dir, "gender_deploy.prototxt")
genderModel = os.path.join(base_dir, "gender_net.caffemodel")

#age and emotion list
emotion_data = []
age_data=[]
# Create a lock for managing access to shared resources
lock = threading.Lock()

#variables neededfor the spotify api
input_file = open('api keys.txt goes here', 'r')
list_codes = input_file.readlines()
client_id = list_codes[0].strip()
client_secret = list_codes[1].strip()
redirect_uri = list_codes[2].strip()
username = list_codes[3].strip()
print(username)
scope = ['user-read-currently-playing', 'user-modify-playback-state', 'playlist-modify-public', 'playlist-modify-private', 'playlist-read-private']
play_list = list_codes[4].strip()
song_list = []
input_age = '109'

#initialise the spotify client 
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id, client_secret, redirect_uri, scope))
#prompt the user token 
token = util.prompt_for_user_token(username, scope,client_id,client_secret,redirect_uri)
if token:
    sp = spotipy.Spotify(auth=token)
else:
    print("Can't get token for", username)

## YOU NEED SPOTIFY TO BE ON AND ALREADY PLAYING A SONG BEFORE THIS WILL WORK
def add_song(search_query , index):
    #searching and processing the made by spotify playlist
    size_hitplaylist = 0
    try:
        spotify_search = sp.search(search_query, limit = 10, offset=0, type='playlist', market="NZ")
        hit_playlist = spotify_search['playlists']['items'][index]["uri"]
        selected_playlist = sp.playlist(hit_playlist, fields=None, market="NZ", additional_types=('track'))
        size_hitplaylist = sp.playlist_items(hit_playlist,fields= None, limit=100, offset=0, market="NZ")["total"]
        selected_song_index = random.randint(0,size_hitplaylist - 1)

    #gets the song from the processsed .json
        playable_song = selected_playlist["tracks"]["items"][selected_song_index]["track"]["id"]
        ##sp.add_to_queue(playable_song)
        song_list.append(playable_song) 
    except IndexError:
        print(f'Search failed, going up an index({index})')
        add_song(search_query, index + 1)
    # pretty_json = json.dumps(selected_playlist, indent=4)
    # output_file = open("output.txt", "w")
    # output_file.write(pretty_json)

#Gets a random age from the age buckets and takes into account the emotion of the person
def searchAge(agerange, emotion):
    #gets the age range from the age buckets
    age = agerange.strip('()').split('-')

    # Generate a random age within the specified range
    input_age = random.randint(int(age[0]), int(age[1]))
    print(input_age)
    #gets the year of when the age of the person is in their teenage years
    year = str(2024 - int(input_age) + 15)
    if input_age > 15:
        if emotion == 'sad':
            search_query = 'Best of Rock: ' + year + ' By Spotify'

        elif emotion == 'angry':
            search_query = 'Best of metal ' + year

        else:
            search_query = 'Top hits of ' + year + ' by Spotify'
    else:
        search_query = "Top hits of 2023"
    print(search_query, f'({input_age})')
    add_song(search_query, 0)

# mean values for the model's preprocessing step
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
# List of age ranges and genders 
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList = ['Male', 'Female']

# Load the pre-trained models for face, age, and gender detection
faceNet = cv2.dnn.readNet(faceModel, faceProto)
ageNet = cv2.dnn.readNet(ageModel, ageProto)
genderNet = cv2.dnn.readNet(genderModel, genderProto)

# path to the image file
img_name = os.path.join(base_dir, "uploads/opencv_frame.png")

def highlightFace(net, frame, conf_threshold=0.7):
    #make a copy of the input frame
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    #create blob from image for face detection
    blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    #iterate over all detected faces
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            #calculate coordinates for the box
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            #draw the box
            cv2.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight / 150)), 8)
    return frameOpencvDnn, faceBoxes

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
#calculates the most common age and emotion from the emoion and age list
def calculate_age_mode():
    global age_data
    threading.Timer(30.0, calculate_age_mode).start()  # Schedule the function to run every 30 seconds
    with lock:
        if age_data:
            try:
                age_mode = mode(age_data)
                emotion_mode = mode(emotion_data)
                print(f"Mode of age bucket values: {age_mode}")
                print(f"Mode of emotion values: {emotion_mode}")
                #calls searchAge method to give the most common emotion and age
                searchAge(age_mode, emotion_mode)   
                #adds the song to the playlist
                sp.playlist_add_items(play_list, song_list)

                # Here you could call a function to handle the age mode, e.g., searchAgeMode(age_mode)
            except StatisticsError:
                print("No unique mode found")
            age_data.clear()  # Clear the list after processing

calculate_age_mode()  # Start the timer
#gets the ages from the frame 
def get_age():
    global song_list
    song_list = []  # Clear the song list at the start of each request

    frame = cv2.imread(img_name)
    if frame is None:
        print("Could not read input image")
        exit()

    padding = 20
    resultImg, faceBoxes = highlightFace(faceNet, frame)
    if not faceBoxes:
        print("No face detected")
    else:
        for faceBox in faceBoxes:
            face = frame[max(0, faceBox[1] - padding):
                        min(faceBox[3] + padding, frame.shape[0] - 1),
                        max(0, faceBox[0] - padding):
                        min(faceBox[2] + padding, frame.shape[1] - 1)]

            blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        
            genderNet.setInput(blob)
            genderPreds = genderNet.forward()
            gender = genderList[genderPreds[0].argmax()]

            ageNet.setInput(blob)
            agePreds = ageNet.forward()
            age = ageList[agePreds[0].argmax()]
            # Emotion analysis
            result = DeepFace.analyze(face, actions=['emotion'], enforce_detection=False)
            emotion = result[0]['dominant_emotion']
            with lock:
                emotion_data.append(emotion)  # Add emotion to the data list
                age_data.append(age)  # Add age to the data list
            print(age_data)
            cv2.putText(resultImg, f'{gender}, {age}', (faceBox[0], faceBox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.imshow("Detecting age and gender", resultImg)
        cv2.destroyAllWindows()


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
     # Check if 'file' is present in the request
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    # Check if a file is selected for uploading
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    # If a file is selected, save it to the upload folder
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # After saving the file, call the get_age function
        get_age()
         # Return success message if file is uploaded successfully
        return jsonify({'message': f'File {filename} successfully uploaded'}), 200
# Start the Flask application 
if __name__ == '__main__':
    # Run the application on all network interfaces with debugging enabled
    app.run(host = '0.0.0.0', debug=True)

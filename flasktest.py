import datetime
import os
from dotenv import load_dotenv
import requests
from flask import Flask, jsonify, redirect, session, request
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import random
import json
import math

load_dotenv()

app = Flask(__name__)
app.secretkey = '123'

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
username = os.getenv("SPOTIPY_USERNAME")
playlist = os.getenv("SPOTIPY_PLAYLIST")

scope = ['user-read-currently-playing', 'user-modify-playback-state', 'playlist-modify-public', 'playlist-modify-private', 'playlist-read-private', 'user-read-playback-state']
song_list = []

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id, client_secret, redirect_uri, scope))
token = util.prompt_for_user_token(username, scope,client_id,client_secret,redirect_uri)
if token:
    sp = spotipy.Spotify(auth=token)
else:
    print("Can't get token for", username)

@app.route('/')
def index():
    return "This my test web server<br><a href='/tutorial'/>Clicky here</a><br><a href='/get_json'/>magic get pi data button</a>"

@app.route('/tutorial')
def tutorial():
    return 'Put your stuff here'


@app.route('/receive_data', methods=['POST'])
def receive_data():
    data = request.json
    process_data(data)
    return jsonify({'message': 'Data received successfully'}), 200

@app.route('/process_data')
def process_data(data):
    sum_ages = 0
    print(data)

    for i in range(len(data["Items"])):
        data_index = data["Items"][i]["Age"]
        age_data = data_index.strip('()').split('-')
        random_age = random.randint(int(age_data[0]), int(age_data[1]))
        sum_ages += random_age
    average_age = math.ceil(sum_ages / (len(data["Items"])))
    print(average_age)
    query_age = 2024 - average_age + 8 - 1
    # emotion_data = data['Emotion']
    


    search_query = "Top hits of " + str(query_age) + " by Spotify"
    print(search_query)
    add_song(search_query)
    sp.playlist_add_items(playlist, song_list)
    
def add_song(search_query):
    #searching and processing the made by spotify playlist
    song_list.clear()
    size_hitplaylist = 0
    spotify_search = sp.search(search_query, limit = 10, offset=0, type='playlist', market="NZ")
    hit_playlist = spotify_search['playlists']['items'][0]["uri"]
    selected_playlist = sp.playlist(hit_playlist, fields=None, market="NZ", additional_types=('track'))
    size_hitplaylist = sp.playlist_items(hit_playlist,fields= None, limit=100, offset=0, market="NZ")["total"]
    selected_song_index = random.randint(0,size_hitplaylist - 1)

    #gets the song from the processsed .json
    try:
        playable_song = selected_playlist["tracks"]["items"][selected_song_index]["track"]["id"]
        sp.add_to_queue(playable_song)
        song_list.append(playable_song)
    except IndexError:
        print("Error Detected, printing json")
        pretty_json = json.dumps(selected_playlist, indent=4)
        output_file = open("output.txt", "w")
        output_file.write(pretty_json)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug= True)



import os
import io
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy.util as util
import json
import random
from dotenv import load_dotenv

# reads .txt file to get api keys

load_dotenv()
client_id = os.getenv("SPOTIPY_CLIENT   _ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
username = os.getenv("SPOTIPY_USERNAME")
playlist = os.getenv("SPOTIPY_PLAYLIST")

scope = ['user-read-currently-playing', 'user-modify-playback-state', 'playlist-modify-public', 'playlist-modify-private', 'playlist-read-private', 'user-read-playback-state']
song_list = []
input_age = '109'

# verifies spotify account doesn't got any problems
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id, client_secret, redirect_uri, scope))
token = util.prompt_for_user_token(username, scope,client_id,client_secret,redirect_uri)
if token:
    sp = spotipy.Spotify(auth=token)
else:
    print("Can't get token for", username)

## YOU NEED SPOTIFY TO BE ON AND ALREADY PLAYING A SONG BEFORE THIS WILL WORK
def add_song(search_query):
    #searching and processing the made by spotify playlist
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
        print("error detectedokmnikdwasvghdvbghkas")
        pretty_json = json.dumps(selected_playlist, indent=4)
        output_file = open("output.txt", "w")
        output_file.write(pretty_json)



for track_or_episode in users_queue['queue']:
    print(f"Queued: {track_or_episode['name']}")
# test if this method would work
while True:
    input_age = input("How old are you? (Enter '0' to exit) ")
    if input_age == '0':
        break
    elif int(input_age) < 15:
        break
    else:
        year = str(2024 - int(input_age) + 15)
        print(year)
        search_query = "Top hits of" + year + " by Spotify"
        add_song(search_query)


sp.playlist_add_items(play_list, song_list)
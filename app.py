from flask import Flask, redirect, request, session, url_for, render_template
import subprocess
import requests
import json
import webbrowser

# Spotify API credentials
from credentials import *

CLIENT_ID = client_id
CLIENT_SECRET = client_secret
REDIRECT_URI = 'http://localhost:3000/callback'
SCOPE = 'playlist-modify-public'


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    auth_url = (
        'https://accounts.spotify.com/authorize?'
        f'client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}'
    )
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    auth_token_url = 'https://accounts.spotify.com/api/token'
    auth_token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    auth_token_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    auth_response = requests.post(auth_token_url, data=auth_token_data, headers=auth_token_headers)
    auth_response_data = auth_response.json()
    session['access_token'] = auth_response_data.get('access_token')
    if session['access_token']:
        return redirect(url_for('create_playlist'))
    else:
        return 'Authorization failed. Please try again.'


@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    if request.method == 'POST':
        playlist_name = request.form['playlist_name']
        artist_name = request.form['artist_name']
        access_token = session.get('access_token')
        if not access_token:
            return redirect(url_for('login'))

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        user_profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        user_profile_data = user_profile_response.json()
        user_id = user_profile_data['id']

        create_playlist_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
        playlist_data = json.dumps({
            'name': playlist_name,
            'public': True
        })

        create_response = requests.post(create_playlist_url, data=playlist_data, headers=headers)
        if create_response.status_code == 201:
            playlist_id = create_response.json()['id']
            subprocess.run(['python', 'wrapper.py', artist_name])
            add_tracks_to_playlist(playlist_id, access_token)
            return 'Playlist created and tracks added successfully!'
        else:
            return 'Failed to create playlist.'

    return render_template('create_playlist.html')


def add_tracks_to_playlist(playlist_id, access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    with open('setlist.txt', 'r', encoding="UTF-8") as file:
        lines = file.readlines()
        artist_name = lines[0].strip()
        tracks = {line.strip() for line in lines[1:]}

    track_uris = []
    for track in tracks:
        query = f'{track} artist:{artist_name}'
        search_url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=1'
        search_response = requests.get(search_url, headers=headers)
        search_results = search_response.json()
        
        if search_results['tracks']['items']:
            track_uris.append(search_results['tracks']['items'][0]['uri'])
        else:
            # If no track found, get the top result (track or podcast)
            query = f'{track} {artist_name}'
            type = "episode%2Ctrack"
            fallback_search_url = f'https://api.spotify.com/v1/search?q={query}&type={type}&limit=1'
            fallback_search_response = requests.get(fallback_search_url, headers=headers)
            fallback_search_results = fallback_search_response.json()

            if fallback_search_results['tracks']['items']:
                track_uris.append(fallback_search_results['tracks']['items'][0]['uri'])
            if fallback_search_results['episodes']['items']:
                track_uris.append(fallback_search_results['episodes']['items'][0]['uri'])

    if track_uris:
        add_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        add_tracks_data = json.dumps({
            'uris': track_uris
        })
        requests.post(add_tracks_url, data=add_tracks_data, headers=headers)


if __name__ == '__main__':
    webbrowser.open('http://localhost:3000/')
    app.run(port=3000, debug=True)
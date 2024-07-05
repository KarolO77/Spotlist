from credentials import *
import requests
import json


base_url = "https://api.spotify.com/v1/"
auth_url = 'https://accounts.spotify.com/api/token'
data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
}

auth_response = requests.post(auth_url, data=data)
access_token = auth_response.json().get('access_token')

print(access_token)
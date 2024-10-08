import requests
import os
import urllib.parse

from flask import Flask, redirect, request, jsonify, session
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

token_url = os.getenv("TOKEN_URL")
api_base_url = os.getenv("API_BASE_URL")
auth = os.getenv("AUTH_URL")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

@app.route('/')
def index():
    return "Welcome! <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-top-read user-read-email'

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': redirect_uri,
        'show_dialog': True
    }

    auth_url = f"{auth}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    # error handling when request is made
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(token_url, data=req_body)
        token = response.json()

        session['access_token'] = token['access_token']
        session['refresh_token'] = token['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token['expires_in']

    return redirect('/top-artists')

@app.route('/top-artists')
def get_artists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(api_base_url + 'me/top/artists', headers=headers)

    artists = response.json()

    return jsonify(artists)

# refresh token
@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        request_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(token_url, data=request_body)
        new_token = response.json()

        session['access_token'] = new_token['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token['expires_at']

        return redirect('/top-artists')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

import requests
import os
import urllib.parse

from flask import Flask, redirect
from dotenv import load_dotenv

load_dotenv()

token_url = os.getenv("TOKEN_URL")
api_base_url = os.getenv("API_BASE_URL")
auth = os.getenv("AUTH_URL")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

app = Flask(__name__)
app.secret_key = '11231231231231'

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

if __name__ == '__main__':
    app.run()

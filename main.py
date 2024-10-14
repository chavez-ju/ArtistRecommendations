from flask import Flask, render_template, redirect, request, jsonify, session
from dotenv import load_dotenv
from datetime import datetime, timedelta

from werkzeug.utils import secure_filename

import requests
import os
import urllib.parse

from utils import *

load_dotenv()

token_url = os.getenv("TOKEN_URL")
api_base_url = os.getenv("API_BASE_URL")
auth = os.getenv("AUTH_URL")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UploadFileForm()
    if form.validate_on_submit():
        # First grab the file
        file = form.file.data

        # Then save the file
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))

        return redirect('/login') # direct users to /login after file has been uploaded
    return render_template('index.html', form=form)

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
    # Error handling when request is made
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

    return redirect('/get-recommendations')

@app.route('/get-recommendations')
def get_recommendations():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    # Get user's top artists
    response = requests.get(api_base_url + 'me/top/artists', headers=headers)
    
    # Gathers user's favorite artists name and genre data from json
    artist_names = get_names(response.json())
    genres = get_genres(response.json())

    lineup_names = read_file()

    # First, read names of favorite arists
    set_i = set(lineup_names).intersection(set(artist_names))

    # Get genre info on lineup artists, by searching with their name
    for name in lineup_names:
        response = requests.get(api_base_url + 'search?q=' + name + '&type=artist&limit=1', headers=headers)
        lineup_artist_genres = item_search_get_genres(response.json())
        if len(lineup_artist_genres) != 0:
            # Threshold set to 50% or more
            thresh = len(lineup_artist_genres) // 2 + (len(lineup_artist_genres) % 2 > 0)
            count = 0
            for i in lineup_artist_genres:
                if i in genres:
                    count += 1
            if count >= thresh:
                set_i.add(name)
        
    print(list(set_i))

    return list(set_i)

# Refresh token
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

        return redirect('/get-recommendations')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

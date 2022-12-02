from dotenv import load_dotenv
import json
from urllib import response
from flask import Flask, request, url_for, session, redirect, jsonify, render_template, flash
from numpy import rec
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
import json
import requests
from collections import Counter
from datetime import datetime
import os

load_dotenv()



app = Flask(__name__)
app.debug=True
pulled_data = pd.DataFrame()
app.secret_key = os.getenv("app.secret_key")
lastfmapi= os.getenv("lastfmapi")
lastfmsecret= os.getenv("lastfmsecret")


app.config['SESSION_COOKIE_NAME'] = 'COOKIEMONSTER'

TOKEN_INFO = "token_info"


@app.route('/')


@app.route('/home', methods=['POST', 'GET'])
def home():
    if session.get('logged_in') == True:
        try:
            token_info = session.get(TOKEN_INFO, None)
            sp = spotipy.Spotify(auth=token_info['access_token'])
            user_id = sp.current_user()
            user_id = user_id['id']
            return(render_template('logged_in_home.html', username = user_id))
        except spotipy.client.SpotifyException:
            print("got exception")


    return(render_template('logged_out_home.html'))



@app.route('/login', methods = ['POST', 'GET'])
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    #session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code,check_cache=False)
    session[TOKEN_INFO] = token_info
    session['logged_in'] = True
    return redirect(url_for('home', _external=True))







@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    print((session.get(TOKEN_INFO, None)))
    print("Logged Out")
    return redirect(url_for('home', _external=False))

@app.route('/getTracks', methods=['POST', 'GET'])
def getTracks():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect(url_for("login", _external=False))

    #if int(len(smaller_data.index)) > 0:
        #return(render_template('tracklist.html',  tables=[smaller_data.to_html(classes='data',index=False)], titles=smaller_data.columns.values))
    else:
        return(render_template('generate.html'))


@app.route('/generate_rec', methods=['POST', 'GET'])
def generate_rec():
    print("1")

    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()
    user_id = user_id['id']
    tracklist = (sp.current_user_top_tracks(limit=5, offset=0, time_range='medium_term'))

    first = pd.DataFrame(tracklist['items'])

    songtotal = pd.DataFrame.from_dict(first)
    songtotal =  int(len(songtotal.index))
    songuri = first['id']
    songuri = songuri.tolist()

    artisturi = first['artists'].squeeze()
    artisturi = pd.DataFrame(artisturi)
    artisturi = artisturi.astype(str)
    artisturi = artisturi['artists'].apply(lambda st: st[st.find("'id': '")+1:st.find("', 'name")])
    artisturi = artisturi.str.removeprefix("id': '")
    artisturi = artisturi.squeeze()
    artisturi = artisturi.tolist()

    print("2")
    genreseeds = []
    for x in range(len(artisturi)):
        genres = sp.artist(artisturi[x])['genres']
        genreseeds = genreseeds + genres
    
    topgenres = Counter(genreseeds)
    topgenres = topgenres.most_common(1)
    topgenres = [i[0] for i in topgenres]

    artistnamesr = first['artists'].squeeze()
    artistnamesr = pd.DataFrame(artistnamesr)
    artistnamesr = artistnamesr.astype(str)
    artistnamesr = artistnamesr['artists'].apply(lambda st: st[st.find("'name': '")+1:st.find("', 'type':")])
    artistnamesr = artistnamesr.str.removeprefix("name': '")
    artistnamesr = artistnamesr.squeeze()
    artistnamesr = artistnamesr.tolist()

    songname = first['name']
    songname = songname.tolist()



    tempartistlist = []
    tempsongurilist = []

    lengtha = len(artisturi)



    recommended_data = pd.DataFrame()

    finrecnames = []
    finrecid = []
    finrecartists = []
    finalbumart  = []
    print(songuri)
    print(artisturi)
    for p in range(lengtha):
        print(p)
        tempsongurilist = [songuri[p]]
        tempartistlist = [artisturi[p]]

        recsongs = sp.recommendations(seed_artists=tempartistlist, seed_genres=topgenres, seed_tracks=tempsongurilist, limit=20)
        recsongsdf = pd.DataFrame(recsongs['tracks'])
        recsongsnames = recsongsdf['name']
        recsongsid = recsongsdf['id']
        recartists = recsongsdf['artists']
        albumart = recsongsdf['album']
        recsongsnames = recsongsnames.tolist()
        recsongsid = recsongsid.tolist()
        recartists = recartists.tolist()
        albumart = albumart.tolist()
        finrecnames = finrecnames + recsongsnames
        finrecid = finrecid + recsongsid
        finrecartists = finrecartists + recartists
        finalbumart = finalbumart + albumart
    print("3")

    artp = pd.DataFrame(finrecartists)
    arter = artp.iloc[:, 0]
    arter = pd.DataFrame(arter)
    arter.columns = ['Artist Name'] 
    arter = arter.astype(str)
    arter = arter['Artist Name'].apply(lambda st: st[st.find("'name': '")+1:st.find("', 'type':")])
    arter = arter.str.removeprefix("name': '")
    arter = arter.squeeze()
    arter = arter.tolist()

    pfinart = pd.DataFrame(finalbumart)
    finart = pfinart['images']
    finart = pd.DataFrame(finart)
    finart = finart.astype(str)
    finart = finart['images'].apply(lambda st: st[st.find("64, ")+1:st.find(", 'width': 64}")])
    finart = finart.str.removeprefix("4, 'url': '")
    finart = finart.str.removesuffix("'")
    finarta = pd.DataFrame(finart)
    finarta.columns = ['Album Art']
    finarta = finarta.squeeze()
    finarta = finarta.tolist()

    finrecnames = pd.DataFrame(finrecnames)
    finrecnames = finrecnames[0].str[:20]

    recommended_data[' '] = finarta
    recommended_data['Rec. Song Names'] = finrecnames
    recommended_data['Artist'] = arter
    recommended_data['Rec. Song IDs'] = finrecid
    


    smaller_data = recommended_data.sample(n = 20)
    smaller_data = smaller_data.drop_duplicates()
    pass_data = smaller_data['Rec. Song IDs']
    display_data = smaller_data.drop(['Rec. Song IDs'], axis=1)

    pass_data = pass_data.tolist()
    session["pass_data"] = pass_data
    print("4")
    return render_template("playlist.html", column_names=display_data.columns.values, row_data=list(display_data.values.tolist()),image_column = " ",username = user_id,zip=zip)
    


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 59

    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh-token'])
    return token_info

@app.route('/create_playlist', methods=['POST', 'GET'])
def create_playlist():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()
    user_id = user_id['id']
    listedsongs = session.get("pass_data")
    print(user_id)
    playlist = sp.user_playlist_create(user_id,"Created_Playlist",public=None,collaborative=None, description=None)
    playlist_id = playlist["id"]
    sp.playlist_add_items(playlist_id, listedsongs)
    flash("Playlist Added")
    return redirect(url_for('home', _external=False))

@app.route('/melon', methods=['POST', 'GET'])
def melon():
    return render_template("melon.html")

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id='119bbbdf4b72475b8ae6a2766285c60d',
        client_secret='a3b6fddb7b9643d192908573f1b2f1e5',
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-top-read,playlist-modify-private",
        show_dialog=True,
        requests_session=False)


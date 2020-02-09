from flask import Flask, jsonify, request
from flask_cors import CORS
from plex.classes import PlexWrapper

app = Flask(__name__)
CORS(app)

@app.route("/movies/dupes")
def get_movies():
    dupes = PlexWrapper().get_dupe_movies()
    return jsonify(dupes)


@app.route("/movies/samples")
def get_movies_samples():
    samples = PlexWrapper().get_movie_sample_files()
    return jsonify(samples)


@app.route("/delete/media", methods=["POST"])
def delete_media():
    content = request.get_json()
    movie_key = content["movie_key"]
    media_id = content["media_id"]

    movie = PlexWrapper().get_movie(movie_key)

    for media in movie.media:
        if media.id == media_id:
            print(movie.title, media.id)
            for part in media.parts:
                print(part.file)
            media.delete()
    return jsonify({
        'success': True
    })

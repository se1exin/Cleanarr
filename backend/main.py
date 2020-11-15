import os

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from plex.classes import PlexWrapper

app = Flask(__name__)
CORS(app)


@app.errorhandler(Exception)
def internal_error(error):
    return jsonify({"error": str(error)}), 500


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
    return jsonify({"success": True})


# Static File Hosting Hack
# See https://github.com/tiangolo/uwsgi-nginx-flask-docker/blob/master/deprecated-single-page-apps-in-same-container.md
@app.route("/")
def main():
    index_path = os.path.join(app.static_folder, "index.html")
    return send_file(index_path)


# Everything not declared before (not a Flask route / API endpoint)...
@app.route("/<path:path>")
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, "index.html")
        return send_file(index_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

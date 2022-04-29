import io
import os

import requests as requests
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from plexwrapper import PlexWrapper

app = Flask(__name__)
CORS(app)


@app.errorhandler(Exception)
def internal_error(error):
    return jsonify({"error": str(error)}), 500


@app.route("/server/info")
def get_server_info():
    info = PlexWrapper().get_server_info()
    return jsonify(info)


@app.route("/server/proxy")
def get_server_proxy():
    # Proxy a request to the server - useful when the user
    # is viewing the cleanarr dash over HTTPS to avoid the browser
    # blocking untrusted server certs
    url = request.args.get('url')
    r = requests.get(url)
    return send_file(io.BytesIO(r.content), mimetype='image/jpeg')


@app.route("/content/dupes")
def get_dupes():
    dupes = PlexWrapper().get_dupe_content()
    return jsonify(dupes)


@app.route("/content/samples")
def get_samples():
    samples = PlexWrapper().get_content_sample_files()
    return jsonify(samples)


@app.route("/server/deleted-sizes")
def get_deleted_sizes():
    sizes = PlexWrapper().get_deleted_sizes()
    return jsonify(sizes)


@app.route("/delete/media", methods=["POST"])
def delete_media():
    content = request.get_json()
    library_name = content["library_name"]
    content_key = content["content_key"]
    media_id = content["media_id"]

    PlexWrapper().delete_media(library_name, content_key, media_id)

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

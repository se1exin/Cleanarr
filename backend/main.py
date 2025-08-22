import io
import os
import urllib

import requests as requests
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from database import Database
from logger import get_logger
from plexwrapper import PlexWrapper

app = Flask(__name__, static_folder='static/static')
CORS(app)

logger = get_logger(__name__)


@app.errorhandler(Exception)
def internal_error(error):
    logger.error(error)
    return jsonify({"error": str(error)}), 500


@app.route("/server/info")
def get_server_info():
    try:
        info = PlexWrapper().get_server_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting server info: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/server/health")
def get_server_health():
    try:
        # Test Plex connection
        plex = PlexWrapper()
        info = plex.get_server_info()
        return jsonify({
            "status": "healthy",
            "plex_connected": True,
            "plex_name": info.get('name'),
            "libraries": plex.libraries,
            "base_url": plex.baseurl
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "plex_connected": False
        }), 500


@app.route("/server/proxy")
def get_server_proxy():
    # Proxy a request to the server - useful when the user
    # is viewing the cleanarr dash over HTTPS to avoid the browser
    # blocking untrusted server certs
    url = request.args.get('url')
    r = requests.get(url)
    return send_file(io.BytesIO(r.content), mimetype='image/jpeg')

@app.route("/server/thumbnail")
def get_server_thumbnail():
    # Proxy a request to the server - useful when the user
    # is viewing the cleanarr dash over HTTPS to avoid the browser
    # blocking untrusted server certs
    content_key = urllib.parse.unquote(request.args.get('content_key'))
    url = PlexWrapper().get_thumbnail_url(content_key)
    r = requests.get(url)
    return send_file(io.BytesIO(r.content), mimetype='image/jpeg')

@app.route("/content/dupes")
def get_dupes():
    logger.info("GET /content/dupes called - fetching all duplicates")
    
    try:
        logger.info("Creating PlexWrapper instance...")
        plex_wrapper = PlexWrapper()
        logger.info("PlexWrapper created successfully")
        
        logger.info("Calling get_dupe_content() to fetch all duplicates...")
        dupes = plex_wrapper.get_dupe_content()
        logger.info(f"get_dupe_content returned {len(dupes) if dupes else 0} total results")
        
        if dupes:
            logger.info(f"First few results: {dupes[:2] if len(dupes) > 2 else dupes}")
        else:
            logger.info("No duplicate content found")
            
        return jsonify({"data": dupes})
    except Exception as e:
        logger.error(f"Error in get_dupes: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return jsonify({"error": str(e)}), 500


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
    try:
        content = request.get_json()
        if not content:
            return jsonify({"error": "No JSON data provided"}), 400
            
        library_name = content.get("library_name")
        content_key = content.get("content_key")
        media_id = content.get("media_id")
        
        # Validate required fields
        if not all([library_name, content_key, media_id]):
            return jsonify({"error": "Missing required fields: library_name, content_key, or media_id"}), 400
        
        logger.info(f"Delete request for library: {library_name}, content: {content_key}, media: {media_id}")
        
        # Perform the delete operation
        result = PlexWrapper().delete_media(library_name, content_key, media_id)
        
        if result:
            logger.info(f"Successfully deleted media {media_id}")
            return jsonify({"success": True, "message": f"Media {media_id} deleted successfully"})
        else:
            logger.error(f"Delete operation failed for media {media_id}")
            return jsonify({"error": "Delete operation failed"}), 500
            
    except Exception as e:
        logger.error(f"Error in delete_media endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/content/ignore", methods=["POST"])
def add_ignored_item():
    content = request.get_json()
    content_key = content["content_key"]

    db = Database()
    db.add_ignored_item(content_key)

    return jsonify({"success": True})


@app.route("/content/unignore", methods=["POST"])
def remove_ignored_item():
    content = request.get_json()
    content_key = content["content_key"]

    db = Database()
    db.remove_ignored_item(content_key)

    return jsonify({"success": True})


# Static File Hosting Hack
# See https://github.com/tiangolo/uwsgi-nginx-flask-docker/blob/master/deprecated-single-page-apps-in-same-container.md
@app.route("/")
def main():
    index_path = os.path.join("static", "index.html")
    return send_file(index_path)


# Everything not declared before (not a Flask route / API endpoint)...
@app.route("/<path:path>")
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join("static", path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join("static", "index.html")
        return send_file(index_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", "80"))

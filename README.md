# Plex Library Cleaner

A simple UI to help find and delete duplicate and sample files from your Plex server.

>Note: At this time only Plex Movie Libraries are supported.

## Run with Docker

This project is available as a docker container on [Docker Hub](https://hub.docker.com/r/selexin/plex-library-cleaner).

### Docker Parameters

You will need to set the correct parameters for your setup:

| Parameter | Function |
| :----: | --- |
| `-e PLEX_BASE_URL="http://plex_ip_address:32400` | (required) Plex Server Address (e.g. http://192.169.1.100:32400) |
| `-e PLEX_TOKEN="somerandomstring"` | (optional) A valid Plex token for your Plex Server ([How to find your Plex Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)) |
| `-p 5000:80` | (required) Expose the UI via the selected port (in this case `5000`). Change `5000` to the port of your choosing, but don't change the number `80`. |


```
docker run \
	-e PLEX_BASE_URL="http://192.169.1.100:32400" \
	-e PLEX_TOKEN="somerandomstring" \
	-p 5000:80 \
	selexin/plex-library-cleaner:latest
```

You can then access the UI in your browser at [http://localhost:5000/](http://localhost:5000/).

## Screenshots

![Demo of deleting duplicate movies](screenshots/demo.gif)


## Credits
Thanks to the following projects:
- [pkkid/python-plexapi](https://github.com/pkkid/python-plexapi)
- [tiangolo/uwsgi-nginx-flask-docker](https://github.com/tiangolo/uwsgi-nginx-flask-docker)

## License
MIT - see [LICENSE.md](https://github.com/se1exin/Plex-Library-Cleaner/blob/master/LICENSE.md)
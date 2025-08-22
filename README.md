# Cleanarr

A simple UI to help find and delete duplicate and sample files from your Plex server.

> Note: At this time only Plex Content Libraries (TV/Movies) are supported.

## Recent Fixes (v1.1.1)

This version includes critical fixes for the delete functionality that was causing 500s and 502s:

### Backend Fixes

- **Fixed Delete Operation**: Resolved race conditions and database conflicts during media deletion
- **Improved Error Handling**: Better error handling and logging throughout the application
- **Database Thread Safety**: Added proper locking to prevent concurrent access issues
- **Updated Dependencies**: All Python packages updated to latest stable versions

### Frontend Fixes

- **Better Error Handling**: Improved API error handling and user feedback
- **Updated Dependencies**: All Node.js packages updated to latest stable versions
- **Enhanced UI**: Better error display and operation status feedback

### Infrastructure Improvements

- **Modern Docker Setup**: Updated to use Python 3.11 and Node.js 18
- **Nginx + uWSGI**: Replaced old uwsgi-nginx-flask with modern nginx + uWSGI setup
- **Health Checks**: Added health check endpoints for better monitoring

## Plex Setup

You need to check `Settings | Library | Allow media deletion` within your plex server's settings

You will need a Plex Token: [How to find your Plex Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)

## Run with Docker

This project is available as a docker container on [Docker Hub](https://hub.docker.com/r/selexin/cleanarr).

### Docker Parameters

You will need to set the correct parameters for your setup:

| Parameter                                | Function                                                                                                                                                                                                                                            |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-v /some/path/on/your/computer:/config` | (**required**) Volume mount for config directory                                                                                                                                                                                                    |
| `-e PLEX_BASE_URL="plex_address"`        | (**required**) Plex Server Address (e.g. http://192.169.1.100:32400)                                                                                                                                                                                |
| `-e PLEX_TOKEN="somerandomstring"`       | (**required**) A valid Plex token for your Plex Server ([How to find your Plex Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/))                                                                    |
| `-e LIBRARY_NAMES="Movies"`              | (**optional**) Name(s) of your Plex Libraries to search. Separate multiple library names with ";" character. E.g. `"Movies 1;Movies 2"`. Default value is **"Movies"**                                                                              |
| `-e BYPASS_SSL_VERIFY=1`                 | (**optional**) Disable SSL certificate verification. Use this if your Plex Server has "Secure Connections: Required" and you are having issues connecting to it. (Thanks [@booksarestillbetter - #2](https://github.com/se1exin/cleanarr/issues/2)) |
| `-p 5000:80`                             | (**required**) Expose the UI via the selected port (in this case `5000`). Change `5000` to the port of your choosing, but don't change the number `80`.                                                                                             |
| `-e PAGE_SIZE=50`                        | (**optional**) To avoid plex timeouts, results are loaded in pages (or chunks). If you recieve Plex Timeout errors, try setting this parameter to a lower value.                                                                                    |
| `-e DEBUG=0`                             | (**optional**) To enable debug logging set `DEBUG` to `1`                                                                                                                                                                                           |
| `-e PLEX_TIMEOUT=7200`                   | (**optional**) modify the timeout for wrapper (Error : Failed to load content!)                                                                                                                                                                     |

#### Example running directly with docker (with make)

##### build

```shell
make build # this will create an .env file if it doesn't already exist
# edit .env file
```

##### run

```shell
# set CONFIG_MOUNT to a location on your machine where you wish to store the state from Cleanarr
CONFIG_MOUNT=/tmp/config make run
```

#### Example running directly with docker (manually)

```shell
# you can build and run manually
docker build -t=selexin/cleanarr:latest .
docker run \
	-e PLEX_BASE_URL="http://192.169.1.100:32400" \
	-e PLEX_TOKEN="somerandomstring" \
	-e LIBRARY_NAMES="Movies" \
	-p 5000:80 \
  -v /some/path/on/your/computer:/config \
	selexin/cleanarr:latest

```

#### Example using Docker Compose

(Thanks @JesseWebDotCom - #8)

Note that environment variables should **not** be quoted when using docker-compose.yml format

```
version: '3'

services:

  cleanarr:
    image: selexin/cleanarr:latest
    container_name: cleanarr
    hostname: cleanarr
    ports:
      - "5000:80"
    environment:
      - BYPASS_SSL_VERIFY=1
      - PLEX_TOKEN=somerandomstring
      - PLEX_BASE_URL=http://192.169.1.100:32400
      - LIBRARY_NAMES=Adult Movies;Kid Videos
    volumes:
      - /some/path/on/your/computer:/config
    restart: unless-stopped
```

You can then access the UI in your browser at [http://localhost:5000/](http://localhost:5000/).

## Building from Source

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
npm run build
```

### Docker Build

```bash
docker build -t cleanarr:latest .
```

## Troubleshooting

### Delete Operations Failing

If you're still experiencing issues with delete operations:

1. **Check Logs**: Enable debug logging by setting `DEBUG=1`
2. **Verify Permissions**: Ensure Plex has permission to delete files
3. **Check Disk Space**: Ensure there's sufficient disk space for database operations
4. **Database Issues**: If database corruption is suspected, delete the `db.json` file and restart

### Performance Issues

- Reduce `PAGE_SIZE` if experiencing timeouts
- Increase `PLEX_TIMEOUT` for large libraries
- Monitor memory usage during bulk operations

## Credits

Thanks to the following projects:

- [pkkid/python-plexapi](https://github.com/pkkid/python-plexapi)
- [tiangolo/uwsgi-nginx-flask-docker](https://github.com/tiangolo/uwsgi-nginx-flask-docker)

## License

MIT - see [LICENSE.md](https://github.com/se1exin/cleanarr/blob/master/LICENSE.md)

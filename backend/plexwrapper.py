import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from plexapi.media import Media, MediaPart, MediaPartStream
from plexapi.server import PlexServer
from plexapi.video import Movie, Video, Episode

from database import Database
from logger import get_logger

logger = get_logger(__name__)

class PlexWrapper(object):
    def __init__(self):
        self.baseurl = os.environ.get("PLEX_BASE_URL")
        token = os.environ.get("PLEX_TOKEN")
        self.page_size = int(os.environ.get("PAGE_SIZE", 50))
        verify_ssl = os.environ.get("BYPASS_SSL_VERIFY", "0") != "1"
        self.libraries = [
            x.strip()
            for x in os.environ.get("LIBRARY_NAMES", "Movies").split(";")
            if x.strip() != ""
        ]
        timeout = int(os.environ.get("PLEX_TIMEOUT",60*60)) # added line
        
        logger.debug("PlexWrapper Init")
        logger.debug("PLEX_BASE_URL %s", self.baseurl)
        logger.debug("LIBRARY_NAMES %s", self.libraries)

        session = requests.Session()
        session.verify = verify_ssl
        logger.debug("Connecting to Plex...")
        self.plex = PlexServer(self.baseurl, token, session=session, timeout=timeout)
        logger.debug("Connected to Plex!")

        logger.debug("Initializing DB...")
        self.db = Database()
        logger.debug("Initialized DB!")


    def _get_sections(self):
        return [self.plex.library.section(title=library) for library in self.libraries]

    def get_deleted_sizes(self):
        sizes = {}
        for library_name in self.libraries:
            sizes[library_name] = self.db.get_deleted_size(library_name)
        return sizes

    def get_server_info(self):
        return {
            'name': self.plex.friendlyName,
            'url': self.baseurl + '/web/index.html'
        }

    def get_dupe_content(self, page=1):
        logger.debug("START")
        dupes = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for section in self._get_sections():
                logger.debug("SECTION: %s", section.title)
                if section.type == "movie":
                    logger.debug("Section type is MOVIE")
                    # Recursively search movies
                    offset = (page - 1) * self.page_size
                    limit = offset + self.page_size
                    logger.debug("Get results from offset %s to limit %s", offset, limit)
                    results = section.search(duplicate=True, libtype='movie', container_start=offset, limit=limit)
                    for movie in results:
                        if len(movie.media) > 1:
                            future = executor.submit(self.movie_to_dict, movie, section.title)
                            futures.append(future)
                elif section.type == "show":
                    logger.debug("Section type is SHOW")
                    # Recursively search TV
                    offset = (page - 1) * self.page_size
                    limit = offset + self.page_size
                    logger.debug("Get results from offset %s to limit %s", offset, limit)
                    results = section.search(duplicate=True, libtype='episode', container_start=offset, limit=limit)
                    for episode in results:
                        if len(episode.media) > 1:
                            future = executor.submit(self.episode_to_dict, episode, section.title)
                            futures.append(future)

            for future in as_completed(futures):
                dupes.append(future.result())

        return dupes

    def get_content_sample_files(self):
        content = []

        for section in self._get_sections():
            for mediaContent in section.all():
                samples = []
                if mediaContent.TYPE != 'movie' or mediaContent.TYPE != 'episode':
                    continue
                for media in mediaContent.media:
                    if media.duration is None or media.duration < (5 * 60 * 1000):
                        samples.append(self.media_to_dict(media))
                if len(samples) > 0:
                    _media = dict()
                    if mediaContent.TYPE == 'movie':
                        _media = self.movie_to_dict(mediaContent, section.title)
                    elif mediaContent.TYPE == 'episode':
                        _media = self.episode_to_dict(mediaContent, section.title)
                    _media["media"] = samples
                    content.append(_media)
        return content

    def get_content(self, media_id):
        return self.plex.fetchItem(media_id)

    def delete_media(self, library_name, content_key, media_id):
        content = self.get_content(content_key)
        deleted_size = self.db.get_deleted_size(library_name)

        for media in content.media:
            if media.id == media_id:
                for part in media.parts:
                    deleted_size += part.size
                media.delete()

        self.db.set_deleted_size(library_name, deleted_size)

    def video_to_dict(self, video: Video) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Video
        ignored = self.db.get_ignored_item(video.key)
        results = {
            "ignored": ignored is not None,
        }
        attributes_to_fetch = {
            "addedAt": lambda: str(video.addedAt),
            "key": lambda: video.key,
            "lastViewedAt": lambda: str(video.lastViewedAt),
            "librarySectionID": lambda: video.librarySectionID,
            "summary": lambda: video.summary,
            "thumbUrl": lambda: video.thumbUrl,
            "title": lambda: video.title,
            "titleSort": lambda: video.titleSort,
            "type": lambda: video.type,
            "updatedAt": lambda: str(video.updatedAt),
            "viewCount": lambda: str(video.viewCount),
            "url": lambda: self.baseurl + '/web/index.html#!/server/' + self.plex.machineIdentifier + '/details?key=' + urllib.parse.quote_plus(video.key)
        }
        with ThreadPoolExecutor(max_workers=len(attributes_to_fetch)) as executor:
            future_to_attr = {executor.submit(self.fetch_attribute, func): attr for attr, func in attributes_to_fetch.items()}
            for future in as_completed(future_to_attr):
                attr = future_to_attr[future]
                results[attr] = future.result()
        return results


    @staticmethod
    def fetch_attribute(func, *args, **kwargs):
        try:
            return func()
        except Exception as e:
            logger.error(f"Error fetching attribute: {e}")

    def movie_to_dict(self, movie: Movie, library: str) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie
        attributes_to_fetch = {
            "duration": lambda: movie.duration,
            "guid": lambda: movie.guid,
            "originalTitle": lambda: movie.originalTitle,
            "originallyAvailableAt": lambda: str(movie.originallyAvailableAt),
            "rating": lambda: movie.rating,
            "ratingImage": lambda: movie.ratingImage,
            "studio": lambda: movie.studio,
            "tagline": lambda: movie.tagline,
            "userRating": lambda: movie.userRating,
            "year": lambda: movie.year,
            "media": lambda: [self.media_to_dict(media) for media in movie.media],
        }
        results = {
            **self.video_to_dict(movie),
            "contentType": 'movie',
            "library": library,
        }
        with ThreadPoolExecutor(max_workers=len(attributes_to_fetch)) as executor:
            future_to_attr = {executor.submit(self.fetch_attribute, func): attr for attr, func in attributes_to_fetch.items()}
            for future in as_completed(future_to_attr):
                attr = future_to_attr[future]
                results[attr] = future.result()

        return results

    def episode_to_dict(self, episode: Episode, library: str) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie
        results = {
            **self.video_to_dict(episode),
            "contentType": 'episode',
            "library": library,
        }
        attributes_to_fetch = {
            "duration": lambda: episode.duration,
            "guid": lambda: episode.guid,
            "originalTitle": lambda: episode.title,
            "originallyAvailableAt": lambda: str(episode.originallyAvailableAt),
            "rating": lambda: episode.rating,
            "year": lambda: episode.year,
            "seasonNumber": lambda: episode.seasonNumber,
            "seasonEpisode": lambda: episode.seasonEpisode,
            "seriesTitle": lambda: episode.grandparentTitle,
            "media": lambda: [self.media_to_dict(media) for media in episode.media],
        }
        with ThreadPoolExecutor(max_workers=len(attributes_to_fetch)) as executor:
            future_to_attr = {executor.submit(self.fetch_attribute, func): attr for attr, func in attributes_to_fetch.items()}
            for future in as_completed(future_to_attr):
                attr = future_to_attr[future]
                results[attr] = future.result()

        return results

    def get_thumbnail_url(self, content_key):
        item = self.get_content(content_key)
        if item is not None:
            return item.thumbUrl
        else:
            return "";

    @classmethod
    def media_to_dict(cls, media: Media) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.Media
        return {
            "id": media.id,
            # 'initpath': media.initpath,
            # 'video': media.video,
            "aspectRatio": media.aspectRatio,
            "audioChannels": media.audioChannels,
            "audioCodec": media.audioCodec,
            "bitrate": media.bitrate,
            "container": media.container,
            "duration": media.duration,
            "width": media.width,
            "height": media.height,
            "has64bitOffsets": media.has64bitOffsets,
            "optimizedForStreaming": media.optimizedForStreaming,
            "target": media.target,
            "title": media.title,
            "videoCodec": media.videoCodec,
            "videoFrameRate": media.videoFrameRate,
            "videoResolution": media.videoResolution,
            "videoProfile": media.videoProfile,
            "parts": [cls.media_part_to_dict(media_part) for media_part in media.parts],
        }

    @classmethod
    def media_part_to_dict(cls, media_part: MediaPart) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.MediaPart
        return {
            "id": media_part.id,
            # 'media_id': media_part.media.id,
            # 'initpath': media_part.initpath,
            "container": media_part.container,
            "duration": media_part.duration,
            "file": media_part.file,
            "indexes": media_part.indexes,
            "key": media_part.key,
            "size": media_part.size,
            "exists": media_part.exists,
            "accessible": media_part.accessible,
            "streams": [
                cls.media_part_stream_to_dict(media_part_stream)
                for media_part_stream in media_part.videoStreams()
            ],
        }

    @classmethod
    def media_part_stream_to_dict(cls, media_part_stream: MediaPartStream) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.MediaPartStream
        return {
            "id": media_part_stream.id,
            # 'media_id': media_part.media.id,
            # 'initpath': media_part.initpath,
            "codec": media_part_stream.codec,
            "codecID": media_part_stream.codecID,
            "language": media_part_stream.language,
            "languageCode": media_part_stream.languageCode,
            "selected": media_part_stream.selected,
            "type": media_part_stream.type,
        }

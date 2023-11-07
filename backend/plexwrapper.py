import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from plexapi.media import Media, MediaPart, MediaPartStream
from plexapi.server import PlexServer
from plexapi.video import Movie, Video, Episode

from utils import trace_time
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

        self.traces = {}

    @trace_time
    def _get_sections(self):
        return [self.plex.library.section(title=library) for library in self.libraries]

    @trace_time
    def get_deleted_sizes(self):
        sizes = {}
        for library_name in self.libraries:
            sizes[library_name] = self.db.get_deleted_size(library_name)
        return sizes

    @trace_time
    def get_server_info(self):
        return {
            'name': self.plex.friendlyName,
            'url': self.baseurl + '/web/index.html'
        }

    @trace_time
    def get_dupe_content(self, page=1):
        logger.debug("START")
        dupes = []
        with ThreadPoolExecutor() as executor:
            futures = []
            logger.debug(f"GET DUPES FOR: {[(x.title, x.type) for x in self._get_sections()]}")
            for section in self._get_sections():
                future = executor.submit(self.get_dupe_content_for_section, page, section)
                futures.append(future)

            for future in as_completed(futures):
                results = future.result()
                if results:
                    dupes = dupes + results

        return dupes

    @trace_time
    def get_dupe_content_for_section(self, page, section):
        if section.type not in ("movie", "show"):
            return {}
        dupes = []
        duplicate=True
        # undocumented environment variable purely for development purposes.
        # instead of looking for duplicates, this will look for non-duplicates
        # which can be useful when wanting to test the UI against a larger dataset
        if os.getenv("CHAOS_NOT_DUPLICATE", "0") == "1":
            duplicate=False
        to_dict_func = self.movie_to_dict
        if section.type == "episode":
            to_dict_func = self.episode_to_dict
        with ThreadPoolExecutor() as executor:
            futures = []
            logger.debug("SECTION: %s/%s", section.title, section.type)
            offset = (page - 1) * self.page_size
            limit = offset + self.page_size
            logger.debug(
                "Get results for %s/%s from offset %s to limit %s",
                section.title,
                section.type,
                offset,
                limit,
            )
            libtype = section.type
            if libtype == "show":
                libtype = "episode"
            results = section.search(duplicate=duplicate, libtype=libtype, container_start=offset, limit=limit)
            for item in results:
                if not duplicate or len(item.media) > 1:
                    future = executor.submit(to_dict_func, item, section.title)
                    futures.append(future)

            for future in as_completed(futures):
                dupes.append(future.result())

        return dupes

    # TODO: refactor and multithread
    @trace_time
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

    @trace_time
    def get_content(self, media_id):
        return self.plex.fetchItem(media_id)

    @trace_time
    def delete_media(self, library_name, content_key, media_id):
        content = self.get_content(content_key)
        deleted_size = self.db.get_deleted_size(library_name)

        for media in content.media:
            if media.id == media_id:
                for part in media.parts:
                    deleted_size += part.size
                media.delete()

        self.db.set_deleted_size(library_name, deleted_size)

    @trace_time
    def video_to_dict(self, video: Video) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Video
        ignored = self.db.get_ignored_item(video.key)
        results = {
            "ignored": ignored is not None,
        }
        attributes_to_fetch = {
            # "addedAt": lambda: str(video.addedAt),
            "key": lambda: video.key,
            # "lastViewedAt": lambda: str(video.lastViewedAt),
            "librarySectionID": lambda: video.librarySectionID,
            # "summary": lambda: video.summary,
            "thumbUrl": lambda: video.thumbUrl,
            "title": lambda: video.title,
            # "titleSort": lambda: video.titleSort,
            "type": lambda: video.type,
            # "updatedAt": lambda: str(video.updatedAt),
            # "viewCount": lambda: str(video.viewCount),
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

    @trace_time
    def movie_to_dict(self, movie: Movie, library: str) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie
        attributes_to_fetch = {
            "duration": lambda: movie.duration,
            "guid": lambda: movie.guid,
            "originalTitle": lambda: movie.title,
            # "originalTitle": lambda: movie.originalTitle,
            # "originallyAvailableAt": lambda: str(movie.originallyAvailableAt),
            # "rating": lambda: movie.rating,
            # "ratingImage": lambda: movie.ratingImage,
            # "studio": lambda: movie.studio,
            # "tagline": lambda: movie.tagline,
            # "userRating": lambda: movie.userRating,
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

    @trace_time
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
            # "originallyAvailableAt": lambda: str(episode.originallyAvailableAt),
            # "rating": lambda: episode.rating,
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

    @trace_time
    def get_thumbnail_url(self, content_key):
        item = self.get_content(content_key)
        if item is not None:
            return item.thumbUrl
        else:
            return ""

    @classmethod
    @trace_time
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
    @trace_time
    def media_part_to_dict(cls, media_part: MediaPart) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.MediaPart
        results = {}
        attributes_to_fetch = {
            "id": lambda: media_part.id,
            "container": lambda: media_part.container,
            "duration": lambda: media_part.duration,
            "file": lambda: media_part.file,
            "indexes": lambda: media_part.indexes,
            "key": lambda: media_part.key,
            "size": lambda: media_part.size,
            "exists": lambda: media_part.exists,
            "accessible": lambda: media_part.accessible,
            "streams": lambda: [
                cls.media_part_stream_to_dict(media_part_stream)
                for media_part_stream in media_part.videoStreams()
            ],
        }
        with ThreadPoolExecutor(max_workers=len(attributes_to_fetch)) as executor:
            future_to_attr = {executor.submit(cls.fetch_attribute, func): attr for attr, func in attributes_to_fetch.items()}
            for future in as_completed(future_to_attr):
                attr = future_to_attr[future]
                results[attr] = future.result()
        return results

    @classmethod
    @trace_time
    def media_part_stream_to_dict(cls, media_part_stream: MediaPartStream) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.MediaPartStream
        results = {}
        attributes_to_fetch = {
            "id": lambda: media_part_stream.id,
            "codec": lambda: media_part_stream.codec,
            "codecID": lambda: media_part_stream.codecID,
            "language": lambda: media_part_stream.language,
            "languageCode": lambda: media_part_stream.languageCode,
            "selected": lambda: media_part_stream.selected,
            "type": lambda: media_part_stream.type,
        }
        with ThreadPoolExecutor(max_workers=len(attributes_to_fetch)) as executor:
            future_to_attr = {executor.submit(cls.fetch_attribute, func): attr for attr, func in attributes_to_fetch.items()}
            for future in as_completed(future_to_attr):
                attr = future_to_attr[future]
                results[attr] = future.result()
        return results

import os
import urllib.parse
from urllib3 import PoolManager
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from plexapi.media import Media, MediaPart, MediaPartStream
from plexapi.server import PlexServer
from plexapi.video import Movie, Video, Episode

from utils import trace_time
from database import Database
from logger import get_logger

logger = get_logger(__name__)

class HostNameIgnoringAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=..., **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       assert_hostname=False)

class PlexWrapper(object):
    def __init__(self):
        self.baseurl = os.environ.get("PLEX_BASE_URL")
        token = os.environ.get("PLEX_TOKEN")
        self.page_size = int(os.environ.get("PAGE_SIZE", 50))
        self.libraries = [
            x.strip()
            for x in os.environ.get("LIBRARY_NAMES", "Movies").split(";")
            if x.strip() != ""
        ]
        timeout = int(os.environ.get("PLEX_TIMEOUT",60*60))
        
        logger.info("PlexWrapper Init")
        logger.info("PLEX_BASE_URL %s", self.baseurl)
        logger.info("LIBRARY_NAMES %s", self.libraries)

        session = requests.Session()
        if os.environ.get("BYPASS_SSL_VERIFY", "0") == "1":
            session.verify = False
            # Suppress SSL warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.info("SSL verification disabled")
        
        logger.debug("Connecting to Plex...")
        logger.info("Using session with verify=%s", session.verify)
        logger.info("Session headers: %s", dict(session.headers))
        
        try:
            # Try connecting with explicit parameters
            logger.info("Attempting PlexServer connection with baseurl=%s, token=%s, timeout=%s", 
                        self.baseurl, token[:10] + "..." if token else "None", timeout)
            
            self.plex = PlexServer(self.baseurl, token, session=session, timeout=timeout)
            logger.debug("Connected to Plex!")
            logger.debug("Plex server name: %s", self.plex.friendlyName)
            
        except Exception as e:
            logger.error("Failed to connect to Plex: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.error("Exception args: %s", e.args)
            raise

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
    def get_dupe_content(self, page=None):
        logger.info("=== START get_dupe_content ===")
        if page is None:
            logger.info("No page specified - fetching all duplicates")
        else:
            logger.info(f"Page requested: {page} (ignored - fetching all)")
        
        dupes = []
        with ThreadPoolExecutor() as executor:
            futures = []
            
            # Get sections first
            logger.info("Getting library sections...")
            sections = self._get_sections()
            logger.info(f"Found {len(sections)} sections: {[(x.title, x.type) for x in sections]}")
            
            for section in sections:
                logger.info(f"Submitting section '{section.title}' ({section.type}) for processing...")
                future = executor.submit(self.get_dupe_content_for_section, None, section)
                futures.append(future)

            logger.info(f"Waiting for {len(futures)} section processing tasks to complete...")
            for future in as_completed(futures):
                try:
                    results = future.result()
                    logger.info(f"Section processing completed, got {len(results) if results else 0} results")
                    if results:
                        dupes = dupes + results
                        logger.info(f"Total dupes so far: {len(dupes)}")
                except Exception as e:
                    logger.error(f"Error processing section: {str(e)}")

        logger.info(f"=== END get_dupe_content, returning {len(dupes)} total results ===")
        return dupes

    @trace_time
    def get_dupe_content_for_section(self, page, section):
        logger.info(f"=== Processing section: {section.title} ({section.type}) ===")
        
        if section.type not in ("movie", "show"):
            logger.info(f"Skipping section {section.title} - type {section.type} not supported")
            return {}
            
        dupes = []
        duplicate=True
        # undocumented environment variable purely for development purposes.
        # instead of looking for duplicates, this will look for non-duplicates
        # which can be useful when wanting to test the UI against a larger dataset
        if os.getenv("CHAOS_NOT_DUPLICATE", "0") == "1":
            duplicate=False
            logger.info("CHAOS_NOT_DUPLICATE=1, looking for NON-duplicates")
        else:
            logger.info("Looking for duplicates")
            
        to_dict_func = self.movie_to_dict
        if section.type == "episode":
            to_dict_func = self.episode_to_dict
            logger.info("Using episode_to_dict function")
        else:
            logger.info("Using movie_to_dict function")
            
        with ThreadPoolExecutor() as executor:
            futures = []
            logger.info(f"Processing section: {section.title}/{section.type}")
            
            if page is None:
                # No pagination - get all results
                logger.info(f"Getting all results for {section.title}/{section.type} (no pagination)")
                libtype = section.type
                if libtype == "show":
                    libtype = "episode"
                    logger.info(f"Show section detected, using libtype='episode' for search")
                    
                logger.info(f"Searching for all content with duplicate={duplicate}, libtype={libtype}")
                results = section.search(duplicate=duplicate, libtype=libtype)
                logger.info(f"Search returned {len(results)} items")
            else:
                # Pagination logic (kept for backward compatibility)
                offset = (page - 1) * self.page_size
                limit = offset + self.page_size
                logger.info(
                    "Get results for %s/%s from offset %s to limit %s (page_size=%s)",
                    section.title,
                    section.type,
                    offset,
                    limit,
                    self.page_size
                )
                libtype = section.type
                if libtype == "show":
                    libtype = "episode"
                    logger.info(f"Show section detected, using libtype='episode' for search")
                    
                logger.info(f"Searching for content with duplicate={duplicate}, libtype={libtype}, offset={offset}, limit={limit}")
                results = section.search(duplicate=duplicate, libtype=libtype, container_start=offset, limit=limit)
                logger.info(f"Search returned {len(results)} items")
            
            for i, item in enumerate(results):
                logger.info(f"Item {i+1}: {item.title} (type: {item.TYPE}) - Media count: {len(item.media)}")
                if not duplicate or len(item.media) > 1:
                    logger.info(f"Processing item '{item.title}' - qualifies as duplicate")
                    future = executor.submit(to_dict_func, item, section.title)
                    futures.append(future)
                else:
                    logger.info(f"Skipping item '{item.title}' - doesn't qualify as duplicate (media count: {len(item.media)})")

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
        try:
            logger.debug(f"Starting delete operation for media_id: {media_id}, content_key: {content_key}")
            
            # Get the content item first
            content = self.get_content(content_key)
            if not content:
                logger.error(f"Content not found for key: {content_key}")
                raise Exception(f"Content not found for key: {content_key}")
            
            # Find the specific media to delete
            target_media = None
            total_size_to_delete = 0
            
            for media in content.media:
                if media.id == media_id:
                    target_media = media
                    # Calculate total size to delete
                    for part in media.parts:
                        if part.exists and part.accessible:
                            total_size_to_delete += part.size
                    break
            
            if not target_media:
                logger.error(f"Media with ID {media_id} not found in content")
                raise Exception(f"Media with ID {media_id} not found")
            
            # Delete the media
            logger.debug(f"Deleting media {media_id} with size {total_size_to_delete} bytes")
            target_media.delete()
            
            # Update the database with the deleted size
            try:
                current_deleted_size = self.db.get_deleted_size(library_name)
                new_total = current_deleted_size + total_size_to_delete
                self.db.set_deleted_size(library_name, new_total)
                logger.debug(f"Updated deleted size for {library_name}: {current_deleted_size} -> {new_total}")
            except Exception as db_error:
                logger.error(f"Failed to update database: {db_error}")
                # Don't fail the delete operation if database update fails
                # The media was already deleted from Plex
            
            logger.info(f"Successfully deleted media {media_id} from {library_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting media {media_id}: {str(e)}")
            # Re-raise the exception to be handled by the caller
            raise

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

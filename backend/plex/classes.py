import os

import requests
from plexapi.media import Media, MediaPart, MediaPartStream
from plexapi.server import PlexServer
from plexapi.video import Movie, Video


class PlexWrapper(object):
    def __init__(self):
        baseurl = os.environ.get("PLEX_BASE_URL")
        token = os.environ.get("PLEX_TOKEN")
        self.maxresults = int(os.environ.get("MAXRESULTS"))
        verify_ssl = os.environ.get("BYPASS_SSL_VERIFY", "0") != "1"
        self.libraries = [
            x.strip() for x
            in os.environ.get("LIBRARY_NAMES", "Movies").split(";")
            if x.strip() != ""
        ]

        session = requests.Session()
        session.verify = verify_ssl
        self.plex = PlexServer(baseurl, token, session=session, timeout=(60 * 60))

    def _get_sections(self):
        return [self.plex.library.section(title=library) for library in self.libraries]

    def get_dupe_movies(self):
        dupes = []
        for section in self._get_sections():
            for movie in section.search(duplicate=True, maxresults=self.maxresults):
                if len(movie.media) > 1:
                    dupes.append(self.movie_to_dict(movie, section.title))
        return dupes

    def get_movie_sample_files(self):
        movies = []

        for section in self._get_sections():
            for movie in section.all():
                samples = []
                for media in movie.media:
                    if media.duration is None or media.duration < (5 * 60 * 1000):
                        samples.append(self.media_to_dict(media))
                if len(samples) > 0:
                    _movie = self.movie_to_dict(movie, section.title)
                    _movie['media'] = samples
                    movies.append(_movie)

        return movies

    def get_movie(self, media_id):
        return self.plex.fetchItem(media_id)

    @classmethod
    def video_to_dict(cls, video: Video) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Video
        return {
            'addedAt': str(video.addedAt),
            'key': video.key,
            'lastViewedAt': str(video.lastViewedAt),
            'librarySectionID': video.librarySectionID,
            'summary': video.summary,
            'thumb': video.thumb,
            'title': video.title,
            'titleSort': video.titleSort,
            'type': video.type,
            'updatedAt': str(video.updatedAt),
            'viewCount': str(video.viewCount),
        }

    @classmethod
    def movie_to_dict(cls, movie: Movie, library: str) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie
        return {
            **cls.video_to_dict(movie),
            'library': library,
            'duration': movie.duration,
            'guid': movie.guid,
            'originalTitle': movie.originalTitle,
            'originallyAvailableAt': str(movie.originallyAvailableAt),
            'rating': movie.rating,
            'ratingImage': movie.ratingImage,
            'studio': movie.studio,
            'tagline': movie.tagline,
            'userRating': movie.userRating,
            'year': movie.year,
            'media': [
                cls.media_to_dict(media)
                for media in movie.media
            ]
        }

    @classmethod
    def media_to_dict(cls, media: Media) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.Media
        return {
            'id': media.id,
            # 'initpath': media.initpath,
            # 'video': media.video,
            'aspectRatio': media.aspectRatio,
            'audioChannels': media.audioChannels,
            'audioCodec': media.audioCodec,
            'bitrate': media.bitrate,
            'container': media.container,
            'duration': media.duration,
            'width': media.width,
            'height': media.height,
            'has64bitOffsets': media.has64bitOffsets,
            'optimizedForStreaming': media.optimizedForStreaming,
            'target': media.target,
            'title': media.title,
            'videoCodec': media.videoCodec,
            'videoFrameRate': media.videoFrameRate,
            'videoResolution': media.videoResolution,
            'videoProfile': media.videoProfile,
            'parts': [
                cls.media_part_to_dict(media_part)
                for media_part in media.parts
            ]
        }

    @classmethod
    def media_part_to_dict(cls, media_part: MediaPart) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.MediaPart
        return {
            'id': media_part.id,
            # 'media_id': media_part.media.id,
            # 'initpath': media_part.initpath,
            'container': media_part.container,
            'duration': media_part.duration,
            'file': media_part.file,
            'indexes': media_part.indexes,
            'key': media_part.key,
            'size': media_part.size,
            'exists': media_part.exists,
            'accessible': media_part.accessible,
            'streams': [
                cls.media_part_stream_to_dict(media_part_stream)
                for media_part_stream in media_part.videoStreams()
            ]
        }

    @classmethod
    def media_part_stream_to_dict(cls, media_part_stream: MediaPartStream) -> dict:
        # https://python-plexapi.readthedocs.io/en/latest/modules/media.html#plexapi.media.MediaPartStream
        return {
            'id': media_part_stream.id,
            # 'media_id': media_part.media.id,
            # 'initpath': media_part.initpath,
            'codec': media_part_stream.codec,
            'codecID': media_part_stream.codecID,
            'language': media_part_stream.language,
            'languageCode': media_part_stream.languageCode,
            'selected': media_part_stream.selected,
            'type': media_part_stream.type
        }

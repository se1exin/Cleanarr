import os
import threading

from tinydb import TinyDB, where
from tinydb.table import Document

from logger import get_logger

DELETED_SIZE_DOC_ID = 1
IGNORED_ITEMS_TABLE = 'ignored'


logger = get_logger(__name__)


class Database(object):
    def __init__(self):
        logger.debug("DB Init")
        config_dir = os.environ.get("CONFIG_DIR", "")  # Will be set by Dockerfile
        self.local = threading.local()
        logger.debug("DB Init Success")

    def get_db(self):
        if not hasattr(self.local, 'db'):
            config_dir = os.environ.get("CONFIG_DIR", "")
            self.local.db = TinyDB(os.path.join(config_dir, 'db.json'))
        return self.local.db

    def set_deleted_size(self, library_name, deleted_size):
        logger.debug("library_name %s, deleted_size %s", library_name, deleted_size)
        self.get_db().upsert(Document({
            library_name: deleted_size
        }, doc_id=DELETED_SIZE_DOC_ID))

    def get_deleted_size(self, library_name):
        logger.debug("library_name %s", library_name)
        data = self.get_db().get(doc_id=DELETED_SIZE_DOC_ID)
        if data is not None:
            if library_name in data:
                return data[library_name]
        return 0

    def get_ignored_item(self, content_key):
        logger.debug("content_key %s", content_key)
        table = self.get_db().table(IGNORED_ITEMS_TABLE)
        data = table.get(where('key') == content_key)
        return data

    def add_ignored_item(self, content_key):
        logger.debug("content_key %s", content_key)
        table = self.get_db().table(IGNORED_ITEMS_TABLE)
        table.insert({
            'key': content_key
        })

    def remove_ignored_item(self, content_key):
        logger.debug("content_key %s", content_key)
        table = self.get_db().table(IGNORED_ITEMS_TABLE)
        table.remove(where('key') == content_key)

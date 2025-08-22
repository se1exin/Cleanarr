import os
import threading
import time
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
        self._lock = threading.RLock()  # Add reentrant lock for thread safety
        logger.debug("DB Init Success")

    def get_db(self):
        if not hasattr(self.local, 'db'):
            config_dir = os.environ.get("CONFIG_DIR", "")
            db_path = os.path.join(config_dir, 'db.json')
            try:
                self.local.db = TinyDB(db_path)
                logger.debug(f"Database initialized at {db_path}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
        return self.local.db

    def set_deleted_size(self, library_name, deleted_size):
        with self._lock:  # Use lock to prevent concurrent writes
            try:
                logger.debug("library_name %s, deleted_size %s", library_name, deleted_size)
                db = self.get_db()
                db.upsert(Document({
                    library_name: deleted_size
                }, doc_id=DELETED_SIZE_DOC_ID))
                logger.debug("Successfully updated deleted size for %s", library_name)
            except Exception as e:
                logger.error(f"Failed to set deleted size: {e}")
                raise

    def get_deleted_size(self, library_name):
        with self._lock:  # Use lock for reads too to ensure consistency
            try:
                logger.debug("library_name %s", library_name)
                db = self.get_db()
                data = db.get(doc_id=DELETED_SIZE_DOC_ID)
                if data is not None:
                    if library_name in data:
                        return data[library_name]
                return 0
            except Exception as e:
                logger.error(f"Failed to get deleted size: {e}")
                return 0  # Return 0 on error instead of crashing

    def get_ignored_item(self, content_key):
        with self._lock:
            try:
                logger.debug("content_key %s", content_key)
                table = self.get_db().table(IGNORED_ITEMS_TABLE)
                data = table.get(where('key') == content_key)
                return data
            except Exception as e:
                logger.error(f"Failed to get ignored item: {e}")
                return None

    def add_ignored_item(self, content_key):
        with self._lock:
            try:
                logger.debug("content_key %s", content_key)
                table = self.get_db().table(IGNORED_ITEMS_TABLE)
                table.insert({
                    'key': content_key
                })
                logger.debug("Successfully added ignored item: %s", content_key)
            except Exception as e:
                logger.error(f"Failed to add ignored item: {e}")
                raise

    def remove_ignored_item(self, content_key):
        with self._lock:
            try:
                logger.debug("content_key %s", content_key)
                table = self.get_db().table(IGNORED_ITEMS_TABLE)
                table.remove(where('key') == content_key)
                logger.debug("Successfully removed ignored item: %s", content_key)
            except Exception as e:
                logger.error(f"Failed to remove ignored item: {e}")
                raise

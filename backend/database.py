import os

from tinydb import TinyDB, where
from tinydb.table import Document

DELETED_SIZE_DOC_ID = 1
IGNORED_ITEMS_TABLE = 'ignored'


class Database(object):
    def __init__(self):
        config_dir = os.environ.get("CONFIG_DIR", "")  # Will be set by Dockerfile
        self.db = TinyDB(os.path.join(config_dir, 'db.json'))

    def set_deleted_size(self, library_name, deleted_size):
        self.db.upsert(Document({
            library_name: deleted_size
        }, doc_id=DELETED_SIZE_DOC_ID))

    def get_deleted_size(self, library_name):
        data = self.db.get(doc_id=DELETED_SIZE_DOC_ID)
        if data is not None:
            if library_name in data:
                return data[library_name]
        return 0

    def get_ignored_item(self, content_key):
        table = self.db.table(IGNORED_ITEMS_TABLE)
        data = table.get(where('key') == content_key)
        return data

    def add_ignored_item(self, content_key):
        table = self.db.table(IGNORED_ITEMS_TABLE)
        table.insert({
            'key': content_key
        })

    def remove_ignored_item(self, content_key):
        table = self.db.table(IGNORED_ITEMS_TABLE)
        table.remove(where('key') == content_key)

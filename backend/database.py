import os

from tinydb import TinyDB
from tinydb.table import Document

DELETED_SIZE_DOC_ID = 1
IGNORED_ITEMS_DOC_ID = 2

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

    def get_ignored_items(self):
        data = self.db.get(doc_id=IGNORED_ITEMS_DOC_ID)
        if data is not None:
            return data.keys()
        return []

    def add_ignored_item(self, content_key):
        self.db.upsert(Document({
            content_key: True
        }, doc_id=IGNORED_ITEMS_DOC_ID))

    def remove_ignored_item(self, content_key):
        items = self.get_ignored_items()
        items.remove(content_key)
        mapped = {key: True for key in items}
        self.db.update(Document(mapped), doc_id=IGNORED_ITEMS_DOC_ID)

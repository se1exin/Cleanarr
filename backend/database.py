import os
import threading

from tinydb import TinyDB, where
from tinydb.table import Document
from sqlalchemy import create_engine, Column, String, Integer, BigInteger
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from logger import get_logger

DELETED_SIZE_DOC_ID = 1
IGNORED_ITEMS_TABLE = 'ignored'
logger = get_logger(__name__)

Base = declarative_base()

class DeletedSize(Base):
    __tablename__ = '_default' # named as such for backwards compatibility
    id = Column(Integer, primary_key=True, default=DELETED_SIZE_DOC_ID)
    library_name = Column(String, unique=True)
    deleted_size = Column(BigInteger)

class IgnoredItem(Base):
    __tablename__ = IGNORED_ITEMS_TABLE
    key = Column(String, primary_key=True)

class DatabaseInterface:
    def set_deleted_size(self, library_name, deleted_size):
        raise NotImplementedError

    def get_deleted_size(self, library_name):
        raise NotImplementedError

    def get_ignored_item(self, content_key):
        raise NotImplementedError

    def add_ignored_item(self, content_key):
        raise NotImplementedError

    def remove_ignored_item(self, content_key):
        raise NotImplementedError

class TinyDBDatabase(DatabaseInterface):
    def __init__(self):
        logger.debug("TinyDB Init")
        config_dir = os.environ.get("CONFIG_DIR", "")
        self.local = threading.local()
        self.config_dir = config_dir
        logger.debug("TinyDB Init Success")

    def get_db(self):
        if not hasattr(self.local, 'db'):
            self.local.db = TinyDB(os.path.join(self.config_dir, 'db.json'))
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

class SQLAlchemyDatabase(DatabaseInterface):
    def __init__(self):
        logger.debug("SQLAlchemy Init")
        config_dir = os.environ.get("CONFIG_DIR", "")
        db_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(config_dir, 'db.sqlite')}")
        self.engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        Base.metadata.create_all(self.engine)
        logger.debug("SQLAlchemy Init Success")

    def set_deleted_size(self, library_name, deleted_size):
        logger.debug("library_name %s, deleted_size %s", library_name, deleted_size)
        session = self.Session()
        obj = session.query(DeletedSize).filter_by(library_name=library_name).first()
        if obj:
            obj.deleted_size = deleted_size
        else:
            obj = DeletedSize(library_name=library_name, deleted_size=deleted_size)
            session.add(obj)
        session.commit()
        session.close()

    def get_deleted_size(self, library_name):
        logger.debug("library_name %s", library_name)
        session = self.Session()
        obj = session.query(DeletedSize).filter_by(library_name=library_name).first()
        session.close()
        return obj.deleted_size if obj else 0

    def get_ignored_item(self, content_key):
        logger.debug("content_key %s", content_key)
        session = self.Session()
        obj = session.query(IgnoredItem).get(content_key)
        session.close()
        return obj

    def add_ignored_item(self, content_key):
        logger.debug("content_key %s", content_key)
        session = self.Session()
        obj = IgnoredItem(key=content_key)
        session.add(obj)
        session.commit()
        session.close()

    def remove_ignored_item(self, content_key):
        logger.debug("content_key %s", content_key)
        session = self.Session()
        session.query(IgnoredItem).filter_by(key=content_key).delete()
        session.commit()
        session.close()

class Database(DatabaseInterface):
    def __init__(self):
        if os.environ.get("DATABASE_URL"):
            self.db = SQLAlchemyDatabase()
        else:
            self.db = TinyDBDatabase()

    def set_deleted_size(self, library_name, deleted_size):
        self.db.set_deleted_size(library_name, deleted_size)

    def get_deleted_size(self, library_name):
        return self.db.get_deleted_size(library_name)

    def get_ignored_item(self, content_key):
        return self.db.get_ignored_item(content_key)

    def add_ignored_item(self, content_key):
        self.db.add_ignored_item(content_key)

    def remove_ignored_item(self, content_key):
        self.db.remove_ignored_item(content_key)

from telethon.sessions import MemorySession
from telethon.crypto import AuthKey
import pymongo

class MongoSession(MemorySession):
    def __init__(self, mongo_uri, session_name):
        super().__init__()
        client = pymongo.MongoClient(mongo_uri)
        db = client.get_default_database()
        self.col = db['sessions']
        self.session_name = session_name
        self._load()

    def _load(self):
        data = self.col.find_one({'_id': self.session_name})
        if data:
            self._dc_id = data.get('dc_id', 0)
            self._server_address = data.get('server_address')
            self._port = data.get('port')
            if data.get('auth_key'):
                self._auth_key = AuthKey(bytes.fromhex(data['auth_key']))

    def set_dc(self, dc_id, server_address, port):
        super().set_dc(dc_id, server_address, port)
        self._save()

    def set_auth_key(self, auth_key):
        self._auth_key = auth_key
        self._save()

    def _save(self):
        self.col.update_one(
            {'_id': self.session_name},
            {'$set': {
                'dc_id': self._dc_id,
                'server_address': self._server_address,
                'port': self._port,
                'auth_key': self._auth_key.key.hex() if self._auth_key else None
            }},
            upsert=True
        )
from telethon.sessions import StringSession
from datetime import datetime
import pymongo

def load_session(mongo_uri, session_name):
    """Busca a string de session salva no MongoDB"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['sessions']
    
    data = col.find_one({'_id': session_name})
    if data and data.get('session_string'):
        print(f"🕒 Último login: {data.get('last_login', 'desconhecido')}")
        return data['session_string']
    return None

def save_session(mongo_uri, session_name, session_string):
    """Salva a string de session no MongoDB"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['sessions']
    
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    col.update_one(
        {'_id': session_name},
        {'$set': {
            'session_string': session_string,
            'last_login': now
        }},
        upsert=True
    )
    print(f"✅ Session salva no MongoDB! [{now}]")

def load_last_message_id(mongo_uri, session_name):
    """Busca o ID da última mensagem clonada"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_state']

    data = col.find_one({'_id': session_name})
    if data:
        return data.get('last_message_id', 0)
    return 0

def save_last_message_id(mongo_uri, session_name, message_id):
    """Salva o ID da última mensagem clonada"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_state']

    col.update_one(
        {'_id': session_name},
        {'$set': {'last_message_id': message_id}},
        upsert=True
    )
    print(f"💾 Último ID salvo: {message_id}")
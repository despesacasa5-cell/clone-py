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

def load_pairs(mongo_uri):
    """Lista todos os pares origem/destino ativos"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_pairs']
    return list(col.find({'active': True}))

def save_pair(mongo_uri, name, origem_id, destino_id, horarios):
    """
    Salva um par origem/destino no MongoDB
    :param name: nome identificador ex: 'par_vendas'
    :param origem_id: ID do grupo origem
    :param destino_id: ID do grupo destino
    :param horarios: lista de horários ex: ['08:00', '12:00', '18:00']
    """
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_pairs']

    col.update_one(
        {'_id': name},
        {'$set': {
            'origem_id': origem_id,
            'destino_id': destino_id,
            'horarios': horarios,
            'active': True,
            'last_message_id': 0
        }},
        upsert=True
    )
    print(f"✅ Par '{name}' salvo!")

def load_last_message_id(mongo_uri, pair_name):
    """Busca o ID da última mensagem clonada de um par"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_pairs']

    data = col.find_one({'_id': pair_name})
    if data:
        return data.get('last_message_id', 0)
    return 0

def save_last_message_id(mongo_uri, pair_name, message_id):
    """Salva o ID da última mensagem clonada de um par"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_pairs']

    col.update_one(
        {'_id': pair_name},
        {'$set': {'last_message_id': message_id}},
        upsert=True
    )
    print(f"💾 [{pair_name}] Último ID salvo: {message_id}")

def save_dialogs(mongo_uri, dialogs):
    """Salva/atualiza a lista de diálogos no MongoDB"""
    client = pymongo.MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['dialogs']

    from datetime import datetime
    updated_at = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    for dialog in dialogs:
        col.update_one(
            {'_id': dialog['id']},
            {'$set': {
                'name': dialog['name'],
                'type': dialog['type'],
                'updated_at': updated_at
            }},
            upsert=True
        )

    print(f"✅ {len(dialogs)} diálogos salvos no MongoDB! [{updated_at}]")
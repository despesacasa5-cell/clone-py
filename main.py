from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from mongo_session import load_session, save_session
from cloner import clonar_grupo
import os

load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
mongo_uri = os.getenv('MONGO_URI')
session_name = 'minha_session'

session_string = load_session(mongo_uri, session_name)

if session_string:
    print("🔄 Carregando session existente do MongoDB...")
    session = StringSession(session_string)
else:
    print("🆕 Primeira execução, criando nova session...")
    session = StringSession()

client = TelegramClient(session, api_id, api_hash)

async def main():
    await client.start()
    save_session(mongo_uri, session_name, client.session.save())

    # IDs dos grupos — pode ser ID numérico ou @username
    ORIGEM  = -1003671128044  # troca pelo ID do grupo origem
    DESTINO = -1003352627576  # troca pelo ID do grupo destino

    await clonar_grupo(
        client=client,
        origem_id=ORIGEM,
        destino_id=DESTINO,
        mongo_uri=mongo_uri,
        session_name=session_name
    )

with client:
    client.loop.run_until_complete(main())
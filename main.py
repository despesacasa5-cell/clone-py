from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from mongo_session import load_session, save_session, save_pair
from scheduler import setup_scheduler
from dialogs import listar_e_salvar_dialogs
from api import app
import uvicorn
import threading
import asyncio
import os

load_dotenv()

api_id       = os.getenv('API_ID')
api_hash     = os.getenv('API_HASH')
mongo_uri    = os.getenv('MONGO_URI')
session_name = 'minha_session'

session_string = load_session(mongo_uri, session_name)
session = StringSession(session_string) if session_string else StringSession()
client = TelegramClient(session, api_id, api_hash)

async def main():
    await client.start()
    save_session(mongo_uri, session_name, client.session.save())
    print("✅ Conectado ao Telegram!\n")

    await listar_e_salvar_dialogs(client, mongo_uri)

    scheduler = setup_scheduler(client, mongo_uri)
    scheduler.start()
    print("🚀 Scheduler rodando!\n")

    # Roda o FastAPI em thread separada
    threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "0.0.0.0", "port": 8000},
        daemon=True
    ).start()
    print("🌐 API rodando na porta 8000!\n")

    await asyncio.Event().wait()

async def run():
    async with client:
        await main()

asyncio.run(run())
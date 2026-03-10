from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from mongo_session import load_session, save_session
from scheduler import setup_scheduler
from dialogs import listar_e_salvar_dialogs
from api import app
from contextlib import asynccontextmanager
import uvicorn
import os

load_dotenv()

api_id       = os.getenv('API_ID')
api_hash     = os.getenv('API_HASH')
mongo_uri    = os.getenv('MONGO_URI')
session_name = 'minha_session'

session_string = load_session(mongo_uri, session_name)
session = StringSession(session_string) if session_string else StringSession()
client = TelegramClient(session, api_id, api_hash)

@asynccontextmanager
async def lifespan(app):
    # Tudo que roda na inicialização
    await client.connect()
    await client.start()
    save_session(mongo_uri, session_name, client.session.save())
    print("✅ Conectado ao Telegram!\n")

    await listar_e_salvar_dialogs(client, mongo_uri)

    scheduler = setup_scheduler(client, mongo_uri)
    scheduler.start()
    print("🚀 Scheduler rodando!\n")

    yield  # app fica rodando aqui

    # Tudo que roda no encerramento
    scheduler.shutdown()
    await client.disconnect()
    print("🔴 Desconectado.")

# Registra o lifespan no FastAPI
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
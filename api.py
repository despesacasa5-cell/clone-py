from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from mongo_session import save_pair, load_pairs, save_session
from dotenv import load_dotenv
import state
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

app = FastAPI(
    title="TG Cloner API",
    description="API para gerenciar clonagem de grupos do Telegram",
    version="1.0.0"
)

# ─── Autenticação ───
def verify_token(x_token: str = Header(..., description="Token de autenticação")):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

# ─── Models ───
class PhoneModel(BaseModel):
    phone: str

    class Config:
        json_schema_extra = {"example": {"phone": "+5521999999999"}}

class CodeModel(BaseModel):
    phone: str
    code: str

    class Config:
        json_schema_extra = {"example": {"phone": "+5521999999999", "code": "12345"}}

class PairModel(BaseModel):
    name: str
    origem_id: int
    destino_id: int
    horarios: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "par_01",
                "origem_id": -1001234567890,
                "destino_id": -1009876543210,
                "horarios": ["08:00", "12:00", "18:00"]
            }
        }

class PairUpdateModel(BaseModel):
    horarios: Optional[List[str]] = None
    active: Optional[bool] = None

# ──────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────

@app.get("/auth/status", tags=["Auth"], dependencies=[Depends(verify_token)])
async def auth_status():
    """Verifica se o Telegram está conectado e autenticado"""
    try:
        if not state.telegram_client:
            return {"status": "client não inicializado"}

        if not state.telegram_client.is_connected():
            return {"status": "desconectado"}

        me = await state.telegram_client.get_me()
        if me:
            return {
                "status": "autenticado",
                "nome": me.first_name,
                "telefone": me.phone
            }
        return {"status": "conectado mas não autenticado"}

    except Exception as e:
        return {"status": "erro", "detail": str(e)}


@app.post("/auth/send-code", tags=["Auth"], dependencies=[Depends(verify_token)])
async def send_code(data: PhoneModel):
    """Envia o código SMS para o telefone informado."""
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    mongo_uri = os.getenv('MONGO_URI')
    api_id    = os.getenv('API_ID')
    api_hash  = os.getenv('API_HASH')

    try:
        # Se o client não existe ou está None, cria um novo
        if not state.telegram_client:
            state.telegram_client = TelegramClient(
                StringSession(), api_id, api_hash
            )

        if not state.telegram_client.is_connected():
            await state.telegram_client.connect()

        result = await state.telegram_client.send_code_request(data.phone)
        state.phone_code_hash = result.phone_code_hash

        return {"message": f"✅ Código enviado para {data.phone}!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/verify", tags=["Auth"], dependencies=[Depends(verify_token)])
async def verify_code(data: CodeModel):
    """Verifica o código recebido por SMS e salva a nova sessão."""
    try:
        if not state.telegram_client or not state.telegram_client.is_connected():
            raise HTTPException(status_code=503, detail="Client não conectado, chame /auth/send-code primeiro")

        await state.telegram_client.sign_in(
            phone=data.phone,
            code=data.code,
            phone_code_hash=state.phone_code_hash
        )

        mongo_uri = os.getenv('MONGO_URI')
        save_session(mongo_uri, 'minha_session', state.telegram_client.session.save())

        return {"message": "✅ Login realizado e sessão salva com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ──────────────────────────────────────────
# DIALOGS
# ──────────────────────────────────────────

@app.get("/dialogs", tags=["Dialogs"], dependencies=[Depends(verify_token)])
def get_dialogs():
    """Lista todos os grupos, canais e conversas salvas no MongoDB"""
    from pymongo import MongoClient
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    dialogs = list(db['dialogs'].find())
    for d in dialogs:
        d['id'] = d.pop('_id')
    return dialogs


# ──────────────────────────────────────────
# PAIRS
# ──────────────────────────────────────────

@app.get("/pairs", tags=["Pairs"], dependencies=[Depends(verify_token)])
def get_pairs():
    """Lista todos os pares de clonagem"""
    mongo_uri = os.getenv('MONGO_URI')
    pairs = load_pairs(mongo_uri)
    for p in pairs:
        p['name'] = p.pop('_id')
    return pairs


@app.post("/pairs", tags=["Pairs"], dependencies=[Depends(verify_token)])
def create_pair(pair: PairModel):
    """Cria um novo par origem/destino"""
    mongo_uri = os.getenv('MONGO_URI')
    save_pair(mongo_uri, pair.name, pair.origem_id, pair.destino_id, pair.horarios)
    return {"message": f"✅ Par '{pair.name}' criado com sucesso!"}


@app.patch("/pairs/{name}", tags=["Pairs"], dependencies=[Depends(verify_token)])
def update_pair(name: str, data: PairUpdateModel):
    """Atualiza horários ou status ativo de um par"""
    from pymongo import MongoClient
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client.get_default_database()

    update = {}
    if data.horarios is not None:
        update['horarios'] = data.horarios
    if data.active is not None:
        update['active'] = data.active

    if not update:
        raise HTTPException(status_code=400, detail="Nada para atualizar")

    db['cloner_pairs'].update_one({'_id': name}, {'$set': update})
    return {"message": f"✅ Par '{name}' atualizado!"}


@app.delete("/pairs/{name}", tags=["Pairs"], dependencies=[Depends(verify_token)])
def delete_pair(name: str):
    """Remove um par de clonagem"""
    from pymongo import MongoClient
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    db['cloner_pairs'].delete_one({'_id': name})
    return {"message": f"✅ Par '{name}' removido!"}


# ──────────────────────────────────────────
# CLONE
# ──────────────────────────────────────────

@app.post("/clone/{pair_name}", tags=["Clone"], dependencies=[Depends(verify_token)])
async def run_clone(pair_name: str):
    """Executa a clonagem de mensagens novas de um par"""
    from pymongo import MongoClient
    from cloner import clonar_grupo

    if not state.telegram_client:
        raise HTTPException(status_code=503, detail="Telegram client não inicializado")

    if not state.telegram_client.is_connected():
        await state.telegram_client.connect()

    mongo_uri = os.getenv('MONGO_URI')
    db = MongoClient(mongo_uri).get_default_database()
    pair = db['cloner_pairs'].find_one({'_id': pair_name})

    if not pair:
        raise HTTPException(status_code=404, detail=f"Par '{pair_name}' não encontrado")

    resultado = await clonar_grupo(
        client=state.telegram_client,
        pair_name=pair['_id'],
        origem_id=pair['origem_id'],
        destino_id=pair['destino_id'],
        mongo_uri=mongo_uri
    )

    return {
        "pair": pair_name,
        "status": "concluído",
        "copiadas": resultado['copiadas'],
        "erros": resultado['erros'],
        "ultimo_id_anterior": resultado['ultimo_id_anterior'],
        "ultimo_id_atual": resultado['ultimo_id_atual']
    }


# ──────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health():
    """Verifica se a API está online"""
    return {"status": "ok"}

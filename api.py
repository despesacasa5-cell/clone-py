from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from mongo_session import save_pair, load_pairs, save_dialogs
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

app = FastAPI(title="TG Cloner API")

# ─── Autenticação simples via token ───
def verify_token(x_token: str = Header(...)):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

# ─── Models ───
class PairModel(BaseModel):
    name: str
    origem_id: int
    destino_id: int
    horarios: List[str]  # ex: ['08:00', '12:00']

class PairUpdateModel(BaseModel):
    horarios: Optional[List[str]] = None
    active: Optional[bool] = None

# ─── Rotas ───

@app.get("/health")
def health():
    return {"status": "ok"}

# Lista todos os diálogos salvos
@app.get("/dialogs", dependencies=[Depends(verify_token)])
def get_dialogs():
    from pymongo import MongoClient
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    dialogs = list(db['dialogs'].find())
    for d in dialogs:
        d['id'] = d.pop('_id')
    return dialogs

# Lista todos os pares
@app.get("/pairs", dependencies=[Depends(verify_token)])
def get_pairs():
    mongo_uri = os.getenv('MONGO_URI')
    pairs = load_pairs(mongo_uri)
    for p in pairs:
        p['name'] = p.pop('_id')
    return pairs

# Cria um novo par
@app.post("/pairs", dependencies=[Depends(verify_token)])
def create_pair(pair: PairModel):
    mongo_uri = os.getenv('MONGO_URI')
    save_pair(mongo_uri, pair.name, pair.origem_id, pair.destino_id, pair.horarios)
    return {"message": f"Par '{pair.name}' criado com sucesso!"}

# Atualiza horários ou status de um par
@app.patch("/pairs/{name}", dependencies=[Depends(verify_token)])
def update_pair(name: str, data: PairUpdateModel):
    from pymongo import MongoClient
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    col = db['cloner_pairs']

    update = {}
    if data.horarios is not None:
        update['horarios'] = data.horarios
    if data.active is not None:
        update['active'] = data.active

    if not update:
        raise HTTPException(status_code=400, detail="Nada para atualizar")

    col.update_one({'_id': name}, {'$set': update})
    return {"message": f"Par '{name}' atualizado!"}

# Deleta um par
@app.delete("/pairs/{name}", dependencies=[Depends(verify_token)])
def delete_pair(name: str):
    from pymongo import MongoClient
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    db['cloner_pairs'].delete_one({'_id': name})
    return {"message": f"Par '{name}' removido!"}

@app.post("/clone/{pair_name}", dependencies=[Depends(verify_token)])
async def run_clone(pair_name: str):
    from pymongo import MongoClient
    from cloner import clonar_grupo

    mongo_uri = os.getenv('MONGO_URI')
    db = MongoClient(mongo_uri).get_default_database()
    pair = db['cloner_pairs'].find_one({'_id': pair_name})

    if not pair:
        raise HTTPException(status_code=404, detail="Par não encontrado")

    resultado = await clonar_grupo(
        client=client,
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
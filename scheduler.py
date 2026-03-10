from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from mongo_session import load_pairs
from cloner import clonar_grupo
import asyncio

def setup_scheduler(client, mongo_uri):
    scheduler = AsyncIOScheduler()
    pairs = load_pairs(mongo_uri)

    if not pairs:
        print("⚠️ Nenhum par encontrado no MongoDB!")
        return scheduler

    for pair in pairs:
        for horario in pair['horarios']:
            hora, minuto = horario.split(':')

            scheduler.add_job(
                clonar_grupo,
                trigger=CronTrigger(hour=int(hora), minute=int(minuto)),
                args=[client, pair['_id'], pair['origem_id'], pair['destino_id'], mongo_uri],
                id=f"{pair['_id']}_{horario}",
                replace_existing=True
            )
            print(f"⏰ [{pair['_id']}] agendado para {horario}")

    return scheduler
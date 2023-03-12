from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.routing import APIRouter
import time
import asyncio
import redis
import requests
import aiohttp


async def async_get_request(url:str, proxy:str=""):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as response:
            return response


async def async_post_request(url:str, proxy:str="", data:dict={}):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, proxy=proxy, data=data) as response:
            return response

django_url = 'http://localhost:8001/api/fastapi/'

async def send_response_to_django(tg_id:str, message:str):
    global django_url
    await async_post_request(
        url=django_url,
        data={"tg_id":tg_id, "message": message}
    )

router = APIRouter()
app = FastAPI(title="lzttgbot")
Redis = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    )



##########
# WORKER #
##########

async def worker(tg_id:int, redis):
    while True:
        if Redis.get(str(tg_id)).decode('utf-8')!='True':
            return
        await send_response_to_django(
            tg_id,
            f"is working {Redis.get(str(tg_id)).decode('utf-8')}"
        )
        await asyncio.sleep(3)

##########
# WORKER #
##########


class Data(BaseModel):
    tg_id: int

@router.post('/start')
async def start(data:Data):
    tg_id = data.tg_id
    global Redis
    if Redis.get(str(tg_id)).decode('utf-8') == 'True':
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан уже идет"
        )
    else:
        with Redis.pipeline() as pipe:
            pipe.multi()
            pipe.set(str(tg_id), 'True'.encode('utf-8'))
            result = pipe.execute()
        
        asyncio.create_task(worker(tg_id, redis))




@router.post('/stop')
async def stop(data:Data):
    tg_id = data.tg_id
    global Redis
    if Redis.get(str(tg_id)).decode('utf-8') != 'True':
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан и так не идет"
        )
    else:
        with Redis.pipeline() as pipe:
            pipe.multi()
            pipe.set(str(tg_id), 'False'.encode('utf-8'))
            result = pipe.execute()
                
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан остановлен"
        )



app.include_router(router)

# if __name__ == "__main__":
#     uvicorn.run('main:app', host="0.0.0.0", port=8000, workers=3)


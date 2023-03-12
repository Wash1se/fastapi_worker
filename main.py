from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.routing import APIRouter
import time
import asyncio
import redis
import requests


router = APIRouter()
app = FastAPI(title="lzttgbot")
Redis = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    )

django_url = 'http://localhost:8001'

##########
# WORKER #
##########

async def worker(tg_id:int, redis):
    while True:
        if Redis.get(str(tg_id)).decode('utf-8')!='True':
            return
        response = requests.post(
                url=django_url+'/api/fastapi/',
                data={"tg_id":tg_id, "message": f"is working {Redis.get(str(tg_id)).decode('utf-8')}"}
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
    with Redis.pipeline() as pipe:
        pipe.multi()
        pipe.set(str(tg_id), 'True'.encode('utf-8'))
        result = pipe.execute()
    
    asyncio.create_task(worker(tg_id, redis))
        
    return {"result": result}


@router.post('/stop')
async def stop(data:Data):
    tg_id = data.tg_id
    global Redis
    with Redis.pipeline() as pipe:
        pipe.multi()
        pipe.set(str(tg_id), 'False'.encode('utf-8'))
        result = pipe.execute()
            
    return {"result": result}



app.include_router(router)

# if __name__ == "__main__":
#     uvicorn.run('main:app', host="0.0.0.0", port=8000, workers=3)


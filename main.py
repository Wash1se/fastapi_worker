from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.routing import APIRouter
import time
import asyncio
import redis
import requests
import aiohttp
from typing import List


###############
# GLOBAL VARS #
###############


RESTRICT_MSG='К сожалению у тебя нет доступа к этому боту😢\nДля приобретения/продления доступа получи свой telegram id по команде "/get_telegram_id" и обратись к @Wash1se'
GREETING_MSG='''Привет, {}👋
    \nЧтобы начать работу, заполни конфиг файл info.json и отправь его мне
    \nВведи "/getfile", чтобы получить шаблон конфиг файла
    \nЧтобы загрузить свой конфиг файл, просто отправьте его боту
    \nВведи "/help", чтобы получить список всех комманд  
                                                    '''
ERROR_MSG="Упс... что-то пошло не так, текст ошибки: {}"
HELP_MSG='''Список всех комманд:
    \n"/start" - запуск телеграм бота
    \n"/getfile" - получить шаблон конфиг файла
    \n"/start_scanning" - начать сканирование аккаун
    \n"/stop_scanning" - закончить сканирование аккаунтов
    \n"/help" - получить список всех комманд
    \nЧтобы загрузить свой конфиг файл, просто отправьте его боту
'''






##################
# REQUESTS FUNCS #
##################

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




####################
# DB QUERIES FUNCS #
####################


def get_if_scanning(tg_id:int):
    global Redis
    if str(Redis.get(str(tg_id))).replace('b','').replace("'", "") =='True':
        return True
    return False

def set_if_scanning(tg_id:int, value:str):
    global Redis
    with Redis.pipeline() as pipe:
        pipe.multi()
        pipe.set(str(tg_id), value.encode('utf-8'))
        result = pipe.execute()




################
#DATA INSTANCES#
################

class Account(BaseModel):
    link:str
    title:str

class Config(BaseModel):
    token:str
    accounts: List[Account]
    proxy: str
    max_purchases: str

class StartData(BaseModel):
    tg_id:int
    user_config: Config

class StopData(BaseModel):
    tg_id: int



##########
# WORKER #
##########

async def worker(tg_id:int, user_config:Config):
    while True:
        print(user_config)
        if not get_if_scanning(tg_id):
            return
        await send_response_to_django(
            tg_id,
            f"is working {Redis.get(str(tg_id)).decode('utf-8')}"
        )
        await asyncio.sleep(3)




async def worker(tg_id:int, user_config:Config):

    #check if StopLztBot flag is True
    if not get_if_scanning(tg_id):
        return

    #get info from user's config
    try:
        #lztbot initializing
        lolzbot = MyLolz(token=user_config.token, tg_id=tg_id, proxy=str(user_config.proxy))

        if await lolzbot.set_lolz_id():
            #get info about max purchases user's config
            max_purchases = int(user_config.max_purchases)

            await send_response_to_django(tg_id, 'Скан аккаунтов...\nДля остановки введи "/stop_scanning"')

            while True:
                #check if StopLztBot flag is True or amount of purchased accounts is over than max purchases
                if (len(lolzbot.purchased_accounts) >= int(max_purchases)) or (not get_if_scanning(tg_id)):
                    set_if_scanning(tg_id, 'False')
                    return 

                #iterate for each account
                for account_input_info in user_config.accounts:

                    #check if StopLztBot flag is True or amount of purchased accounts is over than max purchases
                    if (len(lolzbot.purchased_accounts) >= int(max_purchases)) or (not get_if_scanning(tg_id)):
                        set_if_scanning(tg_id, 'False')
                        return False
                    
                    # try to scan accounts
                    try:
                        await lolzbot.scan_accounts(account_input_info=account_input_info, link=account_input_info['link'], max_purchases=max_purchases)
                    #handling all exceptions occured within the lztbot
                    except Exception as e:
                        await send_response_to_django(tg_id, ERROR_MSG.format(f"{e.args}\n\nбот продолжает скан"))
        else:
            await send_response_to_django(tg_id, 'Ошибка с прокси\n\nБот останавливает скан')
            set_if_scanning(tg_id, 'False')
            return         

    #handling all exceptions occured during getting info from user's config
    except Exception as e:
        await message.answer(ERROR_MSG.format(f"\n{e.args}\nСкорее всего что-то не так с вашим конфиг файлом или прокси"))
        STOP_USER_WORKER[tg_id] = True
        return







###############
# FASTAPI APP #
###############


router = APIRouter()
app = FastAPI(title="lzttgbot")
Redis = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    )


@router.post('/start')
async def start(data:StartData):
    tg_id = data.tg_id
    user_config = data.user_config

    if get_if_scanning(tg_id):
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан уже идет"
        )
    else:
        set_if_scanning(tg_id, 'True')
        asyncio.create_task(worker(tg_id, user_config))

@router.post('/stop')
async def stop(data:StopData):
    tg_id = data.tg_id

    if not get_if_scanning(tg_id):
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан и так не идет"
        )
    else:
        set_if_scanning(tg_id, 'False')
                
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан остановлен"
        )



app.include_router(router)

# if __name__ == "__main__":
#     uvicorn.run('main:app', host="0.0.0.0", port=8000, workers=3)


from pydantic import BaseModel
from sqlalchemy import Column, BigInteger, Boolean, String, DateTime
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from fastapi import FastAPI
from fastapi.routing import APIRouter

import time
import asyncio
import settings
# import redis
import uvicorn
import requests
import aiohttp
from typing import List
import json


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





########################################
# BLOCK FOR COMMON INTERACTION WITH DB #
########################################

# create async engine to interact with db
engine = create_async_engine(settings.REAL_DATABASE_URL, future=True)

#create session for the interaction with db
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



########################
# BLOCK WITH DB MODELS #
########################

Base = declarative_base()

class ScanningUser(Base):
    __tablename__ = 'scanning_users'

    tg_id = Column(BigInteger, primary_key=True)
    is_scanning = Column(Boolean(), default=False)


#######################################################
# BLOCK FOR INTERACTION WITH DB IN BUISSINESS PROCCESS#
#######################################################

class ScanningUsersDAL:
    """Data Access Layer for operating user info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_scanning_user(self, tg_id:int, is_scanning:bool) -> ScanningUser:
        new_user = ScanningUser(
            tg_id=tg_id,
            is_scanning = is_scanning
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user

    async def update_scanning_user(self, tg_id:int, **kwargs) -> ScanningUser:
        query = (
            update(ScanningUser)
            .where(ScanningUser.tg_id == tg_id)
            .values(kwargs)
            .returning(ScanningUser)
        )
        res = await self.db_session.execute(query)
        updated_user_row = res.fetchone()
        if updated_user_row is not None:
            return updated_user_row[0]



#########################
# BLOCK WITH API MODELS #
#########################

class TunedModel(BaseModel):
        class Config:
            """tells pydantic to convert even non dict objects to json"""
            orm_mode = True

class ShowAndCreateScanningUser(TunedModel):
    tg_id: int
    is_scanning: bool


#########################
# BLOCK WITH API ROUTES #
#########################

async def get_if_scanning(tg_id:int):
    async with async_session() as session:
        async with session.begin():
            result=(await session.execute(select(ScanningUser).filter_by(tg_id=tg_id))).scalar_one_or_none()
            print('RESULT', result, type(result))
            if result is None:
                return None
            else:
                return result.is_scanning

async def create_scanning_user(tg_id: int, is_scanning: bool):
    async with async_session() as session:
        async with session.begin():
            scanning_users_dal = ScanningUsersDAL(session)

            user = await scanning_users_dal.create_scanning_user(
                tg_id=tg_id,
                is_scanning=is_scanning
                )

            return ShowAndCreateScanningUser(
                tg_id=user.tg_id,
                is_scanning=user.is_scanning
            )

async def set_if_scanning(tg_id: int, is_scanning:bool):
    async with async_session() as session:
        async with session.begin():
            scanning_users_dal = ScanningUsersDAL(session)
            updated_user = await scanning_users_dal.update_scanning_user(
                tg_id=tg_id, 
                is_scanning=is_scanning
            )
            return ShowAndCreateScanningUser(
                tg_id=updated_user.tg_id,
                is_scanning=updated_user.is_scanning
            )


#async def set_if_scanning(tg_id: int, is_scanning:bool):
#    scanning_user = await get_if_scanning(tg_id)
#    print('tip', type(scanning_user), scanning_user)
#    if scanning_user != None:
#        print("Пользователь найден")
#        return await _update_scanning_user(tg_id=tg_id, is_scanning=is_scanning)
#    else:
#        print("Пользователь не найден")
#        return await _create_new_scanning_user(tg_id=tg_id, is_scanning=False)



##################
# REQUESTS FUNCS #
##################

async def async_get_request(url:str, headers:dict={}, proxy:str=""):
    async with aiohttp.ClientSession(headers=headers, trust_env=True) as session:
        async with session.get(url, proxy=proxy) as response:
            try:
                return await response.json()
            except Exception as e:
                print(e)
                return response

async def async_post_request(url:str, headers:dict=None, proxy:str=None, data:dict={}):
    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        async with session.post(url, proxy=proxy, data=data) as response:
            try:
                return await response.json()
            except:
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


# def get_if_scanning(tg_id:int):
#     global Redis
#     if str(Redis.get(str(tg_id))).replace('b','').replace("'", "") =='True':
#         return True
#     return False

# def set_if_scanning(tg_id:int, value:str):
#     global Redis
#     with Redis.pipeline() as pipe:
#         pipe.multi()
#         pipe.set(str(tg_id), value.encode('utf-8'))
#         result = pipe.execute()




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




#Custom exception for fast_buy func
class AccountBuyingError(Exception):
    pass

#Lolz bot
class MyLolz:
    
    async def set_lolz_id(self):
        if self.user_id is None:
            try:
                response = await async_get_request(url=self.__base_url, headers=self.headers, proxy=self.proxy)
                self.user_id = response['system_info']['visitor_id']
                time.sleep(3)
                return True
            except:
                return False


    def __init__(self, token:str, tg_id, proxy) -> None:
        self.proxy = proxy
        self.tg_id = tg_id
        self.user_id = None
        self.__base_url = "https://api.lzt.market/"
        self.purchased_accounts = {}

        self.page = 1
        self.headers = {
        'Authorization': f'Bearer {token}',
        }


    async def get_accounts(self, link, title):
        response = await async_get_request(link+"?nsb_by_me=1&order_by=price_to_up", headers=self.headers, proxy=self.proxy)
        await asyncio.sleep(3.2)
        if type(response) == dict:   
            try:
                response["searchUrl"]
                #await send_response_to_django(self.tg_id, f'[{time.strftime("%H:%M:%S")}] {title}: найдено {response["totalItems"]} шт')
                return response
            except:
                await send_response_to_django(self.tg_id, f"Ошибка получения аккаунтов {title}\nТекст ошибки: {response['errors'][0]}\n\nБот продолжает скан")
                return {'items':[]} 
        else:
            try:
                response.raise_for_status()
                return {'items':[]}
            except (aiohttp.ClientHttpProxyError, aiohttp.ClientProxyConnectionError): 
                return {'items':[]}
            except Exception as E:
                await send_response_to_django(self.tg_id, f"Ошибка получения аккаунтов {title}\nТекст ошибки: {E.response.reason}\n\nБот продолжает скан")
                return {'items':[]}
           # response.raise_for_status()
            #await bot.send_message(5509484655, f" get acc func: {response}")

    async def fast_buy(self, item_id:str, item_price:str, account_input_info:Account) -> bool:
        response = await async_post_request(f"{self.__base_url+item_id}/fast-buy/", headers=self.headers, proxy=self.proxy, data={"price":item_price})
        await asyncio.sleep(3)
        try:
            if response['status'] == 'ok':
                await send_response_to_django(self.tg_id, f"[{time.strftime('%H:%M:%S')}] Аккаунт {account_input_info.title} куплен")


                self.purchased_accounts[item_id]={"id":item_id, "price":item_price}
                

        except:
            await send_response_to_django(self.tg_id, 'Не удалось купить аккаунт: '+response['errors'][0]+"\n\nбот продолжает скан")
            raise AccountBuyingError
            


    async def scan_accounts(self, link=None, max_purchases=None, account_input_info:Account=None) -> None:

        link = link.replace("https://zelenka.guru/market/", self.__base_url).replace("https://lzt.market/",
        self.__base_url).replace("https://lolz.live/market/", self.__base_url).replace("https://lolz.guru/market/",
        self.__base_url).replace("https://api.lolz.guru/market/", self.__base_url)+f"&page={self.page}"

        items = await self.get_accounts(link, account_input_info.title)
         
        if items["items"] != []:
            for item in items['items']:
                if str(item["seller"]["user_id"]) == str(self.user_id): 
                    continue

                #7 = len('market/')
                category = link[link.rfind('market/')+7:link.rfind('/?')]
                    
                id = str(item['item_id'])
                price = str(item['price'])

                try:
                    await send_response_to_django(self.tg_id, f"Попытка покупки аккаунтов {account_input_info.title}...")
                    await self.fast_buy(item_id=id, item_price=price, account_input_info=account_input_info)
                except Exception as E:
                    break

                if (len(self.purchased_accounts) >= int(max_purchases)) or (not await get_if_scanning(self.tg_id)):
                    await send_response_to_django(self.tg_id, 'Бот завершил скан аккаунтов (max_purchases)')
                    await set_if_scanning(self.tg_id, False)
                    return False





async def worker(tg_id:int, user_config:Config):

    #check if StopLztBot flag is True
    if not await get_if_scanning(tg_id):
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
                if (len(lolzbot.purchased_accounts) >= int(max_purchases)) or (not await get_if_scanning(tg_id)):
                    await set_if_scanning(tg_id, False)
                    return 

                #iterate for each account
                for account_input_info in user_config.accounts:

                    #check if StopLztBot flag is True or amount of purchased accounts is over than max purchases
                    if (len(lolzbot.purchased_accounts) >= int(max_purchases)) or (not await get_if_scanning(tg_id)):
                        await set_if_scanning(tg_id, False)
                        return False
                    
                    # try to scan accounts
                    try:
                        await lolzbot.scan_accounts(account_input_info=account_input_info, link=account_input_info.link, max_purchases=max_purchases)
                    #handling all exceptions occured within the lztbot
                    except Exception as e:
                        await send_response_to_django(tg_id, ERROR_MSG.format(f"{e.args}\n\nбот продолжает скан"))
        else:
            await send_response_to_django(tg_id, 'Ошибка с прокси\n\nБот останавливает скан')
            await set_if_scanning(tg_id, False)
            return         

    #handling all exceptions occured during getting info from user's config
    except Exception as e:
        await send_response_to_django(tg_id, ERROR_MSG.format("\nСкорее всего что-то не так с вашим конфиг файлом или прокси"))
        await set_if_scanning(tg_id, False)
        return







###############
# FASTAPI APP #
###############


router = APIRouter()
app = FastAPI(title="lzttgbot")



@router.post('/start')
async def start(data:StartData):
    tg_id = data.tg_id
    user_config = data.user_config

    is_scanning = await get_if_scanning(tg_id)
    if is_scanning == True:
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан уже идет"
        )
    else:
        if is_scanning == None:
            await create_scanning_user(tg_id, True)
            print('sozdanie')
        if is_scanning == False:
            await set_if_scanning(tg_id, True)
            print('zapusk')
        asyncio.create_task(worker(tg_id, user_config))

@router.post('/stop')
async def stop(data:StopData):
    tg_id = data.tg_id
    is_scanning = await get_if_scanning(tg_id)
    
    if is_scanning is None or is_scanning == False:
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан и так не идет"
        )
    else:
        await set_if_scanning(tg_id, False)
                
        await send_response_to_django(
            tg_id=tg_id,
            message="Скан остановлен"
        )



app.include_router(router)

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8000, workers=3)


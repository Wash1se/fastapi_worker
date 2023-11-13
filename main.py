from ctypes import Union
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
from typing import List, NoReturn
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
                return response

async def async_post_request(url:str, headers:dict=None, proxy:str=None, data=None, json=None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data, proxy=proxy, json=json) as response:
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
                return True
            except:
                return False
        return True


    def __init__(self, token:str, tg_id, proxy) -> None:
        self.proxy = proxy
        self.tg_id = tg_id
        self.user_id = None
        self.id_of_ignoring_users = []
        self.__base_url = "https://api.lzt.market/"
        self.purchased_accounts = set()

        self.page = 1
        self.headers = {
        'Authorization': f'Bearer {token}',
        }

    async def load_id_of_ignoring_users(self) -> None:
        url = "https://api.zelenka.guru/users/ignored"
        response = await async_get_request(url=url, headers=self.headers, proxy=self.proxy)
        for block_user in response["users"]:
            self.id_of_ignoring_users.append(int(block_user["user_id"]))

    async def get_accounts(self, accounts_batch):
        #await send_response_to_django(5509484655, "geting accs")
        try:
            response = await async_post_request(
                url=self.__base_url+"batch/",
                headers=self.headers,
                proxy=self.proxy,
                json=accounts_batch
            )
            await asyncio.sleep(3.2)
            try:
                return response["jobs"]
                #await send_response_to_django(self.tg_id, f'[{time.strftime("%H:%M:%S")}] {title}: найдено {response["totalItems"]} шт')
            except Exception as e:
                #await send_response_to_django(5509484655, f"exc1 {e}")
                await send_response_to_django(self.tg_id, f"Ошибка получения партии аккаунтов\nТекст ошибки: {response['errors'][0]}\n\nБот продолжает работу")
                await asyncio.sleep(3.2)
                return {} 
        except Exception as e:
            await asyncio.sleep(3.2)
            return {}
           # response.raise_for_status()
            #await bot.send_message(5509484655, f" get acc func: {response}")

    async def fast_buy(self, item_id:str, item_price:str, account_title: str) -> None:
        try:
            response = await async_post_request(f"{self.__base_url+item_id}/fast-buy/", headers=self.headers, proxy=self.proxy, data={"price":item_price})
            await asyncio.sleep(3.3)
            try:
                if response['status'] == 'ok':
                    await send_response_to_django(self.tg_id, f"[{time.strftime('%H:%M:%S')}] Аккаунт {account_title} куплен")
                    self.purchased_accounts.add(item_id)
            except:
                await send_response_to_django(self.tg_id, f'Не удалось купить аккаунт: {response["errors"][0]}\n\nбот продолжает скан')

        except (aiohttp.ClientHttpProxyError, aiohttp.ClientProxyConnectionError):
            raise AccountBuyingError('Не удалось купить аккаунт: ошибка подключения (прокси/лолз)\n\nбот продолжает скан')

        except Exception as E:
            raise AccountBuyingError(f'Не удалось купить аккаунт: {E.response.reason}\n\nбот продолжает работу')

        except Exception as E:
            print(f"BUYING EXCEPTION {E}")
            pass

    async def scan_accounts(self, accounts_batch, max_purchases=None) -> bool:
        get_ten_accounts_result = await self.get_accounts(accounts_batch)
        #check if result of getting batch of acconts is emtpy and 
        if len(get_ten_accounts_result) <= 0 :
            return False #Если return пустой, значит в get_accounts была ошибка, ведь только тогда возвращается пустой словарь

        #iteration for each job(account_scanning_result)
        for account_title in get_ten_accounts_result:
            # get the value by key from response (dict)
            found_results = get_ten_accounts_result[account_title]
            #print(f"{account_title} найдено {found_results['totalItems']} шт")
            #check and send msg to client if there was an error in getting specific account
            if found_results['_job_result'] == "error":
                await send_response_to_django(
                    self.tg_id,
                    f"Ошибка получения аккаунтов {account_title}: {found_results['_job_error']}"
                )
                continue
            
            #get list of accounts of completed job
            items = found_results['items']
            
            #iterate for each account if list of accounts is not empty
            if len(items) > 0:
                for account in items:

                    #get id, price and seller_id for current account
                    id = str(account['item_id'])
                    price = str(account['price'])
                    seller_id = int(account['seller']['user_id'])

                    #check if account owner is (client or blocked user) or if account was already purchased
                    #!!!! type(id)=str and type(self.purchased_accounts)=set[str] | purchased_accounts consists of IDs
                    if (seller_id == int(self.user_id)) or (id in self.purchased_accounts) or (seller_id in self.id_of_ignoring_users):
                        continue

                    #try to buy account
                    try:
                        await send_response_to_django(self.tg_id, f"Попытка покупки аккаунтов {account_title}...")
                        await self.fast_buy(item_id=id, item_price=price, account_title=account_title)
                    except AccountBuyingError as E:
                        await send_response_to_django(self.tg_id, E)
                        break

                    #check if it is necessary to stop the bot
                    if (len(self.purchased_accounts) >= int(max_purchases)) or (not await get_if_scanning(self.tg_id)):
                        await send_response_to_django(self.tg_id, 'Бот завершил работу (max_purchases)')
                        await set_if_scanning(self.tg_id, False)
                        return False
        return True



def parse_all_links_list(accounts):
    """
    Распарсивает аккаунты из конфига пользователя в список из списков из 10 аккаунтов
    """
    MAX_BATCH_SIZE = 9
    temp_list = []
    all_links_list = []
    for account_block in accounts:
        account_name = account_block.title
        account_url = account_block.link.replace("https://zelenka.guru/market/", "https://api.lzt.market/").replace("https://lzt.market/", "https://api.lzt.market/")\
        .replace("https://lolz.live/market/", "https://api.lzt.market/").replace("https://lolz.guru/market/", "https://api.lzt.market/")\
        .replace("https://api.lolz.guru/market/", "https://api.lzt.market/")
        
        temp_list.append(
            {
                "id": account_name,
                "uri": account_url
            }
        )

    while len(temp_list) >= 1:
        min_len = min(MAX_BATCH_SIZE, len(temp_list))
        all_links_list.append(
            temp_list[:min_len]
        )
        del temp_list[:min_len]

    return all_links_list


async def worker(tg_id:int, user_config:Config):

    accounts = parse_all_links_list(user_config.accounts)
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

            await lolzbot.load_id_of_ignoring_users()

            await send_response_to_django(tg_id, f'Скан аккаунтов запущен.\nИгнорируется {len(lolzbot.id_of_ignoring_users)} пользователей.\nДля остановки введи "/stop_scanning"')
            await asyncio.sleep(3.2)

            while True:
                #check if StopLztBot flag is True or amount of purchased accounts is over than max purchases
                if (len(lolzbot.purchased_accounts) >= int(max_purchases)) or (not await get_if_scanning(tg_id)):
                    await set_if_scanning(tg_id, False)
                    return 

                #iterate for each account_batch
                for accounts_batch in accounts:
                    #check if StopLztBot flag is True or amount of purchased accounts is over than max purchases
                    if (len(lolzbot.purchased_accounts) >= int(max_purchases)) or (not await get_if_scanning(tg_id)):
                        await set_if_scanning(tg_id, False)
                        return False
                    
                    # try to scan accounts
                    try:
                        await lolzbot.scan_accounts(accounts_batch=accounts_batch, max_purchases=max_purchases)
                    #handling all exceptions occured within the lztbot
                    except Exception as e:
                        await send_response_to_django(tg_id, ERROR_MSG.format(f"{e.args}\n\nбот продолжает скан"))
        else:
            await send_response_to_django(tg_id, 'Ошибка с прокси\n\nБот завершил работу')
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
    uvicorn.run('main:app', host="localhost", port=8002, workers=3)


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




#Custom exception for fast_buy func
class AccountBuyingError(Exception):
    pass

#Lolz bot
class MyLolz:
    
    async def set_lolz_id(self):
        if self.user_id is None:
            try:
                response = requests.request("GET", self.__base_url, headers=self.headers,  proxies={'http':str(self.proxy), 'https':str(self.proxy)}).json()
                self.user_id = response['system_info']['visitor_id']
                time.sleep(3)
            except requests.exceptions.ProxyError:
                return False
        return True


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


    # async def refuse_guarantee(self, item_id:int) -> bool:
    #     response = requests.request("POST", f"{self.__base_url+str(item_id)}/refuse-guarantee", headers=self.headers,  proxies={'http':self.proxy, 'https':self.proxy}).json()
    #     await asyncio.sleep(3)
    #     try:
    #         if response['status'] == 'ok':
    #             TelegramRequests.send_message(chat_id=self.tg_id, text=f'[{time.strftime("%H:%M:%S")}] Гарантия отменена')
    #             return True
    #     except Exception:
    #         TelegramRequests.send_message(chat_id=self.tg_id, text="Ошибка отмены гарантии: "+response['errors'][0]+"\n\nБот продолжает скан")
    #         return False


    # async def cancel_account(self, item_id) -> False:
    #     response = requests.request("POST", f"{self.__base_url+item_id}/cancel-reserve/", headers=self.headers,  proxies={'http':self.proxy, 'https':self.proxy}).json()
    #     time.sleep(3)
    #     try:
    #         if response['status'] == 'ok': 
    #             TelegramRequests.send_message(chat_id=self.tg_id, text=f"[{time.strftime('%H:%M:%S')}] Бронирование отменено")
    #             del self.purchased_accounts[item_id]
    #     except Exception:
    #         TelegramRequests.send_message(chat_id=self.tg_id, text="Ошибка отмены бронирования"+str(response['errors'][0])+"\n\nБот продолжает скан")


    # async def check_goods(self, page_id:int, item_id:int, login_password:str, extra_data:dict) -> None:
    #     url = self.__base_url+f"{page_id}/goods/check"

    #     payload = {'login_password':login_password, 'resell_item_id':item_id}

    #     payload.update(extra_data)

    #     response = requests.request("POST", url, headers=self.headers, data=payload,  proxies={'http':self.proxy, 'https':self.proxy}).json()

    #     await asyncio.sleep(3)

    #     try:
    #         if response['status'] == 'ok':
    #             TelegramRequests.send_message(chat_id=self.tg_id, text=f'[{time.strftime("%H:%M:%S")}] '+response['message'])
    #     except Exception:
    #         TelegramRequests.send_message(chat_id=self.tg_id, text="Не удалось проверить аккаунт (стадия продажи): "+str(response['errors'][0])+"\n\nБот продолжает скан")


    # async def sell_item(self, item_id:int, category_id:int, title:str, price:int, item_origin:str, extended_guarantee=0, currency: str='rub', email_login_data:str=0, extra_data:dict={}) -> None:
        
    #     login_password = email_login_data
        
    #     '''check if email_login_data required Fortnite, Epic games, Escape from Tarkov'''
    #     if category_id not in (9, 12, 18):
    #         email_login_data = 0

    #     url = self.__base_url+f"item/add?category_id={category_id}&currency='rub'&title='{title}'&price={price}&item_origin={item_origin}&extended_guarantee={extended_guarantee}&has_email_login_data=1&email_login_data={email_login_data}&resell_item_id={item_id}"

    #     response = requests.request("POST", url, headers=self.headers,  proxies={'http':self.proxy, 'https':self.proxy}).json()
    #     await asyncio.sleep(3)
    #     try:
    #         if response['status'] == 'ok':
    #             await send_response_to_django(tg_id, f'[{time.strftime("%H:%M:%S")}] '+'Сознадо объявление(товар ещё не продается)')
    #             # SaveAfterPurchase.save_all_data(f"ADD ITEM INFO\n{response}\n\n")

    #             if await self.refuse_guarantee(item_id):
    #                 await self.check_goods(page_id=response['item']['item_id'], item_id=item_id, login_password=login_password, extra_data=extra_data)   
                
    #     except Exception:
    #         await send_response_to_django(tg_id, response['errors'][0]+"\n\nБот продолжает скан")
 

    async def get_accounts(self, link, title):
        try:
            response = requests.request("GET", link+"?nsb_by_me=1&order_by=price_to_up", headers=self.headers, proxies={'http':self.proxy, 'https':self.proxy}, timeout=1).json()
            await asyncio.sleep(3)
 
            try:           
                await send_response_to_django(self.tg_id, "Ошибка получения аккаунтов: "+response['message'][0])
                return {"items":[]}
            except:

                try:
                    #await bot.send_message(chat_id=5509484655, text=f"{self.message.from_user.username}'s get acc func: {response}")
                    #await send_response_to_django(self.tg_id, f'[{time.strftime("%H:%M:%S")}] {title}: найдено {response["totalItems"]} шт')
                    return response
                except Exception:
                   # await bot.send_message(chat_id=5509484655, text=f"{self.message.from_user.username}'s get acc func: {response['errors']}")
                    TelegramRequests.send_message(chat_id=self.tg_id, text=f"Ошибка получения аккаунтов: {response['errors'][0]}")
                    return {"items":[]}

        except requests.exceptions.ProxyError:
            # TelegramRequests.send_message(chat_id=self.tg_id, text="Ошибка получения аккаунтов: "+str(e))
            return {"items":[]}
        except Exception as e:
            await send_response_to_django(self.tg_id, f"Ошибка получения аккаунтов: {response.reason}")
            return {"items":[]}


    async def fast_buy(self, item_id:str, item_price:str, account_input_info:Account) -> bool:
        response = requests.request("POST", f"{self.__base_url+item_id}/fast-buy/", headers=self.headers, data={"price":item_price},  proxies={'http':self.proxy, 'https':self.proxy}).json()
        await asyncio.sleep(3)
        try:
            if response['status'] == 'ok':
                await send_response_to_django(self.tg_id, f"[{time.strftime('%H:%M:%S')}] Аккаунт {account_input_info.title} куплен")

                # item_origin=response['item']['item_origin']
                # category_id=response['item']['category_id']
                # extended_guarantee=response['item']['extended_guarantee']
                # account_data=response['item']["loginData"]["raw"]

                # SaveAfterPurchase.save_all_data(f"PURCHASE INFO\n{response}\n")
                self.purchased_accounts[item_id]={"id":item_id, "price":item_price}
                #SaveAfterPurchase.save_data(response)

                

                #extra_data = {}

                #check cinema cervice
                #if response['item']["category_id"] == 23: extra_data['extra[service_id]']=response['item']['cinema_service_id']

                #await self.sell_item(item_id=item_id, category_id=category_id, title=account_input_info['title'], price=account_input_info['price'], item_origin=item_origin, 
                   # extended_guarantee=extended_guarantee, email_login_data = account_data, extra_data=extra_data)

        except:
            await send_response_to_django(self.tg_id, 'Не удалось купить аккаунт: '+response['errors'][0]+"\n\nбот продолжает скан")
            # await cancel_account(item_id)
            raise AccountBuyingError
            


    async def scan_accounts(self, link=None, max_purchases=None, account_input_info:Account=None) -> None:

        link = link.replace("https://zelenka.guru/market/", self.__base_url).replace("https://lzt.market/",
        self.__base_url).replace("https://lolz.live/market/", self.__base_url).replace("https://lolz.guru/market/",
        self.__base_url).replace("https://api.lolz.guru/market/", self.__base_url)+f"&page={self.page}"

        items = await self.get_accounts(link, account_input_info.title)
        
        
        if items["items"] != []:

            await send_response_to_django(self.tg_id, "Попытка покупки аккаунтов...")

            for item in items['items']:
                
                if str(item["seller"]["user_id"]) == str(self.user_id): 
                    continue

                #7 = len('market/')
                category = link[link.rfind('market/')+7:link.rfind('/?')]
                    
                id = str(item['item_id'])
                price = str(item['price'])

                try:
                    await self.fast_buy(item_id=id, item_price=price, account_input_info=account_input_info)
                except:
                    break

                if (len(self.purchased_accounts) >= int(max_purchases)) or (not get_if_scanning(self.tg_id)):
                    await send_response_to_django(self.tg_id, 'Бот завершил скан аккаунтов (max_purchases)')
                    set_if_scanning(self.tg_id, 'False')
                    return False





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
                        await lolzbot.scan_accounts(account_input_info=account_input_info, link=account_input_info.link, max_purchases=max_purchases)
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

if __name__ == "__main__":
    print('zapusk')
    Redis.delete(*Redis.keys('*'))
#     uvicorn.run('main:app', host="0.0.0.0", port=8000, workers=3)


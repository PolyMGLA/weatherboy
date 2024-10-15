from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import requests
from fastapi import FastAPI
from starlette import status
from starlette.responses import Response
import uvicorn
import socketserver
import http.server

import logging
import argparse

import asyncio
import threading
import signal

from multiprocessing import Process

import time
import datetime

from api import WeatherAPI
from umanage import UserManager

START_TEXT = """
Привет! Напиши в чат город, в котором ты бы хотел узнать погоду
Напиши /help, чтобы узнать команды
Напиши /unreg, чтобы отписаться от уведомлений"""

HELP_TEXT = """WeatherBoy 1.0
[город] - выбрать город
/setdelay - выбрать интервал между отправками погоды
/help - помощь
/unreg - отписаться от уведомлений
"""

OPENWEATHER_API_CODE = "2cfb820c66102664ba3d1ec88b0b00bb"
BOT_TOKEN = "7759246153:AAGXNAMUHQAK-DC58hdr47a6GfCHrl7dIGU"
FORMAT = r'%Y-%m-%d %H:%M:%S'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

wapi = WeatherAPI(OPENWEATHER_API_CODE)
UManager = UserManager("users.db")

inline_btn_delay_1 = InlineKeyboardButton(text='Каждую минуту', callback_data='button1')
inline_btn_delay_5 = InlineKeyboardButton(text='Каждые 5 минут', callback_data='button5')
inline_btn_delay_20 = InlineKeyboardButton(text='Каждые 20 минут', callback_data='button20')
inline_btn_delay_30 = InlineKeyboardButton(text='Каждые 30 минут', callback_data='button30')
inline_btn_delay_60 = InlineKeyboardButton(text='Каждый час', callback_data='button60')
inline_btn_delay_180 = InlineKeyboardButton(text='Каждые 3 часа', callback_data='button180')
inline_kb_delay = InlineKeyboardBuilder().row(inline_btn_delay_1) \
                                        .row(inline_btn_delay_5) \
                                        .row(inline_btn_delay_20) \
                                        .row(inline_btn_delay_30) \
                                        .row(inline_btn_delay_60) \
                                        .row(inline_btn_delay_180).as_markup()
"""
app = FastAPI()

@app.get("/")
def index():
    return {"text": "text"}
"""


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print("Received from {}:".format(self.client_address[0]))
        print(self.data)
        self.request.sendall(self.data.upper())

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    # определяем метод `do_GET` 
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

PORT = 3000

#Handler = http.server.SimpleHTTPRequestHandler
Handler = SimpleHTTPRequestHandler

@dp.message(Command(commands=["start"]))
async def start(message: types.Message) -> None:
    await message.answer(START_TEXT)

@dp.message(Command(commands=["help"]))
async def help(message: types.Message) -> None:
    await message.answer(HELP_TEXT)

@dp.message(Command(commands=["setdelay"]))
async def setdelay(message: types.Message) -> None:
    await message.reply("Выберите частоту отправки погоды:", reply_markup=inline_kb_delay)

@dp.message(Command(commands=["unreg"]))
async def unreg(message: types.Message) -> None:
    UManager.execute_query(f"DELETE FROM users WHERE id={message.from_user.id}")
    await message.answer("Уведомления отключены")

@dp.message()
async def setcity(message: types.Message) -> None:
    UManager.register(message.from_user.id, message.text)
    UManager.update_city(message.from_user.id, message.text)
    await message.answer(f"Город изменен на: {message.text}")

@dp.callback_query(F.data[:6] == 'button')
async def process_callback_button1(callback_query: types.CallbackQuery) -> None:
    global FLAG_RUNNING
    await bot.answer_callback_query(callback_query.id)
    UManager.update_delay(callback_query.from_user.id, int(callback_query.data[6:]))
    UManager.update_timer(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, f"Частота отправки: раз в {callback_query.data[6:]} минут(-у)")
    await bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id, 
        reply_markup=None
    )
    FLAG_RUNNING = False
    # asyncio.create_task(send_weather(callback_query.from_user.id, 60 * int(callback_query.data[6:])))


async def send_weather(user_id, delay) -> None:
    """
    Функция отправки погоды пользователю tid

    :param user_id: ID пользователя
    :param delay: Задержка перед отправкой
    """
    try:
        await bot.send_message(user_id, wapi.get_weather(UManager.get_city(user_id)))
    except requests.exceptions.Timeout:
        logging.warning("API is not responding. i think its dead xd")
    UManager.update_timer(user_id, delay)

async def sleep(delay):
    start = time.time()
    cnt = 0
    while (time.time() - start < delay) and FLAG_RUNNING:
        if cnt % 60 == 0:
            requests.get("http://localhost:3000")
        cnt += 1
        await asyncio.sleep(1)

async def eloop() -> None:
    global FLAG_RUNNING
    while True:
        us = UManager.get_userlist()
        mn = min(list(map(lambda x: datetime.datetime.strptime(x[2], FORMAT), us)) + [datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp() + 1800)])
        print(mn)
        FLAG_RUNNING = True
        await sleep(max((mn - datetime.datetime.now()).total_seconds(), 0))
        FLAG_RUNNING = False
        logging.debug("timed")
        us = UManager.get_userlist()
        for x in us:
            if datetime.datetime.strptime(x[2], FORMAT) <= datetime.datetime.now():
                await send_weather(x[0], x[3] * 60)
        await asyncio.sleep(1)

# def signal_handler():
#     for task in asyncio.all_tasks():
#         task.cancel()

def listen3000() -> None:
    # uvicorn.run('main:app', port=3000)
    # with socketserver.UDPServer(("localhost", 3000), MyTCPHandler) as server:
    #     server.serve_forever()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()

async def main():
    """
    Основная функция, отвечающая за обработку сообщений ботом, настройку логирования, работы с базой данных пользователей
    """
    logging.basicConfig(filename="logs.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--drop", help="-d(--drop): дропнуть базу данных и создать пустую")
    args = parser.parse_args()
    if args.drop == "1":
        UManager.RECREATE()

    UManager.INIT()
    print(UManager.get_userlist())
    await dp.start_polling(bot)

async def launcher():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(main())
        task2 = tg.create_task(eloop())
        await task1
        task2.cancel()
    # loop = asyncio.get_running_loop()
    # loop.add_signal_handler(signal.SIGINT, signal_handler)
    

if __name__ == "__main__":
    # event_loop = Process(target=eloop)
    # event_loop.start()
    # asyncio.create_task(eloop())

    l3000 = threading.Thread(target=listen3000)
    l3000.start()

    asyncio.run(launcher())

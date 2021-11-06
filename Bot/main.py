"""
This is a echo bot.
It echoes any incoming text messages.
"""

import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import reply_keyboard
from dotenv import dotenv_values

os.path.split(__file__)
bot_path , _ = os.path.split(__file__)
config = dotenv_values( os.path.join(bot_path, ".env"))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config["API_TOKEN"])
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=3)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    btns_text = ('Yes!', 'No!')
    keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))
    # adds buttons as a new row to the existing keyboard
    # the behaviour doesn't depend on row_width attribute

    more_btns_text = (
        "1:2:1\nНовый",
        "Q:A:2\nСтарый",
        "pr:1:2\nСтарый",
        "Where am i?",
        "Who is there?",
        "Who is there?",
        "Who is there?",
        "Who is there?",
        "Who is there?",
        "Who is there?",
    )
    keyboard_markup.add(*(types.KeyboardButton(text) for text in more_btns_text))

    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.", reply_markup=keyboard_markup)


@dp.message_handler(regexp='(^cat[s]?$|puss)')
async def cats(message: types.Message):
    with open('data/cats.jpg', 'rb') as photo:
        '''
        # Old fashioned way:
        await bot.send_photo(
            message.chat.id,
            photo,
            caption='Cats are here 😺',
            reply_to_message_id=message.message_id,
        )
        '''

        await message.reply_photo(photo, caption='Cats are here 😺')


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)

    await message.answer(message.text)


if __name__ == '__main__':
    dp
    executor.start_polling(dp, skip_updates=True)

import json
import logging
from re import A
from typing import Text

from telegram import Update, ForceReply, update, user, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, JobQueue, jobqueue, CallbackQueryHandler

import redis

import r_var


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


r = redis.Redis(host="localhost", port=6379, db=0)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext, ) -> None:
    """Send a message when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data='1'),
            InlineKeyboardButton("Option 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    #user = update.effective_user
    #update.message.reply_markdown_v2(
    #    fr'Hi {user.mention_markdown_v2()}\!',
    #    reply_markup=ForceReply(selective=True),
    #)

def del_listener(update: Update, context: CallbackContext) -> None:
    """/cmd2"""
    user_id = update.message.chat_id
    user_id = bytes(str(user_id), encoding='utf-8')
    
    if not r.srem(r_var.user,user_id):
        update.message.reply_text("Вы не получали уведомления")
    
    text = """
    Уведомления отключены
    """
    update.message.reply_text(text)


def add_listener(update: Update, context: CallbackContext) -> None:
    """/cmd1"""
    user_id = update.message.chat_id
    user_id = bytes(str(user_id), encoding='utf-8')
    
    if user_id in r.smembers(r_var.user):
        update.message.reply_text("Вы уже получаете уведомления")

    r.sadd(r_var.user,user_id)
    
    user_id = update.message.chat_id
    r_user = f"listener:{user_id}"
    user_context = {}
    
    if r.exists(r_user):
        user_context = json.loads(r.get(r_user))

    else:

        pass
    
    last_meas = r.lrange(r_var.meas_list, -1, -1)
    last_meas = json.loads(last_meas[0])
    user_context['last_id'] = str(last_meas['head'][3])
    user_context['name'] = update.effective_user.first_name
    r.set(r_user, json.dumps(user_context))    

    text = """
    Уведомления включены
    """
    update.message.reply_text(text)

def check_QC_event(context: CallbackContext):
    """
    Проверяет появились ли уведомления
    Если появилсись, отправляет тем кто подписался на уведомления 
    Для каждого пользователя обновляет информацию о последнем полученном им сообщении
    Удаляет флаг нового уведомления
    """
    if not r.exists(r_var.event_name):
        return

    users = r.smembers(r_var.user)
    last_id = r.get(r_var.id)
    last_id = last_id.decode('utf-8')

    #Преобразование элементов массива к типу int
    users = [int(el.decode('utf-8')) for el in users ]

    text=f"Info {last_id}\n"



    for user in users:
        r_user = f"listener:{user}"
        
        if r.exists(r_user):
            user_context = r.get(r_user)
            user_context = json.loads(user_context)

            if user_context['last_id'] < last_id:
                #Взять список из Redis
                meas_list = r.lrange(r_var.meas_list, 0, -1)
                #Данные в списке былы словарями, ниже из строк восстанавливается список словарей
                meas_list = [json.loads(el) for el in meas_list]
                
                for meas in meas_list:
                    #Если пользователь не получал уведомления, отправить все неполученные 
                    if int(user_context['last_id']) < meas['head'][3] :
                        cur_text = '*ID: {}*\n\n'.format(meas['head'][3])
                        cur_text += 'Партия: #{}\n'.format(meas['head'][0])
                        cur_text += 'Номер коробки: {}\n'.format(meas['head'][1])
                        cur_text += 'Номер детали: {}\n\n'.format(meas['head'][2])
                        
                        index = 1 
                        for size in meas['body']:
                            cur_text += 'Размер {} || {} : {} : {}\n'.format(
                                index,
                                size[0],
                                size[1],
                                size[2],
                            )
                            index+=1
                            if type(size[0]) != float :
                                cur_text += "---> {} <---\n\n".format(size[3])
                                continue

                            mid = size[0]+(size[1]+size[2])/2
                            delta = abs(mid-size[3])

                            if (abs(size[1]) + abs(size[2]))/2 < delta :
                                cur_text += "XXX> {} <XXX\n\n".format(size[3])
                            elif (abs(size[1]) + abs(size[2]))/2*0.8 < delta :
                                cur_text += "!!!> {} <!!!\n\n".format(size[3])
                            else:
                                cur_text += "===> {} <===\n\n".format(size[3])

                        context.bot.sendMessage(
                            chat_id=user,
                            text=cur_text,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        #Обновление информации о последнем отправленном id
                        user_context['last_id'] = str(meas['head'][3])

                #context.bot.sendMessage(chat_id=user, text=text)

        else:
            user_context = {
                "last_id" : last_id
            }
            
            context.bot.sendMessage(chat_id=user, text=text)
        
        #Фиксирует последний обработанный id для указанного слушателя(user)
        r.set(r_user,json.dumps(user_context))


    r_event = int(r.get(r_var.event_name))

    r.delete(r_var.event_name)


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


#def echo(update: Update, context: CallbackContext) -> None:
#    """Echo the user message."""
#    update.message.reply_text(update.message.text)
def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text=f"Selected option: {query.data}")

def main() -> None:
    """Start the bot."""
    API_TOKEN = 'YOUR_API_TOKEN'
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    jobqueue = updater.job_queue

    jobqueue.run_repeating(check_QC_event,interval=5)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("cmd1", add_listener))
    dispatcher.add_handler(CommandHandler("cmd2", del_listener))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
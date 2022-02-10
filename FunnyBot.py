import os
import dotenv
import requests
import telebot
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import KeyboardButton, ReplyKeyboardMarkup
from telebot import custom_filters

dotenv.load_dotenv()

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

analytics_FUNNY_BOT = client.open("ANALYTICS").worksheet("FUNNY BOT")
database = client.open("DATABASE").worksheet("FUNNY BOT")

def chk_flags(id):

    row = database.find(str(id)).row
    col = database.find(str(id)).col 

    flags = {
        "nsfw"      : bool(int(database.cell(row, col+1).value)),   
        "religious" : bool(int(database.cell(row, col+2).value)),
        "political" : bool(int(database.cell(row, col+3).value)),
        "racist"    : bool(int(database.cell(row, col+4).value)),
        "sexist"    : bool(int(database.cell(row, col+5).value)),
        "explicit"  : bool(int(database.cell(row, col+6).value))
        }

    flags_url = ""      # flags have to be in the order defined in the API

    for flag in flags:

        if flags[flag] == True:
            flags_url += f"{flag},"

    if flags_url == "":
        return ""

    else:
        return f"?blacklistFlags={flags_url.strip(',')}"
        
bot = telebot.TeleBot(os.getenv("API_KEY"))
laugh_stk = "CAACAgIAAxkBAAO6YVxv71IuFY0EwKNSRPC4DbNnZrYAAs0OAAJ6QWhKw2w88rSx1sMhBA"

@bot.message_handler(commands=['start'])
def start(message):

    col = database.col_values(1)

    if str(message.chat.id) not in col:
        database.append_row([message.chat.id, 0, 0, 0, 0, 0, 0])
        analytics_FUNNY_BOT.update_acell('F10', str(
            len(database.col_values(1))-1).replace("'", " "))

    bot.send_message(message.chat.id, "Welcome to the Funny Telegram bot! 🤣\n\n\
I can send you random jokes. Specifiying a category like Dark, Pun, Spooky or Christmas is possible too.\n\n\
Send /help for more information.\n\nLaugh a lot! 😂")
    bot.send_sticker(message.chat.id, laugh_stk)
    
    start_count = analytics_FUNNY_BOT.acell('F3').value
    analytics_FUNNY_BOT.update_acell(
        'F3', str(int(start_count)+1).replace("'", " "))

@bot.message_handler(commands=['joke'])
def Joke(message):

    key = telebot.util.extract_arguments(message.text).upper()
    categories = ["", 'PROGRAMMING','MISC','DARK','PUN','SPOOKY','CHRISTMAS']

    if key in categories:

        if key == "MISC":
            key = "MISCELLANEOUS"

        flags = chk_flags(message.chat.id)

        if key == "":

            url = f"https://v2.jokeapi.dev/joke/Any{flags}"

        else:

            url = f"https://v2.jokeapi.dev/joke/{key.capitalize()}{flags}"

        raw_joke = requests.get(url=url).json()

        if raw_joke["error"] == "true":
            bot.send_message(message.chat.id, "Request to the API failed.\n\nPlease try again later.\n\n\
<i>For more information, visit: <b><a href='https://status.sv443.net/'>STATUS PAGE</a></b>.</i>",
            parse_mode="HTML", disable_web_page_preview = True)
        else:    
            if raw_joke["type"] == 'single':

                bot.send_message(message.chat.id, raw_joke["joke"])
            else:

                msg_id = bot.send_message(message.chat.id, raw_joke["setup"])
                time.sleep(2)
                bot.send_message(message.chat.id, raw_joke["delivery"],reply_to_message_id=msg_id.id)
        
    else:
        bot.send_message(message.chat.id, "No such category found :(\n\nUse /help for the list of categories.")
    
    category_count = analytics_FUNNY_BOT.acell('F4').value
    analytics_FUNNY_BOT.update_acell(
        'F4', str(int(category_count)+1).replace("'", " "))

@bot.message_handler(commands=['blocklist'])
def block(message):

    row = database.find(str(message.chat.id)).row
    col = database.find(str(message.chat.id)).col 
    msg = "CURRENT FLAGS STATUS:\n\n"

    flags = {
        "nsfw"      : bool(int(database.cell(row, col+1).value)),
        "religious" : bool(int(database.cell(row, col+2).value)),
        "political" : bool(int(database.cell(row, col+3).value)),
        "racist"    : bool(int(database.cell(row, col+4).value)),
        "sexist"    : bool(int(database.cell(row, col+5).value)),
        "explicit"  : bool(int(database.cell(row, col+6).value))
        }

    for flag in flags:
        if flags[flag] == False:
            msg += f"🟢 {flag.upper()}\n\n"
        else:
            msg += f"🔴 {flag.upper()}\n\n"

    bot.send_message(message.chat.id, msg)

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    F1 = KeyboardButton("NSFW")   
    F2 = KeyboardButton("RELIGIOUS")
    F3 = KeyboardButton("POLITICAL")
    F4 = KeyboardButton("RACIST")
    F5 = KeyboardButton("SEXIST")
    F6 = KeyboardButton("EXPLICIT")   

    markup.row(F1, F2, F3)
    markup.row(F4, F5, F6)

    bot.send_message(message.chat.id, "Choose the flag that you want to edit:", reply_markup=markup)

    blocklist_count = analytics_FUNNY_BOT.acell('F5').value
    analytics_FUNNY_BOT.update_acell(
        'F5', str(int(blocklist_count)+1).replace("'", " "))

@bot.message_handler(text=['NSFW','RELIGIOUS','POLITICAL','RACIST','SEXIST','EXPLICIT'])
def text_filter(message):

    markup = InlineKeyboardMarkup()
    I1 = InlineKeyboardButton("BLOCK 🔴", callback_data = f"block,{message.text},{message.chat.id}")
    I2 = InlineKeyboardButton("UNBLOCK 🟢", callback_data = f"unblock,{message.text},{message.chat.id}")
    markup.row(I1, I2)

    bot.send_message(message.chat.id, "Please select your choice 👇🏻", reply_markup=markup)

bot.add_custom_filter(custom_filters.TextMatchFilter())

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "Thanks for using the Funny Telegram bot.\
After starting the bot with /start you can request jokes by using the /joke command.\
You can specify a category by writing it after the command /category.\
The available categories are Misc, Dark, Pun, Programming, Spooky and Christmas.\
Example: /category Dark\
If you wish to avoid certain categories in general, you can do so with the /blocklist command.\
If you would like to contact me send /contact.\
Feedback is very appreaciated by filling out a Google form which the bot will send you after sending him /feedback.\
Have fun! 🥳")
    help_count = analytics_FUNNY_BOT.acell('F6').value
    analytics_FUNNY_BOT.update_acell(
        'F6', str(int(help_count)+1).replace("'", " "))

@bot.message_handler(commands=['contact'])
def contact(message):
    contact_info = '''
*CONTACT :*\n
Telegram: https://t\.me/Marvin\_Marvin\n
Mail: marvin@poopjournal\.rocks\n
Issue: https://github.com/Crazy-Marvin/FunnyTelegramBot/issues\n
Source: https://github.com/Crazy-Marvin/FunnyTelegramBot
''' 
    bot.send_message(message.chat.id, contact_info,disable_web_page_preview=True)

    contact_count = analytics_FUNNY_BOT.acell('F7').value
    analytics_FUNNY_BOT.update_acell(
        'F7', str(int(contact_count)+1).replace("'", " "))

@bot.message_handler(commands=['feedback'])
def feedback(message):
    bot.send_message(message.chat.id, "I would love to hear your feedback.\n\nhttps://forms.gle/Rj1AxXbpydAQkUcUA",
    disable_web_page_preview=True)

    feedback_count = analytics_FUNNY_BOT.acell('F8').value
    analytics_FUNNY_BOT.update_acell(
        'F8', str(int(feedback_count)+1).replace("'", " "))

@bot.message_handler(commands=['logs'])
def logs(message):

    if message.chat.id == os.getenv('my_id') or message.chat.id == os.getenv('analyst_id'):

        bot.send_message(message.chat.id,
        f"Check out the *[ANALYTICS]({os.getenv('ANALYTICS_LINK')})* for the month\.", parse_mode="MarkdownV2", disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):

    cell = database.find(str(call.message.chat.id))
    data = call.data.split(',')
    
    if data[0] == "block":
        
        if data[1] == "NSFW":

            database.update_cell(cell.row, cell.col + 1, '1')
            bot.edit_message_text("NSFW ➤ 🔴", int(data[2]), call.message.id)

        elif data[1] == "RELIGIOUS":

            database.update_cell(cell.row, cell.col + 2, '1')
            bot.edit_message_text("RELIGIOUS ➤ 🔴", int(data[2]), call.message.id)

        elif data[1] == "POLITICAL":

            database.update_cell(cell.row, cell.col + 3, '1')
            bot.edit_message_text("POLITICAL ➤ 🔴", int(data[2]), call.message.id)

        elif data[1] == "RACIST":

            database.update_cell(cell.row, cell.col + 4, '1')
            bot.edit_message_text("RACIST ➤ 🔴", int(data[2]), call.message.id)

        elif data[1] == "SEXIST":

            database.update_cell(cell.row, cell.col + 5, '1')
            bot.edit_message_text("SEXIST ➤ 🔴", int(data[2]), call.message.id)

        elif data[1] == "EXPLICIT":

            database.update_cell(cell.row, cell.col + 6, '1')
            bot.edit_message_text("EXPLICIT ➤ 🔴", int(data[2]), call.message.id)

    if data[0] == "unblock":

        if data[1] == "NSFW":

            database.update_cell(cell.row, cell.col + 1, '0')
            bot.edit_message_text("NSFW ➤ 🟢", int(data[2]), call.message.id)

        elif data[1] == "RELIGIOUS":

            database.update_cell(cell.row, cell.col + 2, '0')
            bot.edit_message_text("RELIGIOUS ➤ 🟢", int(data[2]), call.message.id)

        elif data[1] == "POLITICAL":

            database.update_cell(cell.row, cell.col + 3, '0')
            bot.edit_message_text("POLITICAL ➤ 🟢", int(data[2]), call.message.id)

        elif data[1] == "RACIST":

            database.update_cell(cell.row, cell.col + 4, '0')
            bot.edit_message_text("RACIST ➤ 🟢", int(data[2]), call.message.id)

        elif data[1] == "SEXIST":

            database.update_cell(cell.row, cell.col + 5, '0')
            bot.edit_message_text("SEXIST ➤ 🟢", int(data[2]), call.message.id)

        elif data[1] == "EXPLICIT":

            database.update_cell(cell.row, cell.col + 6, '0')
            bot.edit_message_text("EXPLICIT ➤ 🟢", int(data[2]), call.message.id)

bot.polling()

#TODO: ADD LANGUAGE SUPPORT
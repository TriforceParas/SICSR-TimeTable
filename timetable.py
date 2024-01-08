# Flash Import
from flask import Flask, request, render_template
from datetime import datetime
from urllib.request import urlopen, Request
from re import search

# Telegram import
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask 
name_bot = []
def get_data():
    app: Flask = Flask(__name__)

    programmes: dict = dict()
    with urlopen("http://time-table.sicsr.ac.in/day.php") as response:
        for line in response.read().decode("UTF-8").splitlines():
            line: str = line.strip()
            match = search(r'<option value="([^"]+)">([^<]+)</option>', line)
            if not match:
                continue
            value, programme = match.group(1), match.group(2)
            if value.isalpha() and not programme.startswith("type."):
                programmes[programme] = value


    programme = list(programmes.keys())[0]
    courses: list[dict] = list()
    index = -1
    date = ['']
    if date == ['']:
        date = ['0', '0', '0']
    with urlopen(Request("http://time-table.sicsr.ac.in/day.php",
                            f"type=F&year={date[0]}&month={date[1]}&day={date[2]}&submit=Submit".encode('UTF-8'))) as courses_response:
        date = ["", ""]
        for courses_response_line in courses_response.read().decode('UTF-8').splitlines():
            courses_response_line: str = courses_response_line.strip()
            match = search(
                r'<a\s+[^>]*href="([^"]*view_entry[^"]*)"[^>]*>', courses_response_line)
            if match:
                index += 1
                courses.append(dict())
                with urlopen(
                        f'http://time-table.sicsr.ac.in/{match.group(1).replace("amp;", "")}&action=export') as view_entry_response:
                    for view_entry_line in view_entry_response.read().decode("UTF-8").splitlines():
                        if view_entry_line.startswith("SUMMARY:"):
                            courses[index]["Course"] = view_entry_line.split(":", 2)[
                                1]
                        elif view_entry_line.startswith("LOCATION:SICSR/"):
                            courses[index]["Room"] = view_entry_line.strip(
                                "LOCATION:SICSR/")
                        else:
                            starttime = view_entry_line.startswith(
                                "DTSTART;TZID")
                            endtime = view_entry_line.startswith(
                                "DTEND;TZID")
                            if starttime or endtime:
                                time = datetime.strptime(view_entry_line.split(":", 1)[
                                    1].strip(), "%Y%m%dT%H%M%S")
                                if date[1] == "":
                                    date[1] = time.strftime("%A %d-%m-%Y")
                                courses[index]["Start" if starttime else "End"] = time.strftime(
                                    "%I:%M %p")
                            elif view_entry_line.startswith("STATUS:") and view_entry_line != "STATUS:CONFIRMED":
                                del courses[index]
                                break
    # Telegram             
    rename_bot = {
        'BCA II Div F -Creative Writing-Mrinmayi Shrirang Huprikar': 'Creative Writing',
        'BCA II Div F -Server Side Web Technology-Ms. Rasila Walhekar': 'Server Side Web tech',
        'BCA II Div F-Relational Database Management System-Mr.Shirish Joshi': 'RDBMS',
        'BCA II Div F -Data Structures and  Algorithms-Ms.Janhavi Pednekar': 'DSA'
    }

    for i in courses:
        if i['Course'] in rename_bot:
            cache = {}
            cache['Start'] = i['Start']
            cache['End'] = i['End']
            cache['Room No.'] = i['Room']
            cache['Subject'] = rename_bot[i['Course']]
            name_bot.append(f"{cache['Room No.']}-{cache['Subject']} @ {cache['Start']} to {cache['End']}")




TOKEN: Final = '6319224437:AAEru3iSAodSN0d6VXlecvZAD1xfvNAi4WE'
BOT_USERNAME: Final = '@SICSR_time_table_bot'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Welcom to SICSR Time Table bot type /table to get latest time table')

async def table_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_data()
    await update.message.reply_text(name_bot)
    
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('table', table_command))
    
    print('Bot Has Started')
    app.run_polling(poll_interval=3)

from os import sep, mkdir

from apscheduler.schedulers.background import BackgroundScheduler
import logging

from bot.helpers import *


# set scheduler
scheduler = BackgroundScheduler()

# Set working directory to store the data
mkdir('Data') if not path.isdir('Data') else None

# Initial Client
bot = Client("MySandBox")

# Creat logger
logger = logging.getLogger('main')
_format = '%(asctime)s - %(levelname)s - %(name)s : %(message)s'
logging.basicConfig(format=_format, filename=f'Data{sep}bot.log')

# Defining data files name depending the session name
CREATOR = None  # TODO: insert the creator ID
DATA_FILE = f"Data{sep}{bot.session_name}"

# import data
if path.isfile(f'{DATA_FILE}_data.json'):
    with open(f'{DATA_FILE}_data.json', 'r') as f:
        data = json.load(f, parse_int=int)
else:
    data = {'start_msg': '', 'group': None, 'non_participant': '', 'ban': list()}

# import translation and messages
with open(f'bot{sep}language.json', 'r', encoding='utf8') as f:
    MSG = json.load(f, parse_int=int)


@bot.on_disconnect()
def turning_off(c: Client):
    """
    function to class the program gently in case of connection error.
    this function logging the error and close the program with code 1
    :param c: :pyrogram.Client: the disconnected client.
    """
    if c.is_initialized:
        logger.critical(f'connection error on: {c.session_name} with token: {c.bot_token}')
        save_data()
        clean_cash()
        scheduler.shutdown(wait=False)
        exit(1)


def run():
    """
    run the bot
    """
    DB.bind(provider='sqlite', filename=f"{DATA_FILE}_DB.sqlite", create_db=True)
    DB.generate_mapping(create_tables=True)
    add_user(CREATOR, is_admin=True)
    scheduler.add_job(clean_cash, trigger='interval', days=1)
    scheduler.start()
    bot.run()


if __name__ == '__main__':
    run()

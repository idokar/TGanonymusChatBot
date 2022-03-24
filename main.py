import configparser
import re

from apscheduler.schedulers.background import BackgroundScheduler
from bot.helpers import *

# Creat logger #
_logger = logging.getLogger('main')
_format = '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s : %(message)s'
logging.basicConfig(format=_format, filename=f'Data{os.sep}bot.log')

# Config #
_config = configparser.ConfigParser()
_config.read('config.ini')
_session = _config['init']['session_name']
if not _session or _session == ':memory:':
    msg = "The session_name can't be ':memory:' or empty"
    _logger.error(msg)
    raise ValueError(msg)
elif re.search(r'[/:*?"<>|~&#%+{}\\]', _session) or len(_session) > 244:
    msg = r'The session_name can not contain: \ / : * ? " < > | ~ & # % + { }'
    _logger.error(msg)
    raise NameError(msg)

CREATOR = _config['init'].getint('creator')

# set scheduler and Telegram client #
_scheduler = BackgroundScheduler()
bot = Client(_session)

# Defining data files name depending the session name #
DATA_FILE = f"Data{os.sep}{_session}"

# Import data #
if os.path.isfile(f'{DATA_FILE}_data.json'):
    with open(f'{DATA_FILE}_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f, parse_int=int)
else:
    data = {'start_msg': '', 'group': None, 'non_participant': '', 'ban': list()}


@bot.on_disconnect()
async def turning_off(c: Client):
    """
    function to class the program gently in case of connection error.
    this function logging the error and close the program with code 1
    :param c: :pyrogram.Client: the disconnected client.
    """
    if c.is_initialized:
        _logger.critical(
            f'connection error on: {c.session_name} with token: {c.bot_token} PID: {os.getpid()}'
        )
        save_data()
        clean_cash()
        _scheduler.shutdown(wait=False)
        exit(1)


def main(db_type: str, **db_kwargs):
    """
    setup and run the bot
    """
    DB.bind(provider=db_type, **db_kwargs)
    DB.generate_mapping(create_tables=True)
    add_user(CREATOR, admin=True)
    _scheduler.add_job(clean_cash, trigger='interval', days=1)
    _scheduler.start()
    _logger.warning(f'Start running. PID: {os.getpid()}')
    bot.run()


if __name__ == '__main__':
    main(db_type='sqlite', filename=f"{DATA_FILE}_DB.sqlite", create_db=True)

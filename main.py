from configparser import ConfigParser
import re

from apscheduler.schedulers.background import BackgroundScheduler
from bot.helpers import *

# Creat logger #
_logger = logging.getLogger('main')
_format = '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s : %(message)s'
logging.basicConfig(format=_format, filename=f'Data{os.sep}bot.log')

# Config #
_config = ConfigParser(inline_comment_prefixes=('#',))
_config.read('config.ini')
_session = _config['init']['session_name']
if not _session or re.search(r'[/:*?"<>|~&#%+{}\\]', _session) or len(_session) > 244:
    msg = r'The session_name can not contain: \ / : * ? " < > | ~ & # % + { }'
    _logger.error(msg)
    raise NameError(msg)

CREATOR = _config['init'].getint('creator')

# set scheduler and Telegram client #
_scheduler = BackgroundScheduler()
bot = Client(_session, api_id=_config['pyrogram'].getint('api_id'),
             api_hash=_config['pyrogram']['api_hash'],
             bot_token=_config['pyrogram']['bot_token'],
             plugins=dict(_config['plugins']))

# Defining data files name depending the session name #
DATA_FILE = f"Data{os.sep}{_session}"

# Import data #
if os.path.isfile(f'{DATA_FILE}_data.json'):
    with open(f'{DATA_FILE}_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f, parse_int=int)
else:
    data = {'start_msg': '', 'group': None, 'non_participant': '', 'ban': list()}


def main(db_type: str, **db_kwargs):
    """
    Setup and run the bot
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

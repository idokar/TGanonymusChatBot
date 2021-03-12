import logging

from pyrogram import StopPropagation
from bot.helpers import *
from main import CREATOR

_logger = logging.getLogger(__name__)


@Client.on_message(filters.command(COMMANDS['demote'] + COMMANDS['promote']) &
                   filters.chat(CREATOR))
async def set_admins(_, m: Message):
    """
    handler function to promote / demote admins in the bot. (only for the CREATOR)
    :param m: the message.
    """
    if not m.reply_to_message and len(m.command) == 2:
        uid = m.command[1]
        try:
            if not get_user(int(uid)):
                return _logger.debug("couldn't find a user")
        except ValueError:
            return _logger.debug("couldn't find a user, using wrong ID")
    elif not m.reply_to_message:
        return _logger.debug("not replayed to a message")
    else:
        uid = get_id(m)
        if not uid:
            return _logger.debug("couldn't find a user in the message")

    state = True if m.command[0] in COMMANDS['promote'] else False
    with db_session:
        get_user(uid).is_admin = state
    await m.reply(format_message('success_add_admin' if state else 'success_remove_admin',
                                 get_user(uid), lang=get_user(m.from_user.id).language
                                 ))
    raise StopPropagation()

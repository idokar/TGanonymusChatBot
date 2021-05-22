from pyrogram.errors import PeerIdInvalid, UserIsBlocked
from bot.helpers import *

_logger = logging.getLogger(__name__)


@db_session
def report_to_admins(admin: User, user: User, c: Client, message: str):
    """
    function to report the admins that admin blocked / released user.
    :param admin: the admin that blocked / released the user.
    :param user: the user that was blocked / released.
    :param c: pyrogram.Client to send the message.
    :param message: the key of which message to send to the admins.
    """
    for k, v in get_admins().items():
        if k != admin.uid:
            try:
                c.send_message(
                    k,
                    format_message(message, user, admin=admin.link(), lang=v.language)
                )
            except PeerIdInvalid:
                _logger.error(f"Wasn't allow to send message to {v.name}")


@Client.on_message(is_admin & filters.reply & filters.private &
                   filters.command(COMMANDS['block']))
def block(c: Client, m: Message):
    """
    function to block a user from using the bot.

    """
    user = get_id(m)
    if not user:
        return _logger.debug("couldn't find user ID in the message")
    user = get_user(user)
    if user.is_admin:
        return
    admin = get_user(m.from_user.id)
    if str(user.uid) not in data['ban']:
        data['ban'].append(str(user.uid))
        m.reply(format_message('user_block', user, lang=admin.language), quote=True)
        save_data()
    else:
        return m.reply(
            format_message('already_blocked', user, lang=admin.language), quote=True)
    report_to_admins(admin, user, c, 'user_block_admin')


@Client.on_message(is_admin & filters.reply & filters.private &
                   filters.command(COMMANDS['unblock']))
def unblock(c: Client, m: Message):
    """
    unblock users, allow user to use the bot again. this function tell the user
    that he is not blocked.
    """
    user = get_id(m)
    if not user:
        return _logger.debug("couldn't find user ID in the message")
    user = get_user(user)
    if user.is_admin:
        return
    admin = get_user(m.from_user.id)
    if str(user.uid) in data['ban']:
        data['ban'].remove(str(user.uid))
        m.reply(format_message('user_unblock', user, lang=admin.language), quote=True)
        save_data()
        try:
            c.send_message(user.uid, MSG('unban_msg', user.language))
        except UserIsBlocked:
            with db_session:
                delete(u for u in User if u.uid == user.uid)
    else:
        return m.reply(format_message('not_blocked', user, lang=admin.language),
                       quote=True)
    report_to_admins(admin, user, c, 'user_unblock_admin')

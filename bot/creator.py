from bot.helpers import *
from pyrogram import StopPropagation
from main import CREATOR


@Client.on_message(filters.command(COMMANDS['demote'] + COMMANDS['promote']) & filters.chat(CREATOR))
async def set_admins(_, m: Message):
    """
    function to promote / demote admins in the bot. (only for the CREATOR)
    """
    if not m.reply_to_message and len(m.command) == 2:
        uid = m.command[1]
        try:
            if not get_user(int(uid)):
                return
        except ValueError:
            return
    elif not m.reply_to_message:
        return
    else:
        uid = get_id(m)
        if not uid:
            return

    state = True if m.command[0] in COMMANDS['promote'] else False
    with db_session:
        get_user(uid).is_admin = state
    await m.reply(format_message('success_add_admin' if state else 'success_remove_admin',
                  get_user(uid), lang=get_user(m.from_user.id).language
                                 ))
    raise StopPropagation()

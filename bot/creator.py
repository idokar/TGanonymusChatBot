from .helpers import *
from main import CREATOR


@Client.on_message(filters.command(
    MSG['commands']['demote'] + MSG['commands']['promote']) & filters.chat(CREATOR))
def set_admins(_, m):
    if not m.reply_to_message and len(m.command) == 2:
        uid = m.command[1]
    elif not m.reply_to_message:
        return
    else:
        uid = get_id(m)
        if not uid:
            return

    state = True if m.command[0] in MSG['commands']['promote'] else False
    with db_session:
        get_user(uid).is_admin = state
    if state:
        return m.reply(
            format_message(
                MSG[get_user(m.from_user.id).language]['success_add_admin'],
                get_user(uid)
            ))
    return m.reply(format_message(
        MSG[get_user(m.from_user.id).language]['success_remove_admin'],
        get_user(uid)
    ))

from re import sub

from bot.helpers import *
from main import CREATOR


def block_list(lang):
    msg = MSG[lang]['block_list']
    for i in data['ban']:
        user = get_user(int(i))
        msg += format_message('{link} ({uid})\n', user) if user else i
    msg += '~empty~' if not data['ban'] else ''
    return msg


@db_session
def admin_list(lang):
    msg = MSG[lang]['admin_list']
    for admin in get_admins().values():
        if admin.uid == CREATOR:
            msg += format_message('🎖 {link} ({uid})\n', admin)
        else:
            msg += format_message('🥇 {link} ({uid})\n', admin)
    return msg


@Client.on_message(is_admin & filters.private & filters.text &
                   filters.command(MSG['commands']['welcome']))
def start_msg(_, m):
    text = m.text[len(m.command[0]) + 2:]
    text = text.replace('$id', '{uid}').replace('$first_name', "{first}")
    text = text.replace('$last_name', '{last}').replace('$username', '{username}')
    text = text.replace('$user', '{link}').replace('$name', '{name}')
    text = sub(r'~', '~~', sub(r'_', '__', sub(r'-', '--', text)))
    text = sub(r'\\--', '-', sub(r'\\__', '_', sub(r'\*', '**', text)))
    text = sub(r'\\~~', '~', sub(r'\\\*\*', '*', text))
    try:
        m.reply(format_message(text, get_user(m.from_user.id))).delete()
    except RPCError:
        return m.reply(MSG[get_user(m.from_user.id).language]['format_err'])
    data['start_msg'] = text
    save_data()
    m.reply(MSG[get_user(m.from_user.id).language]['success_welcome'], quote=True)


@Client.on_message(filters.command('help') & filters.private)
def info_and_help(c, m):
    pass  # TODO: send help message one for admins and one for users.


@Client.on_message(filters.command(MSG['commands']['settings'])
                   & filters.private & is_admin)
def settings_keyboard(c, m):
    pass  # TODO: settings for admins only


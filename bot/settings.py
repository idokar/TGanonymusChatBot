from re import sub

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from bot.helpers import *
from main import CREATOR

languages = {'en': '🇺🇸 English (אנגלית)', 'he': '🇮🇱 Hebrew (עברית)'}


def block_list(lang):
    msg = MSG[lang]['block_list']
    for i in data['ban']:
        user = get_user(int(i))
        msg += format_message('{link} ({uid})\n', user) if user else i
    msg += '**~empty~**' if not data['ban'] else ''
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


def get_settings_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(MSG[lang]['button_lang'], callback_data='lang')],
        [
            InlineKeyboardButton(MSG[lang]['button_remove_welcome'], callback_data='welcome'),
            InlineKeyboardButton('✅' if data['start_msg'] else '☑️', callback_data='on_welcome'),
        ],
        [InlineKeyboardButton(MSG[lang]['button_block_list'], callback_data='block_list')],
        [InlineKeyboardButton(MSG[lang]['button_admin_list'], callback_data='admin_list')]
    ])


@Client.on_message(is_admin & filters.private & filters.text &
                   filters.command(MSG['commands']['welcome']))
def start_msg(_, m):
    """
    function to set or
    :param _: pyrogram Client, unused argument
    :param m:
    :return:
    """
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


@Client.on_message(filters.command(MSG['commands']['settings']) & is_admin
                   & filters.private)
def settings_keyboard(_, m):
    """
    send
    :param _: pyrogram Client, unused argument
    :param m:
    """
    lang = get_user(m.from_user.id).language
    keyboard = get_settings_keyboard(lang)
    m.reply(MSG[lang]['settings'], reply_markup=keyboard)


@Client.on_callback_query(is_admin)
def refresh_keyboard(_, query: CallbackQuery):
    """
    refreshing the settings keyboard.
    :param _: pyrogram Client, unused argument
    :param query: when the user press the keyboard the query returns to this function.
    :type query: pyrogram.types.CallbackQuery
    :return: None or pyrogram.types.Message
    """
    lang = get_user(query.from_user.id).language
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=MSG[lang]['button_back'], callback_data='back')]])
    if query.data == 'lang':
        for k, v in languages.items():
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=v, callback_data=k)])
        return query.message.edit(MSG[lang]['chang_lang'], reply_markup=keyboard)
    elif query.data == 'welcome':
        return query.answer(MSG[lang]['explain_welcome'], show_alert=True, cache_time=60)
    elif query.data == 'on_welcome':
        if data['start_msg']:
            data['start_msg'] = ''
            save_data()
            query.answer(MSG[lang]['welcome_removed'], show_alert=True)
        return query.message.edit_reply_markup(get_settings_keyboard(lang))
    elif query.data == 'admin_list':
        return query.message.edit(admin_list(lang), reply_markup=keyboard)
    elif query.data == 'block_list':
        return query.message.edit(block_list(lang), reply_markup=keyboard)
    elif query.data in languages.keys():
        with db_session:
            get_user(query.from_user.id).language = query.data
        settings_keyboard(_, query.message)
        return query.message.delete(True)
    elif query.data == 'back':
        return query.message.edit(MSG[lang]['settings'], reply_markup=get_settings_keyboard(lang))
    return


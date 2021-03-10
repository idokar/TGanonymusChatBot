from re import sub

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from bot.helpers import *
from main import CREATOR


def block_list(lang: str) -> str:
    """
    generate the blocked users list.
    :param lang: user language like in the keys of 'languages'
    """
    msg = MSG('block_list', lang)
    for i in data['ban']:
        user = get_user(int(i))
        msg += format_message('{link} ({uid})\n', user) if user else i
    msg += '**~empty~**' if not data['ban'] else ''
    return msg


@db_session
def admin_list(lang: str) -> str:
    """
    generate the admins list.
    :param lang: user language like in the keys of 'languages'
    """
    msg = MSG('admin_list', lang)
    for admin in get_admins().values():
        if admin.uid == CREATOR:
            msg += format_message('🎖 {link} ({uid})\n', admin)
        else:
            msg += format_message('🥇 {link} ({uid})\n', admin)
    return msg


def get_settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    """
    generate the admins settings keyboard.
    :param lang: user language like in the keys of 'languages'
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(MSG('button_lang', lang), callback_data='lang')],
        [
            InlineKeyboardButton(MSG('button_remove_welcome', lang), callback_data='explain_welcome'),
            InlineKeyboardButton('✅' if data['start_msg'] else '☑️', callback_data='on_welcome'),
        ],
        [InlineKeyboardButton(MSG('button_block_list', lang), callback_data='block_list')],
        [InlineKeyboardButton(MSG('button_admin_list', lang), callback_data='admin_list')]
    ])


def get_admin_help_keyboard(lang: str) -> InlineKeyboardMarkup:
    """
    generate the admins help keyboard.
    :param lang: user language like in the keys of 'languages'
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(MSG('button_block', lang), 'block'),
         InlineKeyboardButton(MSG('button_admins', lang), 'admins')],
        [InlineKeyboardButton(MSG('button_welcome', lang), 'welcome'),
         InlineKeyboardButton(MSG('button_group', lang), 'group')]
    ])


@Client.on_message(is_admin & filters.private & filters.text & filters.command(COMMANDS['welcome']))
def start_msg(_, m: Message):
    """
    function to set or update the start message.
    """
    text = m.text[len(m.command[0]) + 2:].replace('{', '{{').replace('}', '}}')
    text = text.replace('$id', '{uid}').replace('$first_name', "{first}")
    text = text.replace('$last_name', '{last}').replace('$username', '{username}')
    text = text.replace('$user', '{link}').replace('$name', '{name}')
    text = sub(r'~', '~~', sub(r'_', '__', sub(r'-', '--', text)))
    text = sub(r'\\--', '-', sub(r'\\__', '_', sub(r'\*', '**', text)))
    text = sub(r'\\~~', '~', sub(r'\\\*\*', '*', text))
    try:
        m.reply(format_message(text, get_user(m.from_user.id))).delete()
    except RPCError:
        return m.reply(MSG('format_err', get_user(m.from_user.id).language))
    data['start_msg'] = text
    save_data()
    m.reply(MSG('success_welcome', get_user(m.from_user.id).language), quote=True)


@Client.on_message(filters.command('help') & filters.private)
def info_and_help(_, m: Message):
    """
    send the start message.
    """
    user = get_user(m.from_user.id)
    lang = user.language
    if user.is_admin:
        return m.reply(MSG('admins_help', lang), disable_web_page_preview=True,
                       reply_markup=get_admin_help_keyboard(lang))
    else:
        return m.reply(
            MSG('users_help', lang), disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(MSG('button_lang', lang), 'help_lang')]]
            ))


@Client.on_message(filters.command(COMMANDS['settings']) & is_admin & filters.private)
def settings_keyboard(_, m: Message):
    """
    send the settings keyboard on a command
    """
    m.reply(MSG('settings_msg', get_user(m.from_user.id).language),
            reply_markup=get_settings_keyboard(get_user(m.from_user.id).language))


@Client.on_callback_query(is_admin)
def refresh_admin_keyboards(_, query: CallbackQuery):
    """
    refreshing the settings and the help keyboards.
    :param _: pyrogram Client, unused argument
    :param query: when the user press the keyboard the query returns to this function.
    :type query: pyrogram.types.CallbackQuery
    """
    lang = get_user(query.from_user.id).language
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=MSG('button_back', lang), callback_data='back')]])
    if query.data == 'lang':
        for k in MSG.locales.keys():
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=MSG(k), callback_data=k)])
        return query.message.edit(MSG('chang_lang', lang), reply_markup=keyboard)
    elif query.data == 'explain_welcome':
        return query.answer(MSG('explain_welcome', lang), show_alert=True, cache_time=60)
    elif query.data == 'on_welcome':
        if data['start_msg']:
            data['start_msg'] = ''
            save_data()
            query.answer(MSG('welcome_removed', lang), show_alert=True)
        return query.message.edit_reply_markup(get_settings_keyboard(lang))
    elif query.data == 'admin_list':
        return query.message.edit(admin_list(lang), reply_markup=keyboard)
    elif query.data == 'block_list':
        return query.message.edit(block_list(lang), reply_markup=keyboard)
    elif query.data == 'back':
        return query.message.edit(MSG('settings_msg', lang), reply_markup=get_settings_keyboard(lang))
    elif query.data in ['block', 'admins', 'welcome', 'group']:
        return query.message.edit(MSG(f'help_{query.data}', lang), disable_web_page_preview=True,
                                  reply_markup=get_admin_help_keyboard(lang))


@Client.on_callback_query(group=1)
def change_lang_keyboard(_, query: CallbackQuery):
    """
    refreshing the the user help keyboard by change the language or the settings.
    :param _: pyrogram Client, unused argument.
    :param query: when the user press the keyboard the query returns to this function.
    :type query: pyrogram.types.CallbackQuery
    """
    if query.data == 'help_lang':
        keyboard = [[InlineKeyboardButton(text=MSG(lang), callback_data=lang)] for lang in MSG.locales.keys()]
        return query.message.edit(
            MSG('chang_lang', get_user(query.from_user.id).language),
            reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data in MSG.locales.keys():
        print(query.data)
        with db_session:
            get_user(query.from_user.id).language = query.data
        if get_user(query.from_user.id).is_admin:
            return query.edit_message_text(
                MSG('settings_msg', query.data),
                reply_markup=get_settings_keyboard(query.data))
        else:
            return query.edit_message_text(
                MSG('users_help', query.data), disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(MSG('button_lang', query.data), 'help_lang')]]
                ))

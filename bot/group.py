import time

from bot.helpers import *


@Client.on_message(is_admin & ~filters.private & filters.command(COMMANDS['group']))
def set_group(_, m: Message):
    """
    handler function to limit the bot to a group.
    only the group members will be allow to use the bot.
    :param m: command message.
    """
    if data['group']:
        return m.chat.leave()
    if m.chat.get_member(m.from_user.id).status in ['creator', 'administrator']:
        me = m.chat.get_member('me')
        if me.can_delete_messages and me.can_restrict_members:
            data['group'] = m.chat.id
            save_data()
            return m.reply(MSG('group_added', get_user(m.from_user.id).language, title=m.chat.title))
        m.reply(MSG('bot_promote', add_user(tg_user=m.from_user).language))
    data['group'] = None
    save_data()
    m.chat.leave()


@Client.on_message((is_admin & ~filters.private & filters.command(COMMANDS['remove_group'])) |
                   filters.left_chat_member)
def unset_group(c, m: Message):
    """
    handler function to unlimite the bot to a group.
    all the users will be allow to use the bot.
    :param c: reference to the Client.
    :param m: command message.
    """
    if not data['group']:
        return
    if m.left_chat_member and m.left_chat_member.is_self:
        data['group'] = None
    elif m.chat.get_member(m.from_user.id).status in ["creator", "administrator"]:
        data['group'] = None
        c.send_message(
            m.from_user.id,
            MSG('group_removed', get_user(m.from_user.id).language, title=m.chat.title))
    save_data()


@Client.on_message(filters.new_chat_members)
def joined_group(_, m: Message):
    """
    check permissions on joining the group. if someone added the bot,
    the bot will check it's permissions immediately and after 5 minutes if necessary.
    :param m: join message.
    """
    if data['group'] and str(m.chat.id) != data['group']:
        m.chat.leave()
    for i in m.new_chat_members:
        if i.is_self:
            me = m.chat.get_member('me')
            if me.status in ["creator", "administrator"]:
                if me.can_delete_messages and me.can_restrict_members:
                    return
            m.reply(MSG('bot_promote', add_user(tg_user=m.from_user).language))
            time.sleep(300)
    me = m.chat.get_member('me')
    if me.status in ["creator", "administrator"]:
        if me.can_delete_messages and me.can_restrict_members:
            return
    data['group'] = None
    save_data()
    m.chat.leave()

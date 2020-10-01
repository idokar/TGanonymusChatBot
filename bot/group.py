import time
from .helpers import *


@Client.on_message(is_admin & ~filters.private & filters.command(MSG['commands']['group']))
def set_group(_, m: Message):
    if data['group']:
        return m.chat.leave()
    m.chat.get_member(m.from_user.id)
    if m.chat.get_member(m.from_user.id).status in ['creator', 'administrator']:
        me = m.chat.get_member('me')
        if me.can_delete_messages and me.can_restrict_members:
            data['group'] = m.chat.id
            save_data()
            return m.reply(MSG[get_user(m.from_user.id).language]['group_added'].format(title=m.chat.title))
        m.reply(MSG[add_user(tg_user=m.from_user).language]['bot_promote'])
    data['group'] = None
    save_data()
    m.chat.leave()


@Client.on_message((is_admin & ~filters.private & filters.command(MSG['commands']['remove_group'])) |
                   filters.left_chat_member)
def unset_group(c, m: Message):
    if not data['group']:
        return
    if m.left_chat_member and m.left_chat_member.is_self:
        data['group'] = None
    elif m.chat.get_member(m.from_user.id).status in ["creator", "administrator"]:
        data['group'] = None
        c.send_message(
            m.from_user.id,
            MSG[get_user(m.from_user.id).language]['group_removed'].format(
                title=m.chat.title))
    save_data()


@Client.on_message(filters.new_chat_members)
def joined_group(_, m: Message):
    if data['group'] and str(m.chat.id) != data['group']:
        m.chat.leave()
    for i in m.new_chat_members:
        if i.is_self:
            me = m.chat.get_member('me')
            if me.status in ["creator", "administrator"]:
                if me.can_delete_messages and me.can_restrict_members:
                    return
            m.reply(MSG[add_user(tg_user=m.from_user).language]['bot_promote'])
            time.sleep(300)
    me = m.chat.get_member('me')
    if me.status in ["creator", "administrator"]:
        if me.can_delete_messages and me.can_restrict_members:
            return
    data['group'] = None
    save_data()
    m.chat.leave()

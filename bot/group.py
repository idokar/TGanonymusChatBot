from pyrogram.enums.chat_member_status import ChatMemberStatus
from bot.helpers import *


@Client.on_message(is_admin & ~filters.private & filters.command(COMMANDS['group']))
def set_group(_, m: Message):
    """
    Handler function to limit the bot to a group.
    Only the group members will be allowed to use the bot.
    :param _: pyrogram Client, unused argument
    :param m: command message.
    """
    if data['group']:
        return m.chat.leave()
    if m.chat.get_member(m.from_user.id).status in [ChatMemberStatus.OWNER,
                                                    ChatMemberStatus.ADMINISTRATOR]:
        privileges = m.chat.get_member('me').privileges
        if privileges and privileges.can_delete_messages and privileges.can_restrict_members:
            data['group'] = m.chat.id
            save_data()
            return m.reply(MSG('group_added', get_user(m.from_user.id).language,
                               title=m.chat.title))
        m.reply(MSG('bot_promote', add_user(tg_user=m.from_user).language))
    data['group'] = None
    save_data()
    m.chat.leave()


@Client.on_message(
    (is_admin & ~filters.private & filters.command(COMMANDS['remove_group'])) |
    filters.left_chat_member)
def unset_group(c, m: Message):
    """
    Handler function to unlimited the bot to a group.
    All the users will be allowed to use the bot.
    :param c: reference to the Client.
    :param m: command message.
    """
    if not data['group']:
        return
    if m.left_chat_member and m.left_chat_member.is_self:
        data['group'] = None
        save_data()
    elif m.chat.get_member(m.from_user.id).status in [ChatMemberStatus.OWNER,
                                                      ChatMemberStatus.ADMINISTRATOR]:
        data['group'] = None
        c.send_message(
            m.from_user.id,
            MSG('group_removed', get_user(m.from_user.id).language,
                title=m.chat.title))
        save_data()


@Client.on_message(filters.new_chat_members)
async def joined_group(_, m: Message):
    """
    Check permissions on joining the group. If someone added the bot, the bot
    will check its permissions immediately and after 5 minutes if necessary.
    :param _: pyrogram Client, unused argument
    :param m: join message.
    """
    if data['group'] and str(m.chat.id) != data['group']:
        await m.chat.leave()
    for i in m.new_chat_members:
        if i.is_self:
            me = await m.chat.get_member('me')
            if me.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]\
                    and me.privileges.can_delete_messages \
                    and me.privileges.can_restrict_members:
                return
            await m.reply(
                MSG('bot_promote', add_user(tg_user=m.from_user).language))
            await asyncio.sleep(300)
            break
    me = await m.chat.get_member('me')
    if me.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        if me.privileges.can_delete_messages and me.privileges.can_restrict_members:
            return
    data['group'] = None
    save_data()
    await m.chat.leave()

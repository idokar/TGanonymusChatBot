import logging

from pyrogram.errors import PeerIdInvalid, UserIsBlocked
from pyrogram.types import InputMediaAnimation, InputMediaAudio, \
    InputMediaDocument, InputMediaVideo, InputMediaPhoto

from bot.helpers import *

_logger = logging.getLogger(__name__)


@db_session
async def forward_to_admins(m: Message, user: User, message, **kwargs):
    """
    function to forward the users messages to the admins.
    :param m: message to forward.
    :param user: the user who send the message.
    :param message: the key of which message to send to the admins.
    :param kwargs: more arguments for the message.
    """
    for k, v in get_admins().items():
        try:
            msg = await m.forward(k)
            if not msg.forward_from or m.sticker:
                await msg.reply(format_message(message, user, lang=v.language, **kwargs),
                                quote=True)
            else:
                if m.edit_date:
                    await msg.reply(MSG("edited", v.language), quote=True)
        except PeerIdInvalid:
            _logger.error(f"Wasn't allow to send message to {v.name}")


async def edit_message(m: Message):
    """
    edit any type of pyrogram message using the messages dict.
    :param m: pyrogram.Message to edit.
    """
    if m.text:
        messages[m.date] = await messages[m.date].edit(m.text)
    elif m.caption and m.caption != messages[m.date].caption:
        messages[m.date] = await messages[m.date].edit_caption(m.caption)
    elif m.media:
        caption = {'caption': m.caption + '\n'} if m.caption else {}
        if m.photo and m.photo != messages[m.date].photo:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaPhoto(m.photo.file_id, m.photo.file_unique_id, **caption))
        elif m.video and m.video != messages[m.date].video:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaVideo(m.video.file_id, m.video.file_unique_id, **caption))
        elif m.document and m.document != messages[m.date].document:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaDocument(m.document.file_id, m.document.file_unique_id, **caption))
        elif m.animation and m.animation != messages[m.date].animation:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaAnimation(m.animation.file_id, m.animation.file_unique_id, **caption))
        elif m.audio and m.audio != messages[m.date].audio:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaAudio(m.audio.file_id, m.audio.file_unique_id, **caption))


@Client.on_message(filters.private & filters.command("start"))
async def start(c, m):
    """
    handler for the `/start` command.
    :param c: reference to the Client.
    :param m: the message.
    """
    user = add_user(tg_user=m.from_user)
    if user.is_admin:
        return await m.reply(format_message('admin_welcome', user, lang=user.language))
    elif await user.member(c):
        if str(user.uid) in data['ban']:
            return await m.reply(MSG('ban_msg', user.language), quote=True)
        if data['start_msg']:
            await m.reply(format_message(data['start_msg'], user).replace('{{', '{').replace('}}', '}'))
        await forward_to_admins(m, user, 'reply')
    else:
        if data['non_participant']:
            return await m.reply(format_message(data['non_participant'], user))


@Client.on_message(filters.private & ~filters.me & ~is_admin &
                   ~filters.create(lambda _, __, m: bool(m.command)), group=1)
async def get_messages(c, m):
    """
    handler for getting messages from the users.
    :param c: reference to the Client.
    :param m: the message.
    """
    user = add_user(m.from_user.id)
    if not await user.member(c):
        return
    if str(user.uid) in data['ban']:
        return await m.reply(MSG('ban_msg', user.language), quote=True)
    elif m.forward_date:
        return await m.reply(MSG('forwarded', user.language))
    await forward_to_admins(m, user, 'edited' if m.edit_date else 'reply')


@Client.on_message(is_admin & filters.private & filters.reply, group=1)
async def return_message(c, m):
    """
    handler for return messages to the users.
    :param c: reference to the Client.
    :param m: the message.
    """
    uid = get_id(m)
    if not uid or get_user(uid).is_admin:
        return _logger.debug("not a valid ID or user is not an admin")
    admin = add_user(tg_user=m.from_user)
    try:
        if m.edit_date:
            await edit_message(m)
        else:
            message = m.copy(uid)
            messages[m.date] = await message
        with db_session:
            for k, v in get_admins().items():
                if k != m.from_user.id:
                    try:
                        await c.send_message(
                            k,
                            format_message('admin_ans',
                                           get_user(uid),
                                           lang=v.language,
                                           admin=admin.link(),
                                           msg=m.text or MSG('pic', v.language),
                                           action='edit his message' if m.edit_date else 'reply'
                                           ))
                    except PeerIdInvalid:
                        _logger.error(f"Wasn't allow to send message to {v.name}")
    except UserIsBlocked:
        m.reply(MSG('blocked', admin.language), quote=True)
        with db_session:
            delete(u for u in User if u.uid == uid)

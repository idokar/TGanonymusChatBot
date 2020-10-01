import logging

from pyrogram.errors import PeerIdInvalid, UserIsBlocked
from pyrogram.types import InputMediaAnimation, InputMediaAudio, \
    InputMediaDocument, InputMediaVideo, InputMediaPhoto

from .helpers import *
_log = logging.getLogger(__name__)

@db_session
async def forward_to_admins(m: Message, user: User, message, **kwargs):
    for k, v in get_admins().items():
        try:
            msg = await m.forward(k)
            if not msg.forward_from or m.sticker:
                await msg.reply(format_message(MSG[v.language][message], user, **kwargs),
                                quote=True)
            else:
                if m.edit_date:
                    await msg.reply(MSG[v.language]["edited"], quote=True)
        except PeerIdInvalid:
            pass


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
                InputMediaPhoto(m.photo.file_id, m.photo.file_ref, **caption))
        elif m.video and m.video != messages[m.date].video:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaVideo(m.video.file_id, m.video.file_ref, **caption))
        elif m.document and m.document != messages[m.date].document:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaDocument(m.document.file_id, m.document.file_ref, **caption))
        elif m.animation and m.animation != messages[m.date].animation:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaAnimation(m.animation.file_id, m.animation.file_ref, **caption))
        elif m.audio and m.audio != messages[m.date].audio:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaAudio(m.audio.file_id, m.audio.file_ref, **caption))


@Client.on_message(filters.private & filters.command("start"))
async def start(c, m):
    user = add_user(tg_user=m.from_user)
    if user.is_admin:
        return await m.reply(format_message(MSG[user.language]['admin_welcome'], user))
    elif await user.member(c):
        if str(user.uid) in data['ban']:
            return await m.reply(MSG[user.language]['ban_msg'], quote=True)
        if data['start_msg']:
            await m.reply(format_message(data['start_msg'], user))
        await forward_to_admins(m, user, 'reply')
    else:
        if data['non_participant']:
            return await m.reply(format_message(data['non_participant'], user))


@Client.on_message(filters.private & ~filters.me & ~is_admin &
                   ~filters.create(lambda _, __, m: bool(m.command)))
async def get_messages(c, m):
    user = add_user(m.from_user.id)
    if not await user.member(c):
        return
    if str(user.uid) in data['ban']:
        return await m.reply(MSG[user.language]['ban_msg'], quote=True)
    elif m.forward_date:
        return await m.reply(MSG[user.language]['forwarded'])
    await forward_to_admins(m, user, 'edited' if m.edit_date else 'reply')


@Client.on_message(is_admin & filters.private & filters.reply, group=1)
async def return_message(c, m):
    uid = get_id(m)
    if not uid or get_user(uid).is_admin:
        return
    admin = add_user(tg_user=m.from_user)
    try:
        if m.edit_date:
            await edit_message(m)
        else:
            message = m.forward(uid, as_copy=True)
            messages[m.date] = await message
        with db_session:
            for k, v in get_admins().items():
                if k != m.from_user.id:
                    try:
                        await c.send_message(
                            k,
                            format_message(MSG[v.language]['admin_ans'],
                                           get_user(uid),
                                           admin=admin.link(),
                                           msg=m.text or MSG[v.language]['pic'],
                                           action='edit his message' if m.edit_date else 'reply'
                                           ))
                    except PeerIdInvalid:
                        pass
    except UserIsBlocked:
        m.reply(MSG[admin.language]['blocked'], quote=True)
        with db_session:
            delete(u for u in User if u.uid == uid)


_log.info(f'load plugin {__name__} successfully')

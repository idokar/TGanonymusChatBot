import time

from pyrogram.errors import PeerIdInvalid, UserIsBlocked, FloodWait,\
    MessageEditTimeExpired, MessageIdInvalid
from pyrogram.types import InputMediaAnimation, InputMediaAudio, \
    InputMediaDocument, InputMediaVideo, InputMediaPhoto

from bot.helpers import *
from main import CREATOR

_logger = logging.getLogger(__name__)


async def forward_to_admins(m: Message, user: User, message):
    """
    Forward the users messages to the admins.
    :param m: message to forward.
    :param user: the user who send the message.
    :param message: the key of which message to send to the admins.
                    ['reply', 'edited']
    """
    for k in get_admins().keys():
        try:
            try:
                msg = await m.forward(k)
            except FloodWait as flood:
                time.sleep(flood.value + 3)
                msg = await m.forward(k)
            with db_session:
                admin = get_user(k)
                if not admin:
                    continue
                admin_lang = admin.language
                admin_name = admin.name
            if not msg.forward_from or m.sticker:
                await msg.reply(format_message(message, user, lang=admin_lang), quote=True)
            else:
                if m.edit_date:
                    await msg.reply(MSG('edited', admin_lang), quote=True)
        except PeerIdInvalid:
            _logger.error(f"Wasn't allow to send message to {admin_name}")
        except UserIsBlocked:
            _logger.error(f'The Admin {admin_name} blocked the bot')
            with db_session:
                if k != CREATOR:
                    delete(u for u in User if u.uid == k)
                    commit()


async def edit_message(m: Message):
    """
    Edit any type of pyrogram message using the messages dict.
    :param m: pyrogram.Message to edit.
    """
    if m.text:
        messages[m.date] = await messages[m.date].edit(m.text, entities=m.entities)
    elif m.caption and m.caption != messages[m.date].caption:
        messages[m.date] = await messages[m.date].edit_caption(
            m.caption, caption_entities=m.caption_entities)
    elif m.media:
        caption = {'caption': m.caption + '\n',
                   'caption_entities': m.caption_entities} if m.caption else {}
        if m.photo and m.photo != messages[m.date].photo:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaPhoto(m.photo.file_id, m.photo.file_unique_id,
                                **caption))
        elif m.video and m.video != messages[m.date].video:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaVideo(m.video.file_id, m.video.file_unique_id, **caption))
        elif m.document and m.document != messages[m.date].document:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaDocument(m.document.file_id, m.document.file_unique_id,
                                   **caption))
        elif m.animation and m.animation != messages[m.date].animation:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaAnimation(m.animation.file_id,
                                    m.animation.file_unique_id, **caption))
        elif m.audio and m.audio != messages[m.date].audio:
            messages[m.date] = await messages[m.date].edit_media(
                InputMediaAudio(m.audio.file_id, m.audio.file_unique_id, **caption))


@Client.on_message(filters.private & filters.command('start'))
async def start(c, m):
    """
    Handler for the `/start` command.
    :param c: reference to the Client.
    :param m: the message.
    """
    user = add_user(tg_user=m.from_user)
    if user.is_admin:
        return await m.reply(
            format_message('admin_welcome', user, lang=user.language))
    elif await user.member(c):
        if str(user.uid) in data['ban']:
            return await m.reply(MSG('ban_msg', user.language), quote=True)
        if data['start_msg']:
            await m.reply(format_message(
                data['start_msg'], user).replace('{{', '{').replace('}}', '}'))
        await forward_to_admins(m, user, 'reply')
    else:
        if data['non_participant']:
            return await m.reply(format_message(data['non_participant'], user))


@Client.on_message(filters.private & ~filters.me & ~is_admin &
                   ~filters.create(lambda _, __, m: bool(m.command)), group=1)
@Client.on_edited_message(filters.private & ~filters.me & ~is_admin &
                          ~filters.create(lambda _, __, m: bool(m.command)), group=1)
async def get_messages(c, m):
    """
    Handler for getting messages from the users.
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
@Client.on_edited_message(is_admin & filters.private & filters.reply, group=1)
async def return_message(c, m):
    """
    Handler for return messages to the users.
    :param c: reference to the Client.
    :param m: the message.
    """
    uid = get_id(m)
    admin = add_user(tg_user=m.from_user)
    if not uid:
        return _logger.debug(f'not a valid ID in the message {m}')
    if get_user(uid) is None:
        return await m.reply(MSG('blocked', admin.language), quote=True)
    elif get_user(uid).is_admin:
        return _logger.debug('user is admin')
    try:
        if m.edit_date:
            await edit_message(m)
        else:
            messages[m.date] = await m.copy(uid)
        with db_session:
            for k, v in get_admins().items():
                if k != m.from_user.id:
                    try:
                        await c.send_message(
                            k,
                            format_message(
                                'admin_edit_ans' if m.edit_date else 'admin_ans',
                                get_user(uid),
                                lang=v.language,
                                admin=admin.name,
                                msg=m.text or MSG('pic', v.language)
                            ))

                    except (PeerIdInvalid, UserIsBlocked):
                        _logger.error(f"Wasn't allow to send message to {v.name}")
    except UserIsBlocked:
        await m.reply(MSG('blocked', admin.language), quote=True)
        with db_session:
            delete(u for u in User if u.uid == uid)
    except (KeyError, MessageEditTimeExpired, MessageIdInvalid):
        await m.reply(MSG('edit_expired', admin.language), quote=True)

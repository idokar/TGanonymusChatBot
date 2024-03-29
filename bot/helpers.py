import asyncio
import json
import logging
import os
import sys
from typing import Union, Dict

from pony.orm import *
from plate import Plate
from pyrogram import filters, Client
from pyrogram.errors import RPCError
from pyrogram.types import Message
from pyrogram.enums.chat_member_status import ChatMemberStatus
from main import DATA_FILE, data

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
__logger = logging.getLogger(__name__)

messages = dict()
DB = Database()
MSG = Plate(f'.{os.sep}Data{os.sep}language')
COMMANDS = {c: [MSG(c, i) for i in MSG.locales.keys()] for c in (
    'block', 'unblock',
    'promote', 'demote',
    'group', 'remove_group',
    'welcome', 'settings'
)}


# ==================================== DB ====================================
class User(DB.Entity):
    """
    User entity type to represent Telegram user
    """
    uid = PrimaryKey(int, size=64)
    is_admin = Required(bool)
    language = Required(str)
    first_name = Optional(str)
    last_name = Optional(str)
    username = Optional(str)

    @property
    def name(self) -> str:
        """
        Full name of a user
        :return: the user first and last name if existed.
        """
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        elif self.first_name and not self.last_name:
            return self.first_name
        return self.last_name or ''

    async def member(self, c: Client) -> bool:
        """
        Check if a user is a group member.
        :param c: reference to the Client.
        :return: rather the user is member or not.
        """
        if data['group'] is None:
            return True
        try:
            user = await c.get_chat_member(data['group'], self.uid)
            return bool(user.status not in [ChatMemberStatus.RESTRICTED,
                                            ChatMemberStatus.LEFT,
                                            ChatMemberStatus.BANNED])
        except RPCError:
            return False

    def link(self) -> str:
        """
        Function to get a link to the user
        :return: Markdown hyperlink to the user
        """
        if self.username:
            return f'[{self.name or self.uid}](https://t.me/{self.username[1:]})'
        return f'[{self.name or self.uid}](tg://user?id={self.uid})'


@db_session
def get_user(user_id: int) -> Union[User, None]:
    """
    Getter function for getting users from the database by user id.
    :param user_id: the user telegram ID.
    :return: the user on None in case the user is not in DB.
    """
    try:
        return User[user_id]
    except ObjectNotFound:
        return __logger.debug(f'the ID {user_id} is not found')


@db_session
def add_user(uid=None, tg_user=None, admin=False, language='en_US',
             first_name='', last_name='', username='') -> User:
    """
    Function to add a new user to the database.
    In case the user is already exist in the DB the user will be returned.

        Required: uid or message
    :param uid: the user telegram ID.
    :type uid: int
    :param tg_user: a Telegram user type as represented in pyrogram.
    :type tg_user: pyrogram.types.User

        Optional arguments:
    :param admin: boolean value if the user is admin
    :param language: the user language. One of: ('en_US', 'he_IL')
    :arg first_name: user first name as string
    :arg last_name: user last name as string
    :arg username: the telegram user username
    :return: a new user, or the user from the DB in case the user already exist.
    """
    if tg_user:
        if not get_user(tg_user.id):
            return User(
                uid=tg_user.id,
                is_admin=admin,
                language=language,
                first_name=tg_user.first_name or '',
                last_name=tg_user.last_name or '',
                username=f'@{tg_user.username}' if tg_user.username else ''
            )
        User[tg_user.id].first_name = tg_user.first_name or ''
        User[tg_user.id].last_name = tg_user.last_name or ''
        User[tg_user.id].username = f'@{tg_user.username}' if tg_user.username else ''

    elif uid and not get_user(uid):
        return User(
            uid=uid,
            is_admin=admin,
            language=language,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
    return User[uid or tg_user.id]


@db_session
def get_admins() -> Dict[int, User]:
    """
    Getter to the admin list.
    :return: dict[(admin ID: dataBase user),...]
    """
    return dict(select((u.uid, u) for u in User if u.is_admin))


def save_data():
    """
    Save the data to json that contains the welcome message, group and blocked
    list.
    """
    with open(f'{DATA_FILE}_data.json', 'w', buffering=1) as file:
        json.dump(data, file, indent=4)
    __logger.info('the data was saved')


def clean_cash(message_date=None):
    """
    Delete all the messages sent from the admins or a specific one.
    :param message_date: the pyrogram.types.Message.date (a none zero number)
    """
    global messages
    if message_date:
        message = messages.pop(message_date)
        if message:
            message.delete(True)
    else:
        del messages
        messages = dict()
        __logger.info('All the messages were clean')


# ============================ pyrogram functions ============================
def format_message(message: str, user: User, **kwargs) -> str:
    """
    Function to format messages.
    The message can contain one (or more) of this tags:
        {uid} (the user ID),
        {first} (the user first name),
        {last} (the user last name),
        {username} (the user telegram username),
        {name} (the full name of the user)
        {link} (link to the user (not always exists))

    :param message: a message to format or key of message if 'lang' in kwargs
    :param user: User as represents in the database
    :param kwargs: more optional arguments to the message
    :return: the formatted message.
    """
    if 'lang' in kwargs.keys():
        return MSG(
            message,
            kwargs.pop('lang'),
            uid=user.uid,
            first=user.first_name or '',
            last=user.last_name or '',
            username=user.username or '',
            name=user.name,
            link=user.link(),
            **kwargs
        )
    return message.format(
        uid=user.uid,
        first=user.first_name or '',
        last=user.last_name or '',
        username=user.username or '',
        name=user.name,
        link=user.link(),
        **kwargs
    )


def get_id(message: Message) -> Union[int, None]:
    """
    Function to cathe the use ID from the given message.
    :return the user ID or None in case of filer.
    """
    if message.reply_to_message.forward_from:
        uid = message.reply_to_message.forward_from.id
    else:
        uid = message.reply_to_message.text.split("\n")[0]
    if isinstance(uid, str) and uid.isdigit():
        uid = int(uid)
    if not isinstance(uid, int):
        message.reply(MSG('user_not_found',
                          add_user(tg_user=message.from_user).language))
        return
    return uid


async def _is_admin(_, __, m: Message) -> bool:
    return bool(m.from_user and m.from_user.id in get_admins().keys())


async def _is_command(_, __, m: Message) -> bool:
    return bool(m.command)

is_admin = filters.create(_is_admin)
"""filter for filtering admins messages."""
is_command = filters.create(_is_command)
"""filter for filtering command messages."""

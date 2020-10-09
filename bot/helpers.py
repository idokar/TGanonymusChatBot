import json
from os import path
import sys
from typing import Union, Dict
from pony.orm import *
from pyrogram import filters, Client
from pyrogram.errors import RPCError
from pyrogram.types import Message
from main import DATA_FILE, data, MSG

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

messages = dict()
DB = Database()


# ==================================== DB ====================================
class User(DB.Entity):
    uid = PrimaryKey(int)
    is_admin = Required(bool)
    language = Required(str)
    first_name = Optional(str)
    last_name = Optional(str)
    username = Optional(str)

    @property
    def name(self) -> str:
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        elif self.first_name and not self.last_name:
            return self.first_name
        return self.last_name or ''

    async def member(self, c: Client) -> bool:
        if data['group'] is None:
            return True
        try:
            user = await c.get_chat_member(data['group'], self.uid)
            return bool(user.status not in ["restricted", "left", "kicked"])
        except RPCError:
            return False

    def link(self) -> str:
        return f'[{self.name if self.name else self.uid}](tg://user?id={self.uid})'


@db_session
def get_user(user_id: int) -> Union[User, None]:
    """
    function to get a user from the data base by user id.
    :param user_id: the user telegram ID.
    :return: the user on None in case the user is not in DB.
    """
    try:
        return User[user_id]
    except ObjectNotFound:
        return


@db_session
def add_user(uid=None, tg_user=None, is_admin=False, language='en',
             first_name='', last_name='', username='') -> User:
    """
    function to add a new user to the data base.
    in case the user already exist in DB the user will be returned.

        Required uid or message
    :param uid: the user telegram ID.
    :type uid: int
    :param tg_user: a telegram user type as represented in pyrogram.
    :type tg_user: pyrogram.User
        Optional arguments:
    :param is_admin: boolean value if the user is admin
    :param language: the user language. one of: ('en', 'he')
    :arg first_name: user first name as string
    :arg last_name: user last name as string
    :arg username: the telegram user username
    :return: a new user or the user from the DB in case the user already exist.
    """
    if tg_user:
        if not get_user(tg_user.id):
            return User(
                uid=tg_user.id,
                is_admin=is_admin,
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
            is_admin=is_admin,
            language=language,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
    return User[uid or tg_user.id]


@db_session
def get_admins() -> Dict[int, User]:
    """
    getter to the admin list.
    :return: dict[(admin ID: dataBase user),...]
    """
    return dict(select((u.uid, u) for u in User if u.is_admin))


def save_data():
    """
    save the dada json that contains the welcome message, group and blocked list.
    """
    with open(f'{DATA_FILE}_data.json', "w", buffering=1) as file:
        json.dump(data, file, indent=4)


def clean_cash(message_date=None):
    """
    function to clear all the messages that sent from the admins or a specific one.
    :param message_date: the pyrogram.Message.date (a non zero number)
    """
    global messages
    if message_date:
        message = messages.pop(message_date)
        if message:
            message.delete(True)
    else:
        del messages
        messages = dict()


# ============================ pyrogram functions ============================
def format_message(message: str, user: User, **kwargs) -> str:
    """
    function to format messages.
    The message can contain one (or more) of this tags:
        {uid} (the user ID),
        {first} (the user first name),
        {last} (the user last name),
        {username} (the user telegram username),
        {link} (a text hidden link to the user),
        {name} (the full name of the user)

    :param message: a message to format
    :param user: User as represents in the data base
    :param kwargs: more optional arguments to the message
    :return: the formatted message.
    """
    return message.format(
        uid=user.uid,
        first=user.first_name or '',
        last=user.last_name or '',
        username=user.username or '',
        link=user.link(),
        name=user.name,
        **kwargs
    )


def get_id(message: Message) -> Union[int, None]:
    """
    function to cathe the use ID from the given message.
    :return the user ID or None in case of filer
    """
    if message.reply_to_message.forward_from:
        uid = message.reply_to_message.forward_from.id
    else:
        uid = message.reply_to_message.text.split("\n")[0]
    if isinstance(uid, str) and uid.isdigit():
        uid = int(uid)
    if not isinstance(uid, int):
        message.reply(MSG[add_user(tg_user=message.from_user).language]['user_not_found'])
        return
    return uid


def _is_admin(_, __, m: Message) -> bool:
    if not m.from_user:
        return False
    return bool(m.from_user.id in get_admins().keys())


is_admin = filters.create(_is_admin)
"""
filter for admin messages
"""

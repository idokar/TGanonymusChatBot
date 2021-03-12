# TGanonymusChatBot

This robot's purpose is to create a chat between an admin or several admins (which could stay anonymous if would like) and users.

## About

The robot can function as a mail box so users from all over the world send messages to the bot and are received in one place,
The users don't have the ability to see other user's messages, although the admin can.
The robot was created using [pyrogram + tgcrypto](https://github.com/pyrogram), [ponyorm](https://github.com/ponyorm), [apscheduler](https://github.com/agronholm/apscheduler) and [plate](https://github.com/delivrance/plate).

### usage examples

* You as a channel admin are able to give people a referral to that chatting bot so people can write messages, complaints or spamming and you can remain anonymous. 
* You can allow people who has been muted or spammed by telegram write and contact you even tho they are muted by telegram (due to spam or some thing).
* You as an admin of a telegram group can tell people of some curtain group to message to you by the robot only, you can also give an order to the robot to receive messages from people from a curtain group so it saves him the time and effort of and moving from chat to another.

### benefits

* People who send you messages through the robot can't erase them so you don't lose any messages that has been sent by someone, but if the admin erases a message he sent then it erases for the user too.
* The admin and the user are able to edit an image, messages, video, GIF, also the admin can edit an image or a message and the user will see the editing too. **(editing can be done up to a day)**. 
* You can nominate people to be admins too. 
* You can block specific user from sending you messages.

## Setup

1. clone the bot
`git clone https://github.com/idokar/TGanonymusChatBot.git`
2. Navigate to the folder
`cd TGanonymusChatBot`
3. Install [requirements.txt](https://github.com/idokar/TGanonymusChatBot/blob/master/requirements.txt)
`pip3 install -U -r requirements.txt`
4. Enter to the [config.ini](https://github.com/idokar/TGanonymusChatBot/blob/master/config.ini) file and edit the empty fields:
    1. Create telegram app here: https://core.telegram.org/api/obtaining_api_id for getting `api_id` and `api_hash`
    2. [Create bot token](https://core.telegram.org/bots#3-how-do-i-create-a-bot) using [BotFather](https://t.me/botfather)
    3. Enter the `api_id`, `api_hash` and the `bot_token` to the file (without using "" around the strings).
    ##### Example
     ```
     api_id = 12345
     api_hash = 0123456789abcdef0123456789abcdef
     bot_token = 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
     ```
5. Enter the creator ID (as int) in [main.py](https://github.com/idokar/TGanonymusChatBot/blob/master/main.py) at line `24`
6. Run the bot.

## Bot commands

* `/start` - **admins and users command**. for admins its a permanent message and for users it is a editable using `/set welcome` command.
* `/help` - **admins and users command**. for users it gives the ability to change language and get info about the bot. and for admins, it gives info about all the commands.  
* `/set welcome` - **admins only command**. allows to set a welcome message for the users.
* `/settings` - **admins only command**. allows to choose language, to remove the welcome message and to see the blocked and admins lists.
* `/block` and `/unblock` - **admins only command**. to block and unlock users.
* `/set group` and `/unset group` - **admins only command**. to limit the incoming messages from a curtain group only.
* `/promote` and `/demote` - **creator only command**. to promote and demote users and admins.

**for more information use `/help` (as admin) in the bot.**

## todo
- [ ]  add bot factory to create instances of this bot.
- [ ]  add admins group (to receive messages there)

import os, logging, asyncio, random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatMemberStatus
from YukkiMusic import app, LOGGER

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - [%(levelname)s] - %(message)s'
)
LOGGER = logging.getLogger(__name__)

spam_chats = []

@app.on_message(filters.command(["all", "tagall"], prefixes="/") & filters.group)
async def mentionall(client, message: Message):
    chat_id = message.chat.id
    
    if message.chat.type == "private":
        return await message.reply("__Perintah ini hanya bisa digunakan di grup dan channel!__")

    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        
        if not is_admin:
            return await message.reply("__Hanya admin yang bisa tagall mek!!__")

        if len(message.command) > 1 and message.reply_to_message:
            return await message.reply("__Kata²nya mana mek!!__")
        elif len(message.command) > 1:
            mode = "text_on_cmd"
            msg = message.text.split(None, 1)[1].strip()
        elif message.reply_to_message:
            mode = "text_on_reply"
            msg = message.reply_to_message
            if msg is None:
                return await message.reply(
                    "__Saya tidak bisa mention member untuk pesan lama! (pesan yang dikirim sebelum saya ditambahkan ke grup)__")
        else:
            return await message.reply("__kalo mau tagall tu kasih kata² atau bales pesan ya njeng!!__")

        if chat_id not in spam_chats:
            spam_chats.append(chat_id)
        
        emoji = [ 
            "👍", "👎", "❤", "🔥", "🥰", "😁", "👏", "🤔", "🤯", "😱", 
            "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", 
            "🥱", "🥴", "😍", "🐳", "🌚", "💯", "🌭", "🤣", "⚡", "🍌", 
            "🏆", "💔", "🤨", "😐", "🍓", "🍾", "😡", "👾", "🤷", "😎", 
            "🙊", "💊", "😘", "🦄", "🙉", "💘", "🆒", "🗿", "🤪", "💅", 
            "☃", "🎄", "🎅", "🤗", "✍", "🤝", "😨", "😇", "🙈", "🎃", 
            "👀", "👻", "🤓", "😭", "😴", "😈", "🖕", "💋",
        ]
        
        usrnum = 0
        usrtxt = ''
        
        members = []
        async for usr in client.get_chat_members(chat_id):
            if not usr.user.is_bot: 
                members.append(usr.user.id)
                
        status_msg = await message.reply(f"__Sedang mentag {len(members)} anggota...__")
        
        for user_id in members:
            if chat_id not in spam_chats:
                break
                
            try:
                usrnum += 1
                em = random.choice(emoji)
                usrtxt += f"[{em}](tg://user?id={user_id}) "
                
                if usrnum == 8:
                    try:
                        if mode == "text_on_cmd":
                            txt = f"<blockquote>{msg}</blockquote>\n\n<blockquote>{usrtxt}</blockquote>\n@Ritolog"
                            await client.send_message(chat_id, txt)
                        elif mode == "text_on_reply":
                            await msg.reply(usrtxt)
                            
                        usrnum = 0
                        usrtxt = ''
                        
                        await asyncio.sleep(0.8)
                    except FloodWait as e:
                        LOGGER.warning(f"Hit FloodWait: {e.value}s")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        LOGGER.error(f"Error kirim pesan: {e}")
                        await asyncio.sleep(0.5)
            except Exception as e:
                LOGGER.error(f"Error memproses pengguna: {e}")
        
        if usrnum > 0:
            try:
                if mode == "text_on_cmd":
                    txt = f"<blockquote>{msg}</blockquote>\n\n<blockquote>{usrtxt}</blockquote>\n@ResahBerkata"
                    await client.send_message(chat_id, txt)
                elif mode == "text_on_reply":
                    await msg.reply(usrtxt)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                LOGGER.error(f"Error mengirim pesan terakhir: {e}")
        
        await status_msg.edit("__Mention selesai.__")
        
    except Exception as e:
        LOGGER.error(f"Error dalam tagall: {e}")
    finally:
        if chat_id in spam_chats:
            spam_chats.remove(chat_id)
          
@app.on_message(filters.command(["cancel"], prefixes="/") & filters.group)
async def cancel_spam(client, message: Message):
    chat_id = message.chat.id
    
    member = await client.get_chat_member(chat_id, message.from_user.id)
    is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    
    if not is_admin:
        return await message.reply("__Admin doang yang bisa cancel ya babi!__")
    
    if chat_id not in spam_chats:
        return await message.reply("__Ga ada tagall ngapain cansel asu!...__")
    else:
        try:
            spam_chats.remove(chat_id)
        except:
            pass
        return await message.reply("__Oke aku diem.__")

def load():
    LOGGER(__name__).info("Modul TagAll berhasil dimuat")
    
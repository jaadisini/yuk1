from YukkiMusic import app
import asyncio
import os
import re


from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, MessageDeleteForbidden
from pyrogram.types import ChatPermissions
from pyrogram import filters, enums
from pyrogram.enums import ChatType
from pyrogram.types import Message, User
from pyrogram.enums import MessageEntityType
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong

from YukkiMusic.core.mongo import mongodb  # Assuming this is a class that needs to be instantiated
from YukkiMusic.utils.database import add_served_chat
from pyrogram.enums import ChatMemberStatus
from config import MONGO_DB_URI

from motor.motor_asyncio import AsyncIOMotorClient  # Import the correct class

# Instantiate the MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)  # Ensure MongoCli is correctly instantiated
db = mongo_client["DOR"]
user_collection = db["user_dia"]
gc = db["listgrup"]
psnz = db["msg_text"]
whitelist = db["white_dia"]

async def get_user_ids(client_id):
    user_ids = await user_collection.find_one({"_id": client_id})
    return user_ids["user_dia"] if user_ids else []

async def get_white_ids(client_id):
    white_ids = await whitelist.find_one({"_id": client_id})
    return white_ids["white_dia"] if white_ids else []


async def get_blacklist_status(client_id):
    blacklist_status = await db.settings.find_one({"_id": client_id})
    return blacklist_status["status"] if blacklist_status else False

async def set_blacklist_status(client_id, status):
    await db.settings.update_one({"_id": client_id}, {"$set": {"status": status}}, upsert=True)

async def get_chat_ids(client_id):
    chat_ids = await gc.find_one({"_id": client_id})
    return chat_ids["grup"] if chat_ids else []

async def get_msg_ids(client_id):
    msg_ids = await psnz.find_one({"_id": client_id})
    return msg_ids["msg_text"] if msg_ids else []

async def purge(message):
    await asyncio.sleep(0.5)
    await message.delete()

def get_message(message):
    msg = (
        message.reply_to_message
        if message.reply_to_message
        else "" if len(message.command) < 2 else " ".join(message.command[1:])
    )
    return msg

    

def emoji(alias):
    emojis = {
        "bintang": "<emoji id=5931592939514892319>⭐</emoji>",
        "loading": "<emoji id=5801044672658805468>✨</emoji>",
        "proses": "<emoji id=6276248783525251352>🔄</emoji>",
        "gagal": "<emoji id=6278161560095426411>❌</emoji>",
        "done": "<emoji id=5852871561983299073>✅</emoji>",
        "upload": "<emoji id=5911100572508885928>♻️</emoji>",
        "roses": "<emoji id=5341312820698948923>🙃</emoji>",
        "selesai": "<emoji id=5341576484446283436>😎</emoji>",
        "on": "<emoji id=6275808772715710450>🎚️</emoji>",
        "off": "<emoji id=6276295366740543459>⛔</emoji>",
        "daftar": "<emoji id=5974045315391556490>📝</emoji>",
    }
    return emojis.get(alias, "Emoji tidak ditemukan.")

Q = emoji("bintang")
gagal = emoji("gagal")
prs = emoji("proses")
batal = emoji("gagal")
rs = emoji("roses")
sls = emoji("selesai")
dn = emoji("done")
on = emoji("on")
off = emoji("off")
dftr = emoji("daftar")


async def isGcast(filter, client, update):
    bl = "€¥£¢𝑎𝑏𝑐𝑑𝑒𝑓𝑔𝒉𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ×̰͓̰̈́̈́̈́̈́ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿 🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿 ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘϙʀᴛᴜᴠᴡʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘϙʀᴛᴜᴠᴡʏᴢᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘϙʀᴛᴜᴠᴡʏᴢᗩᗷᑕᗞᗴᖴᏀᕼᏆᒍᏦしᗰᑎᝪᑭᑫᖇᔑᎢᑌᐯᗯ᙭ᎩᏃᗩᗷᑕᗞᗴᖴᏀᕼᏆᒍᏦしᗰᑎᝪᑭᑫᖇᔑᎢᑌᐯᗯ᙭ᎩᏃᎪᏴᏟᎠᎬҒᏀᎻᏆᎫᏦᏞᎷΝϴᏢϘᎡՏͲႮᏙᏔХᎽᏃᎪᏴᏟᎠᎬҒᏀᎻᏆᎫᏦᏞᎷΝϴᏢϘᎡՏͲႮᏙᏔХᎽᏃａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁"
    awoos = update.text
    x = awoos.lower()
    xx = await get_msg_ids(client.me.id)
        
    with open('bl.txt', 'r') as file:
        blc = [w.lower().strip() for w in file.readlines()]
        for chara in bl:
            blc.append(chara)

    for chara in blc:
        if chara in x:
            return True
        
    if x in xx:
        return True
    
    kont = update.from_user.id
    meki = await get_user_ids(client.me.id)

    if kont in meki:
        return True
        
    return False

Gcast = filters.create(isGcast)

@app.on_message(filters.command("duar") & ~filters.private)
async def add_user_to_blacklist(c, m):
    if len(m.command) != 2 and not m.reply_to_message:
        await m.reply_text(
            f"{batal}**gunakan format** : `duar` **user id atau balas ke pesan untuk menambahkan ke daftar antigcast {Q}**",
            quote=True,
        )
        return

    if m.reply_to_message:
        user_id = m.reply_to_message.from_user.id
    else:
        try:
            user_id = int(m.command[1])
        except ValueError:
            try:
                user = await c.get_users(m.command[1])
                user_id = user.id
            except Exception:
                await m.reply_text(f"{gagal} Tidak dapat menemukan pengguna dengan username {m.command[1]}", quote=True)
                return

    user_ids = await get_user_ids(c.me.id)
    if user_id not in user_ids:
        user_ids.append(user_id)
        await user_collection.update_one({"_id": c.me.id}, {"$set": {"user_dia": user_ids}}, upsert=True)
        await m.reply_text(f"{Q}**user dengan id** `{user_id}` **telah ditambahkan ke daftar antigcast** {dn}", quote=True)
    else:
        await m.reply_text(f"{dn}**user tersebut sudah ada dalam daftar antigcast {Q}**", quote=True)
    
@app.on_message(filters.command("listduar") & ~filters.private)
async def display_blacklist(client, message):
    user_ids = await get_user_ids(client.me.id)
    await message.reply_text(f"{dftr} ini hasilnya : `{user_ids}`\n", quote=True)

@app.on_message(filters.command("unduar") & ~filters.private)
async def remove_user_from_blacklist(c, m):
    if len(m.command) != 2 and not m.reply_to_message:
        await m.reply_text(
            f"{batal}**gunakan format** : `unduar` **user id atau balas ke pesan untuk menghapus dari daftar antigcast {Q}**",
            quote=True,
        )
        return

    if m.reply_to_message:
        user_id = m.reply_to_message.from_user.id
    else:
        user_id = int(m.command[1])

    user_ids = await get_user_ids(c.me.id)
    if user_id in user_ids:
        user_ids.remove(user_id)
        await user_collection.update_one({"_id": c.me.id}, {"$set": {"user_dia": user_ids}}, upsert=True)
        await m.reply_text(f"{Q}**user dengan id** `{user_id}` **telah dihapus dalam daftar antigcast** {dn}", quote=True)
    else:
        await m.reply_text(f"{Q}**user tersebut tidak ada dalam daftar antigcast {gagal}**", quote=True)

@app.on_message(filters.command("liat") & ~filters.private)
async def checkstatus(client, message):
    cek = await get_blacklist_status(client.me.id)
    if cek:
        await message.reply_text(f"{Q}**anda sudah mengaktifkan antigcast**{dn}", quote=True)
    else:
        await message.reply_text(f"{Q}**anda belum mengaktifkan antigcast**{gagal}", quote=True)

@app.on_message(filters.command("on") & ~filters.private)
async def enable_blacklist(c, m):
    await set_blacklist_status(c.me.id, True)
    x = await m.reply_text(f"{Q}**antigcast user berhasil di aktifkan** {on}", quote=True)
    await asyncio.sleep(0.5)
    await x.delete()

@app.on_message(filters.command("off") & ~filters.private)
async def disable_blacklist(c, m):
    await set_blacklist_status(c.me.id, False)
    x = await m.reply_text(f"{Q}**antigcast user berhasil di matikan** {off}", quote=True)
    await asyncio.sleep(0.5)
    await x.delete()
@app.on_message(filters.command("addgc") & ~filters.private)
async def add_group_to_antigcast(c, m):
    type = (ChatType.GROUP, ChatType.SUPERGROUP)

    if m.chat.type not in type:
        await m.reply_text(f"{gagal}gunakan fitur ini di grup!")
        return

    user_id = m.chat.id
    chat_ids = await get_chat_ids(c.me.id)
    if user_id not in chat_ids:
        chat_ids.append(user_id)
        await gc.update_one({"_id": c.me.id}, {"$set": {"grup": chat_ids}}, upsert=True)
        await m.reply_text(f"{Q}**grup dengan id** `{user_id}` **telah ditambahkan ke daftar antigcast** {dn}", quote=True)
    else:
        await m.reply_text(f"{dn}**grup tersebut sudah ada dalam daftar antigcast {Q}**", quote=True)

@app.on_message(filters.command("hapusgc") & ~filters.private)
async def remove_group_from_antigcast(c, m):
    type = (ChatType.GROUP, ChatType.SUPERGROUP)
    if m.chat.type not in type:
        await m.reply_text(f"{gagal} Gunakan fitur ini di grup atau berikan ID grup", quote=True)
        return

    chat_id = None
    if len(m.command) >= 2:
        try:
            chat_id = int(m.command[1])
        except ValueError:
            await m.reply_text(f"{gagal} ID grup tidak valid", quote=True)
            return

    if not chat_id:
        chat_id = m.chat.id

    chat_ids = await get_chat_ids(c.me.id)
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        await gc.update_one({"_id": c.me.id}, {"$set": {"grup": chat_ids}}, upsert=True)
        await m.reply_text(f"{Q} Grup dengan ID {chat_id} telah dihapus dari daftar antigcast {dn}", quote=True)
    else:
        await m.reply_text(f"{Q} Grup dengan ID {chat_id} tidak ada dalam daftar antigcast {gagal}", quote=True)

@app.on_message(filters.command("listgc") & ~filters.private)
async def display_antigcast(c, m):
    user_ids = await get_chat_ids(c.me.id)
    await m.reply_text(f"{dftr}**daftar grup antigcast** : `{user_ids}` \n", quote=True)

@app.on_message(filters.command("bl") & ~filters.private)
async def add_pesan(c, m):
    _rply = m.reply_to_message
    if not _rply:
        await m.reply(f"mohon balas ke pengguna")
        return
    user_text = _rply.text
    msg_ids = await get_msg_ids(c.me.id)
    if user_text not in msg_ids:
        msg_ids.append(user_text)
        await psnz.update_one({"_id": c.me.id}, {"$set": {"msg_text": msg_ids}}, upsert=True)
        sukses = await m.reply_text(f"<blockquote><b>{user_text} berhasil di tambahkan ke database{dn}</b></blockquote>", quote=True)
        await _rply.delete()
        await purge(m)
        await sukses.delete()
    else:
        x = await m.reply_text(f"pesan sudah ada di dalam database{gagal}", quote=True)
        await asyncio.sleep(0.5)
        await x.delete()

@app.on_message(filters.command("cekbl") & ~filters.private)
async def strdb(client, message):
    pesan = await get_msg_ids(client.me.id)
    try:
        await message.reply_text(pesan)
    except MessageTooLong:
        with open("db.txt", "a", encoding="utf-8") as file:
            file.write(f"{pesan}\n")
        kirim = await message.reply_document(db.txt)
        if kirim:
            os.remove("db.txt")

@app.on_message(filters.command("unbl") & ~filters.private)
async def remove_kata_from_blacklist(c, m):
    if len(m.command) != 2 and not m.reply_to_message:
        await m.reply_text(
            f"{batal}**gunakan format** : `rmkat` **user id atau balas ke pesan untuk menghapus dari daftar antigcast {Q}**",
            quote=True,
        )
        return

    if m.reply_to_message:
        user_id = m.reply_to_message.text
    else:
        user_id = " ".join(m.command[1:])

    user_ids = await get_msg_ids(c.me.id)
    if user_id in user_ids:
        user_ids.remove(user_id)
        await psnz.update_one({"_id": c.me.id}, {"$set": {"msg_text": user_ids}}, upsert=True)
        await m.reply_text(f"{Q}**berhasil menghapus** `{user_id}` **dari daftar kata antigcast** {dn}", quote=True)
    else:
        await m.reply_text(f"{Q}**kata tersebut tidak ada dalam daftar antigcast {gagal}**", quote=True)


@app.on_message(filters.command("wl") & ~filters.private)
async def add_user_to_whitelist(c, m):
    if len(m.command) != 2 and not m.reply_to_message:
        await m.reply_text(
            f"{batal}**gunakan format** : `wl` **user id atau balas ke pesan untuk menambahkan ke whitelist antigcast {Q}**",
            quote=True,
        )
        return

    if m.reply_to_message:
        user_id = m.reply_to_message.from_user.id
    else:
        try:
            user_id = int(m.command[1])
        except ValueError:
            try:
                user = await c.get_users(m.command[1])
                user_id = user.id
            except Exception:
                await m.reply_text(f"{gagal} Tidak dapat menemukan pengguna dengan username {m.command[1]}", quote=True)
                return

    user_ids = await get_white_ids(c.me.id)
    if user_id not in user_ids:
        user_ids.append(user_id)
        await whitelist.update_one({"_id": c.me.id}, {"$set": {"white_dia": white_dia}}, upsert=True)
        await m.reply_text(f"{Q}**user dengan id** `{user_id}` **telah ditambahkan ke whitelist antigcast** {dn}", quote=True)
    else:
        await m.reply_text(f"{dn}**user tersebut sudah ada dalam whitelist antigcast {Q}**", quote=True)

@app.on_message(filters.command("listwl") & ~filters.private)
async def display_whitelist(client, message):
    user_ids = await get_white_ids(client.me.id)
    await message.reply_text(f"{dftr} ini hasilnya : `{user_ids}`\n", quote=True)

@app.on_message(filters.command("unwl") & ~filters.private)
async def remove_user_from_whitelist(c, m):
    if len(m.command) != 2 and not m.reply_to_message:
        await m.reply_text(
            f"{batal}**gunakan format** : `unwl` **user id atau balas ke pesan untuk menghapus dari daftar antigcast {Q}**",
            quote=True,
        )
        return

    if m.reply_to_message:
        user_id = m.reply_to_message.from_user.id
    else:
        user_id = int(m.command[1])

    user_ids = await get_white_ids(c.me.id)
    if user_id in user_ids:
        user_ids.remove(user_id)
        await whitelist.update_one({"_id": c.me.id}, {"$set": {"white_dia": white_dia}}, upsert=True)
        await m.reply_text(f"{Q}**user dengan id** `{user_id}` **telah dihapus dalam whitelist antigcast** {dn}", quote=True)
    else:
        await m.reply_text(f"{Q}**user tersebut tidak ada dalam whitelist antigcast {gagal}**", quote=True)

# Assuming other imports and client initialization as before

async def is_admin(client, chat_id, user_id):
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

@app.on_message(filters.text & ~filters.private & Gcast)
async def delete_messages(client, message):
    try:
        
        blacklist_status = await get_blacklist_status(client.me.id)
        if not blacklist_status:
            return
        
        if await is_admin(client, message.chat.id, message.from_user.id):
            return

        if await get_white_ids(client.me.id):
            return
        await message.delete()
        xxx = await message.reply(f"<blockquote><b> pesan lu jelek gua apus</b></blockquote>")
        await asyncio.sleep(5)
        await xxx.delete()
        
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await message.delete()
    except MessageDeleteForbidden:
        pass
        
__MODULE__ = "ᴀɴᴛɪɢᴄᴀꜱᴛ"
__HELP__ = """
ɪɴꜰᴏ ᴄᴏᴍᴍᴀɴᴅꜱ:

✱ /on : ᴜɴᴛᴜᴋ ᴍᴇɴɢʜɪᴅᴜᴘᴋᴀɴ ᴀɴᴛɪɢᴄᴀꜱᴛ ᴅɪ ɢʀᴏᴜᴘ
✱ /off : ᴜɴᴛᴜᴋ ᴍᴇɴᴏɴᴀᴋᴛɪꜰᴋᴀɴ ᴀɴᴛɪɢᴄᴀꜱᴛ ᴅɪ ɢʀᴏᴜᴘ
✱ /ᴡʟ : ᴜɴᴛᴜᴋ ᴍᴇɴᴀᴍʙᴀʜᴋᴀɴ ᴜsᴇʀ ᴋᴇ ᴡʜɪᴛᴇʟɪsᴛ 
✱ /ᴜɴᴡʟ : ᴜɴᴛᴜᴋ ᴍᴇɴɢʜᴀᴘᴜs ᴜsᴇʀ ᴅᴀʀɪ ᴅᴀғᴛᴀʀ ᴡʜɪᴛᴇʟɪsᴛ
✱ /liat : ᴜɴᴛᴜᴋ ᴍᴇʟɪʜᴀᴛ ᴀᴘᴀᴋᴀʜ ᴀɴᴛɪɢᴄᴀꜱᴛ ᴛᴇʟᴀʜ ᴅɪ ᴀᴋᴛɪꜰᴋᴀɴ
✱ /bl : ᴜɴᴛᴜᴋ ᴍᴇɴᴀᴍʙᴀʜᴋᴀɴ ᴋᴀᴛᴀ-ᴋᴀᴛᴀ / ᴛʀɪɢɢᴇʀ ʙʟᴀᴄᴋʟɪꜱᴛ ᴅɪ ɢʀᴏᴜᴘ ᴄʜᴀᴛ.
✱ /unbl : ᴜɴᴛᴜᴋ ᴍᴇɴɢʜᴀᴘᴜꜱ ᴋᴀᴛᴀ-ᴋᴀᴛᴀ / ᴛʀɪɢɢᴇʀ ʙʟᴀᴄᴋʟɪꜱᴛ ᴅɪ ɢʀᴏᴜᴘ ᴄʜᴀᴛ.
✱ /cekbl : ᴜɴᴛᴜᴋ ᴍᴇɴɢᴇᴄᴇᴋ ᴅᴀꜰᴛᴀʀ ᴋᴀᴛᴀ ʏɢ ᴅɪ ʙʟᴀᴄᴋʟɪꜱᴛ
✱ /duar :  ᴜɴᴛᴜᴋ ᴍᴇɴᴀᴍʙᴀʜᴋᴀɴ ɪᴅᴜꜱᴇʀ ᴋᴇᴅᴀʟᴀᴍ ᴅᴀᴛᴀʙᴀꜱᴇ ᴀɢᴀʀ ꜱᴇᴍᴜᴀ ᴘᴇꜱᴀɴ ᴅᴀʀɪ ɪᴅᴜꜱᴇʀ ᴛᴇʀꜱᴇʙᴜᴛ ᴀᴋᴀɴ ᴅɪ ʜᴀᴘᴜꜱ.
✱ /unduar : ᴜɴᴛᴜᴋ ᴍᴇɴɢʜᴀᴘᴜꜱ ɪᴅᴜꜱᴇʀ ᴋᴇᴅᴀʟᴀᴍ ᴅᴀᴛᴀʙᴀꜱᴇ ᴀɢᴀʀ ꜱᴇᴍᴜᴀ ᴘᴇꜱᴀɴ ᴅᴀʀɪ ɪᴅᴜꜱᴇʀ ᴛᴇʀꜱᴇʙᴜᴛ ᴀᴋᴀɴ ᴅɪ ʜᴀᴘᴜꜱ.
✱ /listduar : ʟɪʜᴀᴛ ᴋᴀᴛᴀ-ᴋᴀᴛᴀ ʏᴀɴɢ ᴍᴀꜱᴜᴋ ᴅᴀꜰᴛᴀʀ ʜɪᴛᴀᴍ ꜱᴀᴀᴛ ɪɴɪ.'''
"""

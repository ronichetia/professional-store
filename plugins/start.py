from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
from config import Config
from database import db
import asyncio
import pyromod # Used for asking user input dynamically
import re
import json # 👈 New import for loading batch json

# ==================== TIME PARSER HELPER ====================
def parse_time(time_str):
    time_str = str(time_str).strip().lower()
    if time_str == "0" or time_str == "off": 
        return 0
    try:
        if time_str.endswith('s'): return int(time_str[:-1])
        if time_str.endswith('m'): return int(time_str[:-1]) * 60
        if time_str.endswith('h'): return int(time_str[:-1]) * 3600
        if time_str.endswith('d'): return int(time_str[:-1]) * 86400
        return int(time_str) # Default seconds if no letter provided
    except ValueError:
        return None

# ==================== BACKGROUND TASK ====================
# 👈 Helper Task for DM Auto Delete
async def delete_messages_later(client, chat_id, message_ids, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id=chat_id, message_ids=message_ids)
    except Exception as e:
        pass


# ==================== HELPER FUNCTIONS ====================
# Start Menu Generator 
async def get_start_menu(user_name, is_admin):
    settings = await db.get_settings()
    custom_msg = settings.get("welcome_msg", "default")
    
    if custom_msg == "default" or not custom_msg:
        text = (
            f"> 👋 **ʜᴇʏ {user_name}! ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʙᴏᴛ**\n\n"
            "ɪ ᴡɪʟʟ ʜᴇʟᴘ ʏᴏᴜ ᴘʀᴏᴠɪᴅᴇ ᴀɴɪᴍᴇ ᴠɪᴅᴇᴏs ᴀɴᴅ ʟɪɴᴋs.\n"
            "ᴇxᴘʟᴏʀᴇ ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ:"
        )
    else:
        text = custom_msg.replace("{user}", user_name)
    
    buttons = []
    if is_admin:
        buttons.append([InlineKeyboardButton("👮 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ 👮", callback_data="open_admin")])
        
    buttons.append([
        InlineKeyboardButton("❓ ʜᴇʟᴘ", callback_data="user_help"),
        InlineKeyboardButton("ℹ️ ᴀʙᴏᴜᴛ", callback_data="user_about")
    ])
    
    return text, InlineKeyboardMarkup(buttons)

# About Menu Generator
async def get_about_menu(client):
    bot_info = await client.get_me()
    bot_name = bot_info.first_name
    
    text = (
        "> ℹ️ **ʙᴏᴛ ɪɴꜰᴏ & ᴀʙᴏᴜᴛ**\n\n"
        f"🤖 **ꜱᴜᴘᴘᴏʀᴛ:** [tg founder](https://t.me/telegram)\n"
        "» **ᴊᴏɪɴ ᴜꜱ:** [KdramaTalkies](https://t.me/kdramatalkies)\n"
        "» **ᴅᴇᴠᴇʟᴏᴘᴇʀ:** [hellogram](https://t.me/telegram)"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_start"),
         InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close_panel")]
    ])
    return text, buttons

# Admin Menu Generator
async def get_admin_menu():
    text = "> 👮 **ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ**\n\nᴍᴀɴᴀɢᴇ ᴀʟʟ ʙᴏᴛ sᴇᴛᴛɪɴɢs ꜰʀᴏᴍ ʜᴇʀᴇ."
    
    btn_list = [
        [InlineKeyboardButton("📊 ʙᴏᴛ sᴛᴀᴛs", callback_data="admin_stats"),
         InlineKeyboardButton("📢 ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📺 ᴍᴀɴᴀɢᴇ ꜰ-sᴜʙ", callback_data="manage_fsub"),
         InlineKeyboardButton("📁 ᴍᴀɴᴀɢᴇ ᴄʜᴀɴɴᴇʟs", callback_data="manage_channels")],
        [InlineKeyboardButton("⚙️ ꜰ-sᴜʙ sᴇᴛᴛɪɴɢs", callback_data="admin_fsub"),
         InlineKeyboardButton("⏳ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ", callback_data="admin_autodel")],
        [InlineKeyboardButton("📝 ᴡᴇʟᴄᴏᴍᴇ ᴍsɢ", callback_data="admin_welcome"),
         InlineKeyboardButton("🔗 ᴘᴏsᴛ ʙᴜᴛᴛᴏɴs", callback_data="admin_post_btns")],
        [InlineKeyboardButton("📮 ᴘᴏsᴛ ᴍᴏᴅᴇ", callback_data="admin_post_mode")], 
        [InlineKeyboardButton("👥 ᴍᴀɴᴀɢᴇ ᴀᴅᴍɪɴs", callback_data="admin_manage"),
         InlineKeyboardButton("🎥 ʜᴇʟᴘ ᴠɪᴅᴇᴏ", callback_data="edit_help_video")],
        [InlineKeyboardButton("📝 ʜᴇʟᴘ ᴛᴇxᴛ", callback_data="edit_help_text"),
         InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_start")],
        [InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close_panel")]
    ]
    return text, InlineKeyboardMarkup(btn_list)

# F-Sub Menu (UPDATED with Custom Text Edit button)
async def render_fsub_menu(query):
    settings = await db.get_settings()
    fsub_on = settings.get("fsub", False)
    fsub_text = "✅ ꜰ-sᴜʙ: ᴏɴ" if fsub_on else "❌ ꜰ-sᴜʙ: ᴏꜰꜰ"
    
    text = "> ⚙️ **ꜰᴏʀᴄᴇ-sᴜʙ sᴇᴛᴛɪɴɢs**\n\nᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ-sᴜʙ ᴏɴ ᴏʀ ᴏꜰꜰ ꜰʀᴏᴍ ʜᴇʀᴇ, ᴀɴᴅ ᴇᴅɪᴛ ᴛʜᴇ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ ᴍᴇssᴀɢᴇ:"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(fsub_text, callback_data="toggle_fsub")],
        [InlineKeyboardButton("📝 ᴇᴅɪᴛ ꜰ-sᴜʙ ᴛᴇxᴛ", callback_data="edit_fsub_text")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")] 
    ])
    
    try:
        await query.message.edit_text(text, reply_markup=buttons)
    except MessageNotModified:
        pass

# Post Mode Menu
async def render_post_mode_menu(query):
    settings = await db.get_settings()
    mode = settings.get("post_mode", "Link") 
    
    text = "> 📮 **ᴘᴏsᴛ ᴍᴏᴅᴇ sᴇᴛᴛɪɴɢs**\n\nᴄʜᴏᴏsᴇ ʜᴏᴡ ᴛʜᴇ ʙᴏᴛ sʜᴏᴜʟᴅ sᴇɴᴅ ᴘᴏsᴛs ɪɴ ᴄʜᴀɴɴᴇʟs:\n\n• **ʟɪɴᴋ:** sᴇɴᴅs ᴀ ᴅᴇᴇᴘʟɪɴᴋ ʙᴜᴛᴛᴏɴ.\n• **ꜰᴏʀᴡᴀʀᴅ:** ꜰᴏʀᴡᴀʀᴅs ᴛʜᴇ ᴍᴇssᴀɢᴇ.\n• **ᴄᴏᴘʏ:** sᴇɴᴅs ᴀs ᴀ ᴄᴏᴘʏ (ɴᴏ ꜰᴏʀᴡᴀʀᴅ ᴛᴀɢ)."
    
    btn_link = "✅ ʟɪɴᴋ" if mode == "Link" else "ʟɪɴᴋ"
    btn_fwd = "✅ ꜰᴏʀᴡᴀʀᴅ" if mode == "Forward" else "ꜰᴏʀᴡᴀʀᴅ"
    btn_copy = "✅ ᴄᴏᴘʏ" if mode == "Copy" else "ᴄᴏᴘʏ"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_link, callback_data="set_pm_Link"),
         InlineKeyboardButton(btn_fwd, callback_data="set_pm_Forward"),
         InlineKeyboardButton(btn_copy, callback_data="set_pm_Copy")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")]
    ])
    try:
        await query.message.edit_text(text, reply_markup=buttons)
    except MessageNotModified:
        pass

# Auto-Delete Menu
async def render_autodel_menu(query):
    settings = await db.get_settings()
    dm_autodel = settings.get("auto_delete", 600)
    post_autodel = settings.get("post_auto_delete", 0)
    
    dm_text = f"✅ ᴅᴍ ({dm_autodel}s)" if dm_autodel > 0 else "❌ ᴅᴍ (ᴏꜰꜰ)"
    post_text = f"✅ ᴘᴏsᴛ ({post_autodel}s)" if post_autodel > 0 else "❌ ᴘᴏsᴛ (ᴏꜰꜰ)"

    text = "> ⏳ **ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ sᴇᴛᴛɪɴɢs**\n\nᴍᴀɴᴀɢᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀs ꜰᴏʀ ᴅᴍs (ʙᴏᴛ) ᴀɴᴅ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛs:"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(dm_text, callback_data="toggle_dm_autodel"),
         InlineKeyboardButton(post_text, callback_data="toggle_post_autodel")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")] 
    ])
    try:
        await query.message.edit_text(text, reply_markup=buttons)
    except MessageNotModified:
        pass


# ==================== 1. START / WELCOME COMMAND ====================
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if hasattr(db, "add_user"):
        await db.add_user(message.from_user.id)

    is_admin = message.from_user.id in Config.ADMINS

    # ====== NEW F-SUB VERIFICATION SYSTEM ======
    settings = await db.get_settings()
    fsub_on = settings.get("fsub", False)
    fsub_channels = settings.get("fsub_channels", [])
    fsub_bots = settings.get("fsub_bots", [])
    
    if fsub_on and (fsub_channels or fsub_bots) and not is_admin:
        is_joined = True
        
        for ch in fsub_channels:
            try:
                member = await client.get_chat_member(ch["id"], message.from_user.id)
                if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                    is_joined = False
                    break
            except Exception:
                is_joined = False
                break
                
        if not is_joined:
            btn_list = []
            all_fsub_btns = []
            
            # Combine both channels and bots into a single list
            for ch in fsub_channels:
                all_fsub_btns.append(InlineKeyboardButton(f"{ch['name']}", url=ch['url']))
            for bt in fsub_bots:
                all_fsub_btns.append(InlineKeyboardButton(f"{bt['name']}", url=bt['url']))
                
            # Chunking buttons 2 per row
            for i in range(0, len(all_fsub_btns), 2):
                btn_list.append(all_fsub_btns[i:i+2])

            bot_username = (await client.get_me()).username
            if len(message.command) > 1:
                retry_url = f"https://t.me/{bot_username}?start={message.command[1]}"
                btn_list.append([InlineKeyboardButton("✅ ᴛʀʏ ᴀɢᴀɪɴ", url=retry_url)])
            else:
                btn_list.append([InlineKeyboardButton("✅ ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/{bot_username}?start=true")])

            # Fetch Custom F-Sub Text (or default to the new one you provided)
            default_fsub_text = (
                "🚫 ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴍᴜꜱᴛ ᴊᴏɪɴ ᴏᴜʀ ᴘᴀʀᴛɴᴇʀ ᴄʜᴀɴɴᴇʟs ʙᴇʟᴏᴡ. 📢\n\n"
                "ᴛʜɪꜱ ɪs ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ᴏᴜʀ ᴄᴏɴᴛᴇɴᴛ. ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴛʜᴇᴍ ᴀɴᴅ ᴛᴀᴘ ᴛʜᴇ '✅ ᴛʀʏ ᴀɢᴀɪɴ' ʙᴜᴛᴛᴏɴ."
            )
            fsub_msg_text = settings.get("fsub_text", default_fsub_text)
            if not fsub_msg_text: # Ensure no empty string slips through
                fsub_msg_text = default_fsub_text

            await message.reply_text(
                fsub_msg_text,
                reply_markup=InlineKeyboardMarkup(btn_list)
            )
            return
    # ===========================================

    # 👈 UPDATED: DEEP LINKING LOGIC FOR BATCH & AUTO-DELETE
    if len(message.command) > 1 and message.command[1] != "true":
        file_hash = message.command[1]
        file_data = await db.get_file(file_hash)
        
        if file_data:
            file_ids_str = file_data["file_id"]
            
            # Check if ID is in List (JSON) format or old string format
            try:
                file_ids = json.loads(file_ids_str)
            except json.JSONDecodeError:
                file_ids = [file_ids_str] # If it's an old single file, put it in a list
                
            main_caption = file_data.get("caption", "ʜᴇʀᴇ ɪs ʏᴏᴜʀ ꜰɪʟᴇ!")
            sent_msg_ids = []
            
            # Send each file to the user (Single or batch)
            for idx, f_id in enumerate(file_ids):
                # Caption will only be sent on the first video to avoid spam
                cap = main_caption if idx == 0 else ""
                try:
                    msg = await client.send_document(
                        chat_id=message.chat.id,
                        document=f_id,
                        caption=cap
                    )
                    sent_msg_ids.append(msg.id)
                except Exception:
                    try:
                        msg = await client.send_video(
                            chat_id=message.chat.id,
                            video=f_id,
                            caption=cap
                        )
                        sent_msg_ids.append(msg.id)
                    except:
                        pass
                # Slight delay in batch to prevent FloodWait issues
                await asyncio.sleep(0.5)

            # 👈 DM AUTO-DELETE LOGIC ADDED
            dm_autodel_timer = settings.get("auto_delete", 0)
            if dm_autodel_timer > 0 and sent_msg_ids:
                warning = await message.reply_text(f"⚠️ **Note:** ʏᴏᴜʀ ꜰɪʟᴇs ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇᴅ ɪɴ {dm_autodel_timer} sᴇᴄᴏɴᴅs. ᴘʟᴇᴀsᴇ ꜰᴏʀᴡᴀʀᴅ ᴏʀ sᴀᴠᴇ ᴛʜᴇᴍ ǫᴜɪᴄᴋʟʏ.")
                sent_msg_ids.append(warning.id)
                
                # Run deletion task in background
                asyncio.create_task(delete_messages_later(client, message.chat.id, sent_msg_ids, dm_autodel_timer))

            return
        else:
            await message.reply_text("❌ **ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ!**")
            return

    # NORMAL START MENU 
    text, buttons = await get_start_menu(message.from_user.first_name, is_admin)
    await message.reply_text(text, reply_markup=buttons)


# ==================== 2. ADMIN COMMANDS ====================
@Client.on_message(filters.command("admin") & filters.user(Config.ADMINS))
async def admin_cmd(client, message):
    text, buttons = await get_admin_menu()
    await message.reply_text(text, reply_markup=buttons, disable_web_page_preview=True)

@Client.on_message(filters.command("addadmin") & filters.user(Config.ADMINS))
async def add_admin_cmd(client, message):
    try:
        new_admin_id = int(message.command[1])
        Config.ADMINS = list(Config.ADMINS)
        if new_admin_id not in Config.ADMINS:
            Config.ADMINS.append(new_admin_id)
            await message.reply_text(f"> ✅ **sᴜᴄᴄᴇss:** ᴜsᴇʀ `{new_admin_id}` ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴀs ᴀᴅᴍɪɴ!")
        else:
            await message.reply_text("⚠️ **ᴛʜɪs ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ!**")
    except IndexError:
        await message.reply_text("❌ **ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ!**\nᴜsᴇ: `/addadmin UserID`")
    except ValueError:
        await message.reply_text("❌ **ɪɴᴠᴀʟɪᴅ ɪᴅ!** ᴏɴʟʏ ɴᴜᴍʙᴇʀs ᴀʟʟᴏᴡᴇᴅ.")

@Client.on_message(filters.command("deladmin") & filters.user(Config.ADMINS))
async def del_admin_cmd(client, message):
    try:
        del_admin_id = int(message.command[1])
        Config.ADMINS = list(Config.ADMINS)
        if del_admin_id in Config.ADMINS:
            Config.ADMINS.remove(del_admin_id)
            await message.reply_text(f"> 🗑️ **sᴜᴄᴄᴇss:** ᴜsᴇʀ `{del_admin_id}` ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴀᴅᴍɪɴs.")
        else:
            await message.reply_text("⚠️ **ᴛʜɪs ᴜsᴇʀ ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ ᴀᴅᴍɪɴ ʟɪsᴛ!**")
    except IndexError:
        await message.reply_text("❌ **ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ!**\nᴜsᴇ: `/deladmin UserID`")
    except ValueError:
        await message.reply_text("❌ **ɪɴᴠᴀʟɪᴅ ɪᴅ!** ᴏɴʟʏ ɴᴜᴍʙᴇʀs ᴀʟʟᴏᴡᴇᴅ.")


# ==================== 3. ALL CALLBACK HANDLERS ====================
@Client.on_callback_query(filters.regex(r"^(close_panel|open_admin|user_about|user_help|back_start|admin_|edit_|reset_|toggle_|add_|del_|clear_|manage_|set_pm_|cancel_flow)"))
async def main_callback_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    is_admin = user_id in Config.ADMINS

    try:
        if data == "close_panel":
            await query.message.delete()
            
        elif data == "cancel_flow":
            await query.message.edit_text("🚫 **Process closed by Admin.**")

        elif data == "open_admin":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            text, buttons = await get_admin_menu()
            if query.message.video or query.message.photo or query.message.document:
                await query.message.delete()
                await client.send_message(query.message.chat.id, text, reply_markup=buttons, disable_web_page_preview=True)
            else:
                await query.message.edit_text(text, reply_markup=buttons, disable_web_page_preview=True)
                
        elif data == "user_about":
            text, buttons = await get_about_menu(client)
            if query.message.video or query.message.photo or query.message.document:
                await query.message.delete()
                await client.send_message(query.message.chat.id, text, reply_markup=buttons, disable_web_page_preview=True)
            else:
                await query.message.edit_text(text, reply_markup=buttons, disable_web_page_preview=True)

        elif data == "back_start":
            text, buttons = await get_start_menu(query.from_user.first_name, is_admin)
            if query.message.video or query.message.photo or query.message.document:
                await query.message.delete()
                await client.send_message(query.message.chat.id, text, reply_markup=buttons)
            else:
                await query.message.edit_text(text, reply_markup=buttons)

        elif data == "user_help":
            settings = await db.get_settings()
            custom_help_text = settings.get("help_text", None)
            
            if custom_help_text and custom_help_text.lower() != "default":
                text = custom_help_text
            else:
                text = (
                    "> ❓ **𝗛𝗲𝗹𝗽 & 𝗜𝗻𝘀𝘁𝗿𝘂𝗰𝘁𝗶𝗼𝗻𝘀**\n\n"
                    "• **𝗛𝗼𝘄 𝘁𝗼 𝗳𝗶𝗻𝗱 𝗙𝗶𝗹𝗲𝘀 / 𝗔𝗻𝗶𝗺𝗲?**\n"
                    "  Click the episode button in the channel and press `/start` in the bot.\n\n"
                    "• **𝗙𝗼𝗿𝗰𝗲 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:**\n"
                    "  It is mandatory to join the official channel before downloading files."
                )
            
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_start")]])
            help_video = settings.get("help_video", None)
            if help_video:
                try:
                    await query.message.delete()
                    await client.send_video(
                        chat_id=query.message.chat.id, video=help_video,
                        caption=text, reply_markup=buttons
                    )
                except:
                    await client.send_message(query.message.chat.id, text, reply_markup=buttons)
            else:
                if query.message.video or query.message.photo or query.message.document:
                    await query.message.delete()
                    await client.send_message(query.message.chat.id, text, reply_markup=buttons)
                else:
                    await query.message.edit_text(text, reply_markup=buttons)

        # ====== ADMIN SUB-MENUS ======
        elif data == "edit_help_video":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask = await query.message.chat.ask("🎥 **sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ʜᴇʟᴘ ᴠɪᴅᴇᴏ (ꜰɪʟᴇ ɪᴅ ᴏʀ ʟɪɴᴋ):**\n\n(sᴇɴᴅ `OFF` ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴏʀ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask.text and ask.text.lower() == "/cancel": return await ask.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            
            video_val = ask.video.file_id if ask.video else None if ask.text and ask.text.strip().lower() == "off" else ask.text.strip() if ask.text else None
            if video_val is None and not (ask.text and ask.text.strip().lower() == "off"):
                return await ask.reply("❌ **ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏɴʟʏ ᴀ ᴠɪᴅᴇᴏ ᴏʀ ʟɪɴᴋ.**")
            
            await db.update_setting("help_video", video_val)
            await ask.reply("✅ **ʜᴇʟᴘ ᴠɪᴅᴇᴏ ᴜᴘᴅᴀᴛᴇᴅ!**" if video_val else "🗑️ **ʜᴇʟᴘ ᴠɪᴅᴇᴏ ʀᴇᴍᴏᴠᴇᴅ!**")

        elif data == "edit_help_text":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask = await query.message.chat.ask("📝 **sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ʜᴇʟᴘ ᴛᴇxᴛ:**\n\n(sᴇɴᴅ `OFF` ᴏʀ `default` ᴛᴏ ʀᴇsᴇᴛ, ᴏʀ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            
            if ask.text:
                if ask.text.lower() == "/cancel": return await ask.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
                elif ask.text.lower() in ["off", "default"]:
                    await db.update_setting("help_text", None)
                    return await ask.reply("✅ **ʜᴇʟᴘ ᴛᴇxᴛ ʀᴇsᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ!**")
                else:
                    await db.update_setting("help_text", ask.text)
                    await ask.reply("✅ **ʜᴇʟᴘ ᴛᴇxᴛ ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**")
            else:
                await ask.reply("❌ **ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ! ᴏɴʟʏ ᴛᴇxᴛ ɪs ᴀʟʟᴏᴡᴇᴅ.**")

        elif data == "admin_manage":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            text = f"> 👥 **ᴀᴅᴍɪɴ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ**\n\n**ᴄᴜʀʀᴇɴᴛ ᴀᴅᴍɪɴs ᴄᴏᴜɴᴛ:** `{len(Config.ADMINS)}`\n\nᴜsᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴀᴅᴅ ᴏʀ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴs ᴏʀ ᴜsᴇ ᴄᴏᴍᴍᴀɴᴅ `/addadmin ID`."
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ᴀᴅᴅ ᴀᴅᴍɪɴ", callback_data="add_admin"), InlineKeyboardButton("➖ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ", callback_data="del_admin")],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")]
            ])
            await query.message.edit_text(text, reply_markup=buttons)

        elif data == "add_admin":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask = await query.message.chat.ask("➕ **sᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ ɪᴅ ᴏꜰ ᴛʜᴇ ɴᴇᴡ ᴀᴅᴍɪɴ:**\n\n(sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask.text.lower() == "/cancel": return await ask.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            try:
                new_id = int(ask.text.strip())
                Config.ADMINS = list(Config.ADMINS)
                if new_id not in Config.ADMINS:
                    Config.ADMINS.append(new_id)
                    await ask.reply(f"✅ **ᴜsᴇʀ `{new_id}` ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴀs ᴀᴅᴍɪɴ!**")
                else: await ask.reply("⚠️ **ᴛʜɪs ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ!**")
            except ValueError: await ask.reply("❌ **ɪɴᴠᴀʟɪᴅ ɪᴅ! ᴏɴʟʏ ɴᴜᴍʙᴇʀs ᴀʟʟᴏᴡᴇᴅ.**")

        elif data == "del_admin":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask = await query.message.chat.ask("➖ **sᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ ɪᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ꜰʀᴏᴍ ᴀᴅᴍɪɴs:**\n\n(sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask.text.lower() == "/cancel": return await ask.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            try:
                del_id = int(ask.text.strip())
                Config.ADMINS = list(Config.ADMINS)
                if del_id in Config.ADMINS:
                    Config.ADMINS.remove(del_id)
                    await ask.reply(f"🗑️ **ᴜsᴇʀ `{del_id}` ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴀᴅᴍɪɴs!**")
                else: await ask.reply("⚠️ **ᴛʜɪs ᴜsᴇʀ ɪs ɴᴏᴛ ɪɴ ᴛʜᴇ ᴀᴅᴍɪɴ ʟɪsᴛ!**")
            except ValueError: await ask.reply("❌ **ɪɴᴠᴀʟɪᴅ ɪᴅ! ᴏɴʟʏ ɴᴜᴍʙᴇʀs ᴀʟʟᴏᴡᴇᴅ.**")

        # ==============================================================
        # MANAGE POSTING CHANNELS (ADD / REMOVE VIA BUTTONS)
        # ==============================================================
        elif data == "manage_channels":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            
            channels = await db.get_channels() 
            
            text = (
                "<b>📁 MANAGE POSTING CHANNELS</b>\n\n"
                "<i>Manage the channels where the bot will send posts.</i>\n\n"
                "» Tap <b>REMOVE</b> beside a channel to delete it."
            )
            buttons = []
            for ch in channels:
                ch_id = ch.get("id", ch.get("_id"))
                ch_name = ch.get("name", "Unknown Channel")
                
                buttons.append([
                    InlineKeyboardButton(f"📢 {ch_name}", callback_data="noop"),
                    InlineKeyboardButton("❌ REMOVE", callback_data=f"del_bot_ch_{ch_id}")
                ])
                
            buttons.append([InlineKeyboardButton("➕ ADD CHANNEL", callback_data="add_bot_channel")])
            buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="open_admin")])
            
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)

        elif data == "add_bot_channel":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            chat = query.message.chat
            cancel_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 BACK", callback_data="cancel_flow"),
                 InlineKeyboardButton("❌ CLOSE", callback_data="cancel_flow")]
            ])

            try:
                # STEP 1: CHANNEL ID
                id_msg = await chat.ask("➕ **Add channel**\n\nSend the channel ID (numeric, e.g. `-1001234567890`).\n\nSend /cancel to go back.", timeout=120)
                if id_msg.text.lower() == "/cancel": return await id_msg.reply("🚫 **Cancelled.**")
                ch_id = int(id_msg.text)

                # VERIFICATION
                try:
                    verify_chat = await client.get_chat(ch_id)
                except Exception as e:
                    return await id_msg.reply(f"❌ **Error:** `Peer id invalid`\n\n⚠️ **I cannot access this channel!**\nPlease make me an **Admin** in this channel (`{ch_id}`) first.\n\n**Error:** `{e}`")

                # STEP 2: TITLE
                fetched_title = verify_chat.title if verify_chat else "Unknown"
                title_msg = await chat.ask(f"Send the title for this channel (e.g. \"One Piece\"):\n\n**Fetched Title:** `{fetched_title}`", reply_markup=cancel_btn, timeout=120)
                if title_msg.text.lower() == "/cancel": return
                title = title_msg.text

                # STEP 3: GENRES
                genre_msg = await chat.ask("Send **Genres** for this channel (e.g., Romance, Drama) or send `/skip`:", reply_markup=cancel_btn, timeout=120)
                if genre_msg.text.lower() == "/cancel": return
                desc = "" if genre_msg.text.lower() == "/skip" else re.sub(r"(?i)^genres?:\s*", "", genre_msg.text)

                # STEP 4: POSTER IMAGE
                poster_msg = await chat.ask("Send a poster image for this channel, or send `/skip` to skip:", reply_markup=cancel_btn, timeout=120)
                if poster_msg.text and poster_msg.text.lower() == "/cancel": return
                poster_id = poster_msg.photo.file_id if poster_msg.photo else None

                # SAVE TO DB
                channel_data = {
                    "name": title,
                    "description": desc,
                    "poster_id": poster_id
                }
                await db.add_channel(ch_id, channel_data)

                # SUCCESS MSG
                success_text = (
                    "✅ **Channel Added Successfully!**\n\n"
                    f"**Title:** {title}\n"
                    f"**ID:** `{ch_id}`\n"
                    f"**Genres:** {desc if desc else 'Skipped'}\n\n"
                    "*(Post Mode and Auto-Delete settings will be applied globally from the Admin Panel)*"
                )
                if poster_id:
                    await client.send_photo(chat.id, photo=poster_id, caption=success_text)
                else:
                    await client.send_message(chat.id, success_text)

            except asyncio.TimeoutError:
                await client.send_message(chat.id, "⏰ **Time is up! Process reset. Try again.**")
            except ValueError:
                await client.send_message(chat.id, "❌ **Invalid ID provided! Must be numeric.**")

        elif data.startswith("del_bot_ch_"):
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            
            ch_id_to_del = int(data.split("_")[3]) 
            
            await db.remove_channel(ch_id_to_del)
            await query.answer("✅ Channel Removed Successfully!", show_alert=True)
            
            query.data = "manage_channels"
            await main_callback_handler(client, query)

        # ==============================================================
        # MANAGE F-SUB (REQUIREMENTS)
        # ==============================================================
        elif data == "manage_fsub":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            settings = await db.get_settings()
            fsub_channels = settings.get("fsub_channels", [])
            fsub_bots = settings.get("fsub_bots", [])
            
            text = (
                "<b>MANAGE F-SUB REQUIREMENTS</b>\n\n"
                "<i>Your configured channels and bot requirements are shown below.</i>\n\n"
                "» Tap <b>REMOVE</b> beside an item to delete it."
            )
            buttons = []
            for i, ch in enumerate(fsub_channels):
                buttons.append([InlineKeyboardButton(f"{ch['name']} (fsub)", url=ch['url']), InlineKeyboardButton("❌ REMOVE", callback_data=f"del_fch_{i}")])
            for i, bt in enumerate(fsub_bots):
                buttons.append([InlineKeyboardButton(f"🤖 {bt['name']} (bot fsub)", url=bt['url']), InlineKeyboardButton("❌ REMOVE", callback_data=f"del_fbt_{i}")])
                
            buttons.append([InlineKeyboardButton("➕ ADD CHANNEL", callback_data="add_fsub_ch"), InlineKeyboardButton("➕ ADD BOT", callback_data="add_fsub_bot")])
            buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="open_admin")])
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)

        elif data == "add_fsub_ch":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask_id = await query.message.chat.ask("📢 **Send the Channel ID (e.g., -100123456789):**\n\n(Send /cancel to abort)", timeout=120)
            if ask_id.text.lower() == "/cancel": return await ask_id.reply("🚫 **Cancelled.**")
            ch_id = int(ask_id.text.strip())

            ask_name = await query.message.chat.ask("🏷️ **Send Button Name (e.g., Main Channel):**", timeout=120)
            if ask_name.text.lower() == "/cancel": return await ask_name.reply("🚫 **Cancelled.**")
            ch_name = ask_name.text.strip()

            ask_url = await query.message.chat.ask("🔗 **Send Invite Link / URL:**", timeout=120)
            if ask_url.text.lower() == "/cancel": return await ask_url.reply("🚫 **Cancelled.**")
            ch_url = ask_url.text.strip()

            settings = await db.get_settings()
            fsub_channels = settings.get("fsub_channels", [])
            fsub_channels.append({"id": ch_id, "name": ch_name, "url": ch_url})
            await db.update_setting("fsub_channels", fsub_channels)
            await ask_url.reply("✅ **Channel added successfully to F-Sub!**")

        elif data == "add_fsub_bot":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask_name = await query.message.chat.ask("🤖 **Send Button Name (e.g., Backup Bot):**", timeout=120)
            if ask_name.text.lower() == "/cancel": return await ask_name.reply("🚫 **Cancelled.**")
            bot_name = ask_name.text.strip()

            ask_url = await query.message.chat.ask("🔗 **Send Start Link / URL:**", timeout=120)
            if ask_url.text.lower() == "/cancel": return await ask_url.reply("🚫 **Cancelled.**")
            bot_url = ask_url.text.strip()

            settings = await db.get_settings()
            fsub_bots = settings.get("fsub_bots", [])
            fsub_bots.append({"name": bot_name, "url": bot_url})
            await db.update_setting("fsub_bots", fsub_bots)
            await ask_url.reply("✅ **Bot added successfully to F-Sub!**")

        elif data.startswith("del_fch_"):
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            idx = int(data.split("_")[2])
            settings = await db.get_settings()
            fsub_channels = settings.get("fsub_channels", [])
            if 0 <= idx < len(fsub_channels):
                fsub_channels.pop(idx)
                await db.update_setting("fsub_channels", fsub_channels)
                await query.answer("✅ Channel Requirement Removed!", show_alert=True)
                query.data = "manage_fsub"
                await main_callback_handler(client, query)

        elif data.startswith("del_fbt_"):
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            idx = int(data.split("_")[2])
            settings = await db.get_settings()
            fsub_bots = settings.get("fsub_bots", [])
            if 0 <= idx < len(fsub_bots):
                fsub_bots.pop(idx)
                await db.update_setting("fsub_bots", fsub_bots)
                await query.answer("✅ Bot Requirement Removed!", show_alert=True)
                query.data = "manage_fsub"
                await main_callback_handler(client, query)


        elif data == "admin_broadcast":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await query.answer("📢 ʙʀᴏᴀᴅᴄᴀsᴛ ʀᴇᴀᴅʏ! ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ /broadcast.", show_alert=True)

        elif data == "admin_stats":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            users = await db.get_all_users()
            channels = await db.get_channels()
            text = f"> 📊 **ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs**\n\n👤 **ᴛᴏᴛᴀʟ ᴜsᴇʀs:** `{len(users)}`\n📺 **ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴄʜᴀɴɴᴇʟs:** `{len(channels)}`\n👥 **ᴛᴏᴛᴀʟ ᴀᴅᴍɪɴs:** `{len(Config.ADMINS)}`"
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")]])
            await query.message.edit_text(text, reply_markup=buttons)

        elif data == "admin_welcome":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            settings = await db.get_settings()
            curr_msg = settings.get("welcome_msg", "default")
            text = f"> 📝 **ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ sᴇᴛᴛɪɴɢs**\n\n**ᴄᴜʀʀᴇɴᴛ ᴍᴇssᴀɢᴇ:**\n`{curr_msg}`\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴛ ᴀ ɴᴇᴡ ᴍᴇssᴀɢᴇ, ᴏʀ ʀᴇsᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ."
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ᴇᴅɪᴛ ᴍᴇssᴀɢᴇ", callback_data="edit_welcome"), InlineKeyboardButton("🔄 ʀᴇsᴇᴛ ᴅᴇꜰᴀᴜʟᴛ", callback_data="reset_welcome")],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")]
            ])
            await query.message.edit_text(text, reply_markup=buttons)

        elif data == "reset_welcome":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await db.reset_welcome_msg()
            await query.answer("ᴍᴇssᴀɢᴇ ʀᴇsᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ!", show_alert=False)
            query.data = "admin_welcome"
            await main_callback_handler(client, query)

        elif data == "edit_welcome":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask_msg = await query.message.chat.ask("📝 **sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ:**\n\n💡 _You can use {user} in text to mention their name._\n\n(sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask_msg.text.lower() == "/cancel": return await ask_msg.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            await db.update_welcome_msg(ask_msg.text)
            await ask_msg.reply("✅ **ɴᴇᴡ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ sᴇᴛ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**")

        elif data == "admin_post_btns":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            settings = await db.get_settings()
            post_buttons = settings.get("post_buttons", [])
            text = "> 🔗 **ᴍᴀɴᴀɢᴇ ᴘᴏsᴛ ʙᴜᴛᴛᴏɴs**\n\nᴍᴀɴᴀɢᴇ ᴄᴜsᴛᴏᴍ ʙᴜᴛᴛᴏɴs ꜰᴏʀ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛs:\n\n"
            if not post_buttons: text += "🚫 **ɴᴏ ʙᴜᴛᴛᴏɴs ᴄᴜʀʀᴇɴᴛʟʏ sᴇᴛ.**"
            else:
                for i, btn in enumerate(post_buttons, 1): text += f"**{i}. {btn['name']}** - `{btn['url']}`\n"
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ᴀᴅᴅ ʙᴜᴛᴛᴏɴ", callback_data="add_post_btn"), InlineKeyboardButton("➖ ʀᴇᴍᴏᴠᴇ ʙᴜᴛᴛᴏɴ", callback_data="del_post_btn")],
                [InlineKeyboardButton("🗑️ ᴄʟᴇᴀʀ ᴀʟʟ ʙᴜᴛᴛᴏɴs", callback_data="clear_post_btns")],
                [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="open_admin")]
            ])
            await query.message.edit_text(text, reply_markup=buttons, disable_web_page_preview=True)

        elif data == "add_post_btn":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask_name = await query.message.chat.ask("🏷️ **sᴇɴᴅ ᴛʜᴇ ɴᴀᴍᴇ ꜰᴏʀ ᴛʜᴇ ɴᴇᴡ ʙᴜᴛᴛᴏɴ:**\n\n(sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask_name.text.lower() == "/cancel": return await ask_name.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            btn_name = ask_name.text.strip()
            
            ask_url = await query.message.chat.ask("🔗 **sᴇɴᴅ ᴛʜᴇ ᴜʀʟ/ʟɪɴᴋ ꜰᴏʀ ᴛʜɪs ʙᴜᴛᴛᴏɴ:**\n\n(sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask_url.text.lower() == "/cancel": return await ask_url.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            btn_url = ask_url.text.strip()
            
            settings = await db.get_settings()
            post_buttons = settings.get("post_buttons", [])
            post_buttons.append({"name": btn_name, "url": btn_url})
            await db.update_setting("post_buttons", post_buttons)
            await ask_url.reply("✅ **ɴᴇᴡ ʙᴜᴛᴛᴏɴ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**")

        elif data == "del_post_btn":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            settings = await db.get_settings()
            post_buttons = settings.get("post_buttons", [])
            if not post_buttons: return await query.answer("🚫 ɴᴏ ʙᴜᴛᴛᴏɴs ᴛᴏ ʀᴇᴍᴏᴠᴇ!", show_alert=True)
                
            ask_idx = await query.message.chat.ask("🔢 **sᴇɴᴅ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ɴᴜᴍʙᴇʀ ᴛᴏ ʀᴇᴍᴏᴠᴇ (1, 2, 3...):**\n\n(sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            if ask_idx.text.lower() == "/cancel": return await ask_idx.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
            try:
                idx = int(ask_idx.text.strip()) - 1
                if 0 <= idx < len(post_buttons):
                    removed = post_buttons.pop(idx)
                    await db.update_setting("post_buttons", post_buttons)
                    await ask_idx.reply(f"🗑️ **ʙᴜᴛᴛᴏɴ '{removed['name']}' ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**")
                else: await ask_idx.reply("❌ **ɪɴᴠᴀʟɪᴅ ʙᴜᴛᴛᴏɴ ɴᴜᴍʙᴇʀ!**")
            except ValueError: await ask_idx.reply("❌ **ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!**")

        elif data == "clear_post_btns":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await db.update_setting("post_buttons", [])
            await query.answer("🗑️ ᴀʟʟ ᴘᴏsᴛ ʙᴜᴛᴛᴏɴs ᴄʟᴇᴀʀᴇᴅ!", show_alert=True)
            query.data = "admin_post_btns"
            await main_callback_handler(client, query)

        # =============================================================
        # NEW SETTINGS: F-SUB, POST MODE & AUTO-DELETE
        # =============================================================

        elif data == "admin_fsub":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await render_fsub_menu(query)
            
        elif data == "toggle_fsub":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await db.toggle_fsub()
            await query.answer("ꜰ-sᴜʙ sᴇᴛᴛɪɴɢ ᴛᴏɢɢʟᴇᴅ!", show_alert=False)
            await render_fsub_menu(query)
            
        # 👈 NEW CALLBACK HANDLER FOR EDITING F-SUB TEXT
        elif data == "edit_fsub_text":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            ask_msg = await query.message.chat.ask("📝 **sᴇɴᴅ ᴛʜᴇ ɴᴇᴡ ꜰ-sᴜʙ (ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ) ᴍᴇssᴀɢᴇ:**\n\n(sᴇɴᴅ `default` ᴛᴏ ʀᴇsᴇᴛ, ᴏʀ /cancel ᴛᴏ ᴀʙᴏʀᴛ)", timeout=120)
            
            if ask_msg.text:
                if ask_msg.text.lower() == "/cancel": 
                    return await ask_msg.reply("🚫 **ᴄᴀɴᴄᴇʟʟᴇᴅ.**")
                elif ask_msg.text.lower() == "default":
                    await db.update_setting("fsub_text", None)
                    return await ask_msg.reply("✅ **ꜰ-sᴜʙ ᴍᴇssᴀɢᴇ ʀᴇsᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ!**")
                else:
                    await db.update_setting("fsub_text", ask_msg.text)
                    await ask_msg.reply("✅ **ɴᴇᴡ ꜰ-sᴜʙ ᴍᴇssᴀɢᴇ sᴇᴛ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**")
            else:
                await ask_msg.reply("❌ **ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ! ᴏɴʟʏ ᴛᴇxᴛ ɪs ᴀʟʟᴏᴡᴇᴅ.**")

        elif data == "admin_post_mode":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await render_post_mode_menu(query)

        elif data.startswith("set_pm_"):
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            new_mode = data.split("_")[2] # Link, Forward, Copy
            await db.update_setting("post_mode", new_mode)
            await query.answer(f"✅ Post Mode set to: {new_mode}", show_alert=False)
            await render_post_mode_menu(query)

        elif data == "admin_autodel":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            await render_autodel_menu(query)

        elif data == "toggle_dm_autodel":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            settings = await db.get_settings()
            curr = settings.get("auto_delete", 600)
            
            if curr > 0:
                await db.update_setting("auto_delete", 0)
                await query.answer("❌ DM Auto-Delete turned OFF!", show_alert=True)
                await render_autodel_menu(query)
            else:
                ask = await query.message.chat.ask("⏱️ **Send DM Auto-Delete Time:**\n\n(Examples: `30s`, `5m`, `2h`, `1d`)\n(Send /cancel to abort)", timeout=120)
                if ask.text.lower() == "/cancel": return await ask.reply("🚫 **Cancelled.**")
                
                new_val = parse_time(ask.text)
                if new_val is None or new_val <= 0:
                    return await ask.reply("❌ **Invalid time format! Please try again.**")
                
                await db.update_setting("auto_delete", new_val)
                await ask.reply(f"✅ **DM Auto-Delete turned ON for {new_val} seconds!**")
                await render_autodel_menu(query)

        elif data == "toggle_post_autodel":
            if not is_admin: return await query.answer("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!", show_alert=True)
            settings = await db.get_settings()
            curr = settings.get("post_auto_delete", 0)
            
            if curr > 0:
                await db.update_setting("post_auto_delete", 0)
                await query.answer("❌ Post Auto-Delete turned OFF!", show_alert=True)
                await render_autodel_menu(query)
            else:
                ask = await query.message.chat.ask("⏱️ **Send Post Auto-Delete Time:**\n\n(Examples: `30s`, `5m`, `2h`, `1d`)\n(Send /cancel to abort)", timeout=120)
                if ask.text.lower() == "/cancel": return await ask.reply("🚫 **Cancelled.**")
                
                new_val = parse_time(ask.text)
                if new_val is None or new_val <= 0:
                    return await ask.reply("❌ **Invalid time format! Please try again.**")
                
                await db.update_setting("post_auto_delete", new_val)
                await ask.reply(f"✅ **Post Auto-Delete turned ON for {new_val} seconds!**")
                await render_autodel_menu(query)

    except MessageNotModified:
        await query.answer()
    except Exception as e:
        print(f"Callback Error: {e}")


# ==================== 4. BROADCAST COMMAND ====================
@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMINS) & filters.reply)
async def broadcast_msg(client, message):
    users = await db.get_all_users()
    msg = await message.reply("`ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴍᴇssᴀɢᴇ...`")
    success, failed = 0, 0
    
    for user in users:
        try:
            await message.reply_to_message.copy(user["_id"])
            success += 1
            await asyncio.sleep(0.1) 
        except:
            failed += 1
            
    await msg.edit(f"> 📢 **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n✅ sᴜᴄᴄᴇss: `{success}`\n❌ ꜰᴀɪʟᴇᴅ: `{failed}`")

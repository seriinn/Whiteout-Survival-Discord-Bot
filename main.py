import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
import os
import discord
from discord.ext import commands
import sqlite3
from colorama import Fore, Style, init
import requests
import asyncio

init(autoreset=True)

VERSION_URL = "https://raw.githubusercontent.com/Reloisback/Whiteout-Survival-Discord-Bot/refs/heads/main/autoupdateinfo.txt"

def restart_bot():
    print(Fore.YELLOW + "\nRestarting bot..." + Style.RESET_ALL)
    python = sys.executable
    os.execl(python, python, *sys.argv)

def setup_version_table():
    try:
        if not os.path.exists('db'):
            os.makedirs('db')
        with sqlite3.connect('db/settings.sqlite') as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS versions (
                file_name TEXT PRIMARY KEY,
                version TEXT,
                is_main INTEGER DEFAULT 0
            )''')
            conn.commit()
            print(Fore.GREEN + "Version table created successfully." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error creating version table: {e}" + Style.RESET_ALL)

async def check_and_update_files():
    # 기존 업데이트 코드 그대로 사용 가능
    return False  # Railway에서는 업데이트는 수동으로 하셔도 됩니다

class CustomBot(commands.Bot):
    async def on_error(self, event_name, *args, **kwargs):
        if event_name == "on_interaction":
            error = sys.exc_info()[1]
            if isinstance(error, discord.NotFound) and error.code == 10062:
                return
        await super().on_error(event_name, *args, **kwargs)

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.NotFound) and error.code == 10062:
            return
        await super().on_command_error(ctx, error)

intents = discord.Intents.default()
intents.message_content = True

bot = CustomBot(command_prefix='/', intents=intents)

# ===== Railway용 수정: input() 제거, 환경변수 BOT_TOKEN 사용 =====
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    print("Error: BOT_TOKEN 환경변수가 설정되지 않았습니다.")
    exit(1)
# ================================================================

if not os.path.exists('db'):
    os.makedirs('db')
    print(Fore.GREEN + "db folder created" + Style.RESET_ALL)

databases = {
    "conn_alliance": "db/alliance.sqlite",
    "conn_giftcode": "db/giftcode.sqlite",
    "conn_changes": "db/changes.sqlite",
    "conn_users": "db/users.sqlite",
    "conn_settings": "db/settings.sqlite",
}

connections = {name: sqlite3.connect(path) for name, path in databases.items()}

print(Fore.GREEN + "Database connections have been successfully established." + Style.RESET_ALL)

def create_tables():
    with connections["conn_changes"] as conn_changes:
        conn_changes.execute('''CREATE TABLE IF NOT EXISTS nickname_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_nickname TEXT, 
            new_nickname TEXT, 
            change_date TEXT
        )''')
        conn_changes.execute('''CREATE TABLE IF NOT EXISTS furnace_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_furnace_lv INTEGER, 
            new_furnace_lv INTEGER, 
            change_date TEXT
        )''')

    with connections["conn_settings"] as conn_settings:
        conn_settings.execute('''CREATE TABLE IF NOT EXISTS botsettings (
            id INTEGER PRIMARY KEY, 
            channelid INTEGER, 
            giftcodestatus TEXT 
        )''')
        conn_settings.execute('''CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY, 
            is_initial INTEGER
        )''')

    with connections["conn_users"] as conn_users:
        conn_users.execute('''CREATE TABLE IF NOT EXISTS users (
            fid INTEGER PRIMARY KEY, 
            nickname TEXT, 
            furnace_lv INTEGER DEFAULT 0, 
            kid INTEGER, 
            stove_lv_content TEXT, 
            alliance TEXT
        )''')

    with connections["conn_giftcode"] as conn_giftcode:
        conn_giftcode.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
            giftcode TEXT PRIMARY KEY, 
            date TEXT
        )''')
        conn_giftcode.execute('''CREATE TABLE IF NOT EXISTS user_giftcodes (
            fid INTEGER, 
            giftcode TEXT, 
            status TEXT, 
            PRIMARY KEY (fid, giftcode),
            FOREIGN KEY (giftcode) REFERENCES gift_codes (giftcode)
        )''')

    with connections["conn_alliance"] as conn_alliance:
        conn_alliance.execute('''CREATE TABLE IF NOT EXISTS alliancesettings (
            alliance_id INTEGER PRIMARY KEY, 
            channel_id INTEGER, 
            interval INTEGER
        )''')
        conn_alliance.execute('''CREATE TABLE IF NOT EXISTS alliance_list (
            alliance_id INTEGER PRIMARY KEY, 
            name TEXT
        )''')

    print(Fore.GREEN + "All tables checked." + Style.RESET_ALL)

create_tables()
setup_version_table()

async def load_cogs():
    await bot.load_extension("cogs.olddb")
    await bot.load_extension("cogs.control")
    await bot.load_extension("cogs.alliance")
    await bot.load_extension("cogs.alliance_member_operations")
    await bot.load_extension("cogs.bot_operations")
    await bot.load_extension("cogs.logsystem")
    await bot.load_extension("cogs.support_operations")
    await bot.load_extension("cogs.gift_operations")
    await bot.load_extension("cogs.changes")
    await bot.load_extension("cogs.w")
    await bot.load_extension("cogs.wel")
    await bot.load_extension("cogs.other_features")
    await bot.load_extension("cogs.bear_trap")
    await bot.load_extension("cogs.id_channel")
    await bot.load_extension("cogs.backup_operations")
    await bot.load_extension("cogs.bear_trap_editor")

@bot.event
async def on_ready():
    try:
        print(f"{Fore.GREEN}Logged in as {Fore.CYAN}{bot.user}{Style.RESET_ALL}")
        synced = await bot.tree.sync()
    except Exception as e:
        print(f"Error syncing commands: {e}")

async def main():
    # Railway에서는 check_and_install_requirements() 제거
    await check_and_update_files()
    await load_cogs()
    await bot.start(bot_token)

if __name__ == "__main__":
    asyncio.run(main())

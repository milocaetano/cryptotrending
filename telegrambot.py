import argparse
import asyncio
from telegram import Bot

bot = Bot(token='5698857058:AAEmLvAeUsCnbsUycRjBZhIuuU2Sb9d7r6U')

async def get_chat_id():
    updates = await bot.get_updates()
    if not updates:
        raise Exception("No updates found. Please send a message to the bot first.")
    return updates[-1].message.chat_id

async def send_telegram_message(chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message)

async def send_msg(message):
    chat_id = await get_chat_id()
    await send_telegram_message(chat_id, message)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--msg", type=str, help="Message to TelegramBot", required=True)
    args = parser.parse_args()

    try:
        chat_id = await get_chat_id()
        await send_telegram_message(chat_id, args.msg)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())

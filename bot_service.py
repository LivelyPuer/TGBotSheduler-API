import os
from aiogram import Bot
from aiogram.types import InputMediaPhoto, URLInputFile, FSInputFile
from dotenv import load_dotenv
import logging

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.warning("BOT_TOKEN is not set in .env file")

def get_input_file(path: str):
    """Определяет тип файла (URL или локальный) и возвращает соответствующий объект."""
    if path.startswith("http://") or path.startswith("https://"):
        return URLInputFile(path)
    return FSInputFile(path)

async def send_scheduled_message(chat_id: str | int, text: str | None, media_paths: list[str]):
    """
    Отправляет сообщение в Telegram.
    Поддерживает текст, одно фото или группу фото.
    Принимает список путей (URL или локальные пути).
    Удаляет локальные файлы после попытки отправки.
    """
    if not BOT_TOKEN:
        logging.error("Cannot send message: BOT_TOKEN is missing")
        return

    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Случай 1: Только текст
        if not media_paths:
            if text:
                await bot.send_message(chat_id=chat_id, text=text)
            else:
                logging.warning("Empty message scheduled (no text, no photos)")
        
        # Случай 2: Одно фото
        elif len(media_paths) == 1:
            media = get_input_file(media_paths[0])
            await bot.send_photo(
                chat_id=chat_id,
                photo=media,
                caption=text
            )
            
        # Случай 3: Несколько фото (альбом)
        else:
            media_group = []
            for i, path in enumerate(media_paths):
                # Подпись добавляется только к первому элементу медиа-группы
                caption = text if i == 0 else None
                media = get_input_file(path)
                media_group.append(
                    InputMediaPhoto(media=media, caption=caption)
                )
            
            await bot.send_media_group(chat_id=chat_id, media=media_group)
            
        logging.info(f"Message sent to {chat_id}")
        
    except Exception as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")
    finally:
        await bot.session.close()
        
        # Автоматическая очистка локальных файлов
        for path in media_paths:
            # Проверяем, что это не URL и файл существует
            if not (path.startswith("http://") or path.startswith("https://")):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        logging.info(f"Deleted temporary file: {path}")
                except Exception as e:
                    logging.error(f"Failed to delete file {path}: {e}")

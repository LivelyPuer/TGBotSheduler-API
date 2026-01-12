from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import shutil
import uuid
from typing import List, Optional

from bot_service import send_scheduled_message

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка хранилища задач (SQLite для персистентности)
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="UTC")

MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск планировщика при старте приложения
    scheduler.start()
    logger.info("Scheduler started")
    yield
    # Остановка планировщика при выключении
    scheduler.shutdown()
    logger.info("Scheduler shut down")

app = FastAPI(lifespan=lifespan, title="Telegram Post Scheduler")

@app.post("/schedule", summary="Запланировать публикацию")
async def schedule_post(
    chat_id: str = Form(..., description="ID канала или группы"),
    text: Optional[str] = Form(None, description="Текст сообщения"),
    publish_at: datetime = Form(..., description="Время публикации в UTC"),
    photo_urls: List[str] = Form(default=[], description="Список URL картинок"),
    files: List[UploadFile] = File(default=[], description="Список файлов картинок")
):
    """
    Планирует отправку сообщения в Telegram на указанное время (UTC).
    Поддерживает отправку текста, URL картинок и загрузку файлов.
    """
    # Проверка, что время в будущем
    if publish_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Publication time must be in the future")

    media_paths = []
    
    # Добавляем URL
    if photo_urls:
        media_paths.extend(photo_urls)
    
    # Сохраняем загруженные файлы
    if files:
        for file in files:
            try:
                # Генерируем уникальное имя файла, чтобы не было коллизий
                file_ext = os.path.splitext(file.filename)[1]
                filename = f"{uuid.uuid4()}{file_ext}"
                file_path = os.path.join(MEDIA_DIR, filename)
                
                # Сохраняем файл на диск
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Сохраняем абсолютный путь, чтобы бот точно нашел файл
                abs_path = os.path.abspath(file_path)
                media_paths.append(abs_path)
            except Exception as e:
                logger.error(f"Failed to save file {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}")

    try:
        job = scheduler.add_job(
            send_scheduled_message,
            'date',
            run_date=publish_at,
            args=[chat_id, text, media_paths]
        )
        
        return {
            "status": "scheduled",
            "job_id": job.id,
            "publish_at": publish_at,
            "chat_id": chat_id,
            "media_count": len(media_paths)
        }
    except Exception as e:
        logger.error(f"Error scheduling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs", summary="Список запланированных задач")
async def get_jobs():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run_time": job.next_run_time,
            "args": job.args
        })
    return {"jobs": jobs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

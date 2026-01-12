from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PostRequest(BaseModel):
    chat_id: str | int = Field(..., description="ID канала или группы (например, @channelname или -100123456789)")
    text: Optional[str] = Field(None, description="Текст сообщения")
    photo_urls: List[str] = Field(default_factory=list, description="Список URL картинок")
    publish_at: datetime = Field(..., description="Время публикации в UTC")

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "@my_channel",
                "text": "Hello World!",
                "photo_urls": ["https://picsum.photos/200/300"],
                "publish_at": "2024-01-01T12:00:00Z"
            }
        }

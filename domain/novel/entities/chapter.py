# domain/novel/entities/chapter.py
from enum import Enum
from datetime import datetime
from domain.shared.base_entity import BaseEntity
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.chapter_content import ChapterContent
from domain.novel.value_objects.word_count import WordCount


class ChapterStatus(str, Enum):
    """章节状态"""
    DRAFT = "draft"
    REVIEWING = "reviewing"
    COMPLETED = "completed"


class Chapter(BaseEntity):
    """章节实体"""

    def __init__(
        self,
        id: str,
        novel_id: NovelId,
        number: int,
        title: str,
        content: str = "",
        outline: str = "",
        status: ChapterStatus = ChapterStatus.DRAFT
    ):
        super().__init__(id)
        self.novel_id = novel_id
        self.number = number
        self.title = title
        self._content_text = content  # 直接存储文本，允许空内容
        self.outline = outline  # 章节大纲
        self.status = status

    @property
    def content(self) -> str:
        return self._content_text

    @property
    def word_count(self) -> WordCount:
        if not self._content_text:
            return WordCount(0)
        content_obj = ChapterContent(self._content_text)
        return WordCount(content_obj.word_count())

    def update_content(self, content: str) -> None:
        """更新内容（允许空内容用于草稿）"""
        self._content_text = content
        self.updated_at = datetime.utcnow()

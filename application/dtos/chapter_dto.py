"""Chapter 数据传输对象"""
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.novel.entities.chapter import Chapter


@dataclass
class ChapterDTO:
    """章节 DTO"""
    id: str
    novel_id: str
    number: int
    title: str
    content: str
    word_count: int
    status: str

    @classmethod
    def from_domain(cls, chapter: 'Chapter') -> 'ChapterDTO':
        """从领域对象创建 DTO

        Args:
            chapter: Chapter 领域对象

        Returns:
            ChapterDTO
        """
        return cls(
            id=chapter.id,
            novel_id=chapter.novel_id.value,
            number=chapter.number,
            title=chapter.title,
            content=chapter.content,
            word_count=chapter.word_count.value,
            status=chapter.status.value
        )

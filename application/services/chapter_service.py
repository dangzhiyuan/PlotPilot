"""Chapter 应用服务"""
from typing import List, Optional
from domain.novel.entities.chapter import Chapter
from domain.novel.value_objects.chapter_id import ChapterId
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.repositories.chapter_repository import ChapterRepository
from domain.novel.repositories.novel_repository import NovelRepository
from domain.shared.exceptions import EntityNotFoundError
from application.dtos.chapter_dto import ChapterDTO


class ChapterService:
    """Chapter 应用服务"""

    def __init__(
        self,
        chapter_repository: ChapterRepository,
        novel_repository: NovelRepository
    ):
        """初始化服务

        Args:
            chapter_repository: Chapter 仓储
            novel_repository: Novel 仓储
        """
        self.chapter_repository = chapter_repository
        self.novel_repository = novel_repository

    def update_chapter_content(
        self,
        chapter_id: str,
        content: str
    ) -> ChapterDTO:
        """更新章节内容

        Args:
            chapter_id: 章节 ID
            content: 内容

        Returns:
            更新后的 ChapterDTO

        Raises:
            EntityNotFoundError: 如果章节不存在
        """
        chapter = self.chapter_repository.get_by_id(ChapterId(chapter_id))
        if chapter is None:
            raise EntityNotFoundError("Chapter", chapter_id)

        chapter.update_content(content)
        self.chapter_repository.save(chapter)

        return ChapterDTO.from_domain(chapter)

    def list_chapters_by_novel(self, novel_id: str) -> List[ChapterDTO]:
        """列出小说的所有章节

        Args:
            novel_id: 小说 ID

        Returns:
            ChapterDTO 列表
        """
        chapters = self.chapter_repository.list_by_novel(NovelId(novel_id))
        return [ChapterDTO.from_domain(chapter) for chapter in chapters]

    def get_chapter(self, chapter_id: str) -> Optional[ChapterDTO]:
        """获取章节

        Args:
            chapter_id: 章节 ID

        Returns:
            ChapterDTO 或 None
        """
        chapter = self.chapter_repository.get_by_id(ChapterId(chapter_id))
        if chapter is None:
            return None
        return ChapterDTO.from_domain(chapter)

    def delete_chapter(self, chapter_id: str) -> None:
        """删除章节

        Args:
            chapter_id: 章节 ID
        """
        self.chapter_repository.delete(ChapterId(chapter_id))

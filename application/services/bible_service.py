"""Bible 应用服务"""
from typing import Optional
from domain.bible.entities.bible import Bible
from domain.bible.entities.character import Character
from domain.bible.entities.world_setting import WorldSetting
from domain.bible.value_objects.character_id import CharacterId
from domain.novel.value_objects.novel_id import NovelId
from domain.bible.repositories.bible_repository import BibleRepository
from domain.shared.exceptions import EntityNotFoundError
from application.dtos.bible_dto import BibleDTO


class BibleService:
    """Bible 应用服务"""

    def __init__(self, bible_repository: BibleRepository):
        """初始化服务

        Args:
            bible_repository: Bible 仓储
        """
        self.bible_repository = bible_repository

    def create_bible(self, bible_id: str, novel_id: str) -> BibleDTO:
        """创建 Bible

        Args:
            bible_id: Bible ID
            novel_id: 小说 ID

        Returns:
            BibleDTO
        """
        bible = Bible(id=bible_id, novel_id=NovelId(novel_id))
        self.bible_repository.save(bible)
        return BibleDTO.from_domain(bible)

    def add_character(
        self,
        novel_id: str,
        character_id: str,
        name: str,
        description: str
    ) -> BibleDTO:
        """添加人物

        Args:
            novel_id: 小说 ID
            character_id: 人物 ID
            name: 人物名称
            description: 人物描述

        Returns:
            更新后的 BibleDTO

        Raises:
            EntityNotFoundError: 如果 Bible 不存在
        """
        bible = self.bible_repository.get_by_novel_id(NovelId(novel_id))
        if bible is None:
            raise EntityNotFoundError("Bible", f"for novel {novel_id}")

        character = Character(
            id=CharacterId(character_id),
            name=name,
            description=description
        )
        bible.add_character(character)
        self.bible_repository.save(bible)

        return BibleDTO.from_domain(bible)

    def add_world_setting(
        self,
        novel_id: str,
        setting_id: str,
        name: str,
        description: str,
        setting_type: str
    ) -> BibleDTO:
        """添加世界设定

        Args:
            novel_id: 小说 ID
            setting_id: 设定 ID
            name: 设定名称
            description: 设定描述
            setting_type: 设定类型

        Returns:
            更新后的 BibleDTO

        Raises:
            EntityNotFoundError: 如果 Bible 不存在
        """
        bible = self.bible_repository.get_by_novel_id(NovelId(novel_id))
        if bible is None:
            raise EntityNotFoundError("Bible", f"for novel {novel_id}")

        setting = WorldSetting(
            id=setting_id,
            name=name,
            description=description,
            setting_type=setting_type
        )
        bible.add_world_setting(setting)
        self.bible_repository.save(bible)

        return BibleDTO.from_domain(bible)

    def get_bible_by_novel(self, novel_id: str) -> Optional[BibleDTO]:
        """根据小说 ID 获取 Bible

        Args:
            novel_id: 小说 ID

        Returns:
            BibleDTO 或 None
        """
        bible = self.bible_repository.get_by_novel_id(NovelId(novel_id))
        if bible is None:
            return None
        return BibleDTO.from_domain(bible)

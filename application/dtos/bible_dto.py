"""Bible 数据传输对象"""
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.bible.entities.bible import Bible
    from domain.bible.entities.character import Character
    from domain.bible.entities.world_setting import WorldSetting


@dataclass
class CharacterDTO:
    """人物 DTO"""
    id: str
    name: str
    description: str
    relationships: List[str]

    @classmethod
    def from_domain(cls, character: 'Character') -> 'CharacterDTO':
        """从领域对象创建 DTO

        Args:
            character: Character 领域对象

        Returns:
            CharacterDTO
        """
        return cls(
            id=character.character_id.value,
            name=character.name,
            description=character.description,
            relationships=character.relationships.copy()
        )


@dataclass
class WorldSettingDTO:
    """世界设定 DTO"""
    id: str
    name: str
    description: str
    setting_type: str

    @classmethod
    def from_domain(cls, setting: 'WorldSetting') -> 'WorldSettingDTO':
        """从领域对象创建 DTO

        Args:
            setting: WorldSetting 领域对象

        Returns:
            WorldSettingDTO
        """
        return cls(
            id=setting.id,
            name=setting.name,
            description=setting.description,
            setting_type=setting.setting_type
        )


@dataclass
class BibleDTO:
    """Bible DTO"""
    id: str
    novel_id: str
    characters: List[CharacterDTO]
    world_settings: List[WorldSettingDTO]

    @classmethod
    def from_domain(cls, bible: 'Bible') -> 'BibleDTO':
        """从领域对象创建 DTO

        Args:
            bible: Bible 领域对象

        Returns:
            BibleDTO
        """
        return cls(
            id=bible.id,
            novel_id=bible.novel_id.value,
            characters=[CharacterDTO.from_domain(c) for c in bible.characters],
            world_settings=[WorldSettingDTO.from_domain(s) for s in bible.world_settings]
        )

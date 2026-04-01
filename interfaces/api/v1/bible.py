"""Bible API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from application.services.bible_service import BibleService
from application.dtos.bible_dto import BibleDTO
from interfaces.api.dependencies import get_bible_service
from domain.shared.exceptions import EntityNotFoundError


router = APIRouter(prefix="/bible", tags=["bible"])


# Request Models
class CreateBibleRequest(BaseModel):
    """创建 Bible 请求"""
    bible_id: str = Field(..., description="Bible ID")
    novel_id: str = Field(..., description="小说 ID")


class AddCharacterRequest(BaseModel):
    """添加人物请求"""
    character_id: str = Field(..., description="人物 ID")
    name: str = Field(..., description="人物名称")
    description: str = Field(..., description="人物描述")


class AddWorldSettingRequest(BaseModel):
    """添加世界设定请求"""
    setting_id: str = Field(..., description="设定 ID")
    name: str = Field(..., description="设定名称")
    description: str = Field(..., description="设定描述")
    setting_type: str = Field(..., description="设定类型")


class AddLocationRequest(BaseModel):
    """添加地点请求"""
    location_id: str = Field(..., description="地点 ID")
    name: str = Field(..., description="地点名称")
    description: str = Field(..., description="地点描述")
    location_type: str = Field(..., description="地点类型")


class AddTimelineNoteRequest(BaseModel):
    """添加时间线笔记请求"""
    note_id: str = Field(..., description="笔记 ID")
    event: str = Field(..., description="事件")
    time_point: str = Field(..., description="时间点")
    description: str = Field(..., description="描述")


class AddStyleNoteRequest(BaseModel):
    """添加风格笔记请求"""
    note_id: str = Field(..., description="笔记 ID")
    category: str = Field(..., description="类别")
    content: str = Field(..., description="内容")


class CharacterData(BaseModel):
    """人物数据"""
    id: str = Field(..., description="人物 ID")
    name: str = Field(..., description="人物名称")
    description: str = Field(..., description="人物描述")
    relationships: list[str] = Field(default_factory=list, description="关系列表")


class WorldSettingData(BaseModel):
    """世界设定数据"""
    id: str = Field(..., description="设定 ID")
    name: str = Field(..., description="设定名称")
    description: str = Field(..., description="设定描述")
    setting_type: str = Field(..., description="设定类型")


class LocationData(BaseModel):
    """地点数据"""
    id: str = Field(..., description="地点 ID")
    name: str = Field(..., description="地点名称")
    description: str = Field(..., description="地点描述")
    location_type: str = Field(..., description="地点类型")


class TimelineNoteData(BaseModel):
    """时间线笔记数据"""
    id: str = Field(..., description="笔记 ID")
    event: str = Field(..., description="事件")
    time_point: str = Field(..., description="时间点")
    description: str = Field(..., description="描述")


class StyleNoteData(BaseModel):
    """风格笔记数据"""
    id: str = Field(..., description="笔记 ID")
    category: str = Field(..., description="类别")
    content: str = Field(..., description="内容")


class BulkUpdateBibleRequest(BaseModel):
    """批量更新 Bible 请求"""
    characters: list[CharacterData] = Field(default_factory=list, description="人物列表")
    world_settings: list[WorldSettingData] = Field(default_factory=list, description="世界设定列表")
    locations: list[LocationData] = Field(default_factory=list, description="地点列表")
    timeline_notes: list[TimelineNoteData] = Field(default_factory=list, description="时间线笔记列表")
    style_notes: list[StyleNoteData] = Field(default_factory=list, description="风格笔记列表")


# Routes
@router.post("/novels/{novel_id}/bible", response_model=BibleDTO, status_code=201)
async def create_bible(
    novel_id: str,
    request: CreateBibleRequest,
    service: BibleService = Depends(get_bible_service)
):
    """为小说创建 Bible

    Args:
        novel_id: 小说 ID
        request: 创建 Bible 请求
        service: Bible 服务

    Returns:
        创建的 Bible DTO
    """
    return service.create_bible(request.bible_id, novel_id)


@router.get("/novels/{novel_id}/bible", response_model=BibleDTO)
async def get_bible_by_novel(
    novel_id: str,
    service: BibleService = Depends(get_bible_service)
):
    """获取小说的 Bible

    Args:
        novel_id: 小说 ID
        service: Bible 服务

    Returns:
        Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    bible = service.get_bible_by_novel(novel_id)
    if bible is None:
        raise HTTPException(
            status_code=404,
            detail=f"Bible not found for novel: {novel_id}"
        )
    return bible


@router.get("/novels/{novel_id}/bible/characters", response_model=list)
async def list_characters(
    novel_id: str,
    service: BibleService = Depends(get_bible_service)
):
    """列出 Bible 中的所有人物

    Args:
        novel_id: 小说 ID
        service: Bible 服务

    Returns:
        人物 DTO 列表

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    bible = service.get_bible_by_novel(novel_id)
    if bible is None:
        raise HTTPException(
            status_code=404,
            detail=f"Bible not found for novel: {novel_id}"
        )
    return bible.characters


@router.post("/novels/{novel_id}/bible/characters", response_model=BibleDTO)
async def add_character(
    novel_id: str,
    request: AddCharacterRequest,
    service: BibleService = Depends(get_bible_service)
):
    """添加人物到 Bible

    Args:
        novel_id: 小说 ID
        request: 添加人物请求
        service: Bible 服务

    Returns:
        更新后的 Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    try:
        return service.add_character(
            novel_id=novel_id,
            character_id=request.character_id,
            name=request.name,
            description=request.description
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/novels/{novel_id}/bible/world-settings", response_model=BibleDTO)
async def add_world_setting(
    novel_id: str,
    request: AddWorldSettingRequest,
    service: BibleService = Depends(get_bible_service)
):
    """添加世界设定到 Bible

    Args:
        novel_id: 小说 ID
        request: 添加世界设定请求
        service: Bible 服务

    Returns:
        更新后的 Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    try:
        return service.add_world_setting(
            novel_id=novel_id,
            setting_id=request.setting_id,
            name=request.name,
            description=request.description,
            setting_type=request.setting_type
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/novels/{novel_id}/bible/locations", response_model=BibleDTO)
async def add_location(
    novel_id: str,
    request: AddLocationRequest,
    service: BibleService = Depends(get_bible_service)
):
    """添加地点到 Bible

    Args:
        novel_id: 小说 ID
        request: 添加地点请求
        service: Bible 服务

    Returns:
        更新后的 Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    try:
        return service.add_location(
            novel_id=novel_id,
            location_id=request.location_id,
            name=request.name,
            description=request.description,
            location_type=request.location_type
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/novels/{novel_id}/bible/timeline-notes", response_model=BibleDTO)
async def add_timeline_note(
    novel_id: str,
    request: AddTimelineNoteRequest,
    service: BibleService = Depends(get_bible_service)
):
    """添加时间线笔记到 Bible

    Args:
        novel_id: 小说 ID
        request: 添加时间线笔记请求
        service: Bible 服务

    Returns:
        更新后的 Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    try:
        return service.add_timeline_note(
            novel_id=novel_id,
            note_id=request.note_id,
            event=request.event,
            time_point=request.time_point,
            description=request.description
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/novels/{novel_id}/bible/style-notes", response_model=BibleDTO)
async def add_style_note(
    novel_id: str,
    request: AddStyleNoteRequest,
    service: BibleService = Depends(get_bible_service)
):
    """添加风格笔记到 Bible

    Args:
        novel_id: 小说 ID
        request: 添加风格笔记请求
        service: Bible 服务

    Returns:
        更新后的 Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    try:
        return service.add_style_note(
            novel_id=novel_id,
            note_id=request.note_id,
            category=request.category,
            content=request.content
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/novels/{novel_id}/bible", response_model=BibleDTO)
async def bulk_update_bible(
    novel_id: str,
    request: BulkUpdateBibleRequest,
    service: BibleService = Depends(get_bible_service)
):
    """批量更新 Bible 的所有数据

    Args:
        novel_id: 小说 ID
        request: 批量更新请求
        service: Bible 服务

    Returns:
        更新后的 Bible DTO

    Raises:
        HTTPException: 如果 Bible 不存在
    """
    try:
        return service.update_bible(
            novel_id=novel_id,
            characters=request.characters,
            world_settings=request.world_settings,
            locations=request.locations,
            timeline_notes=request.timeline_notes,
            style_notes=request.style_notes
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

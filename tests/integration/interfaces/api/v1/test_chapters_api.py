"""Chapter API 集成测试

测试 Chapter API 端点的集成功能。
"""
import pytest
from fastapi.testclient import TestClient
import shutil
from pathlib import Path
from infrastructure.persistence.storage.file_storage import FileStorage
from infrastructure.persistence.repositories.file_novel_repository import FileNovelRepository
from infrastructure.persistence.repositories.file_chapter_repository import FileChapterRepository
from application.services.novel_service import NovelService
from application.services.chapter_service import ChapterService
from interfaces.api.dependencies import get_novel_service, get_chapter_service
from interfaces.main import app


# Global variables to hold test services
_test_novel_service = None
_test_chapter_service = None


def get_test_novel_service():
    """Get test novel service"""
    return _test_novel_service


def get_test_chapter_service():
    """Get test chapter service"""
    return _test_chapter_service


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """设置测试环境"""
    global _test_novel_service, _test_chapter_service

    test_data = tmp_path / "data"
    test_data.mkdir()

    # 创建测试存储和仓储
    storage = FileStorage(test_data)
    novel_repo = FileNovelRepository(storage)
    chapter_repo = FileChapterRepository(storage)

    # 创建服务
    _test_novel_service = NovelService(novel_repo, chapter_repo)
    _test_chapter_service = ChapterService(chapter_repo, novel_repo)

    # 覆盖依赖
    app.dependency_overrides[get_novel_service] = get_test_novel_service
    app.dependency_overrides[get_chapter_service] = get_test_chapter_service

    yield

    # 清理
    app.dependency_overrides.clear()
    _test_novel_service = None
    _test_chapter_service = None
    if test_data.exists():
        shutil.rmtree(test_data)


client = TestClient(app)


@pytest.fixture
def test_novel():
    """创建测试小说"""
    response = client.post("/api/v1/novels/", json={
        "novel_id": "test-novel-chapters",
        "title": "测试小说",
        "author": "测试作者",
        "target_chapters": 10
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_chapter(test_novel):
    """创建测试章节"""
    from domain.novel.entities.chapter import Chapter, ChapterStatus
    from domain.novel.value_objects.novel_id import NovelId

    # 直接通过仓储创建章节
    chapter = Chapter(
        id="chapter-1",
        novel_id=NovelId("test-novel-chapters"),
        number=1,
        title="第一章",
        content="这是第一章的内容",
        status=ChapterStatus.DRAFT
    )

    # 使用测试服务的仓储
    _test_chapter_service.chapter_repository.save(chapter)

    return {
        "id": "chapter-1",
        "novel_id": "test-novel-chapters",
        "number": 1,
        "title": "第一章",
        "content": "这是第一章的内容"
    }


class TestListChapters:
    """测试列出章节端点"""

    def test_list_chapters_empty(self, test_novel):
        """测试列出空章节列表"""
        response = client.get("/api/v1/novels/test-novel-chapters/chapters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_chapters_with_data(self, test_chapter):
        """测试列出有数据的章节列表"""
        response = client.get("/api/v1/novels/test-novel-chapters/chapters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["number"] == 1
        assert data[0]["title"] == "第一章"
        assert data[0]["novel_id"] == "test-novel-chapters"

    def test_list_chapters_multiple(self, test_novel):
        """测试列出多个章节"""
        from domain.novel.entities.chapter import Chapter, ChapterStatus
        from domain.novel.value_objects.novel_id import NovelId

        # 使用测试服务的仓储
        repo = _test_chapter_service.chapter_repository

        # 创建多个章节
        for i in range(1, 4):
            chapter = Chapter(
                id=f"chapter-{i}",
                novel_id=NovelId("test-novel-chapters"),
                number=i,
                title=f"第{i}章",
                content=f"这是第{i}章的内容",
                status=ChapterStatus.DRAFT
            )
            repo.save(chapter)

        response = client.get("/api/v1/novels/test-novel-chapters/chapters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # 验证按章节号排序
        assert data[0]["number"] == 1
        assert data[1]["number"] == 2
        assert data[2]["number"] == 3


class TestGetChapter:
    """测试获取单个章节端点"""

    def test_get_chapter_success(self, test_chapter):
        """测试成功获取章节"""
        response = client.get("/api/v1/novels/test-novel-chapters/chapters/1")
        assert response.status_code == 200
        data = response.json()
        assert data["number"] == 1
        assert data["title"] == "第一章"
        assert data["content"] == "这是第一章的内容"
        assert data["novel_id"] == "test-novel-chapters"

    def test_get_chapter_not_found(self, test_novel):
        """测试获取不存在的章节"""
        response = client.get("/api/v1/novels/test-novel-chapters/chapters/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_chapter_wrong_novel(self, test_chapter):
        """测试从错误的小说获取章节"""
        response = client.get("/api/v1/novels/wrong-novel-id/chapters/1")
        assert response.status_code == 404


class TestUpdateChapter:
    """测试更新章节端点"""

    def test_update_chapter_content(self, test_chapter):
        """测试更新章节内容"""
        new_content = "这是更新后的内容"
        response = client.put(
            "/api/v1/novels/test-novel-chapters/chapters/1",
            json={"content": new_content}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == new_content
        assert data["number"] == 1
        assert data["novel_id"] == "test-novel-chapters"

        # 验证内容已持久化
        get_response = client.get("/api/v1/novels/test-novel-chapters/chapters/1")
        assert get_response.status_code == 200
        assert get_response.json()["content"] == new_content

    def test_update_chapter_empty_content(self, test_chapter):
        """测试更新章节为空内容"""
        response = client.put(
            "/api/v1/novels/test-novel-chapters/chapters/1",
            json={"content": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == ""

    def test_update_chapter_not_found(self, test_novel):
        """测试更新不存在的章节"""
        response = client.put(
            "/api/v1/novels/test-novel-chapters/chapters/999",
            json={"content": "新内容"}
        )
        assert response.status_code == 404

    def test_update_chapter_wrong_novel(self, test_chapter):
        """测试从错误的小说更新章节"""
        response = client.put(
            "/api/v1/novels/wrong-novel-id/chapters/1",
            json={"content": "新内容"}
        )
        assert response.status_code == 404

    def test_update_chapter_invalid_request(self, test_chapter):
        """测试无效的更新请求"""
        response = client.put(
            "/api/v1/novels/test-novel-chapters/chapters/1",
            json={}
        )
        assert response.status_code == 422  # Validation error

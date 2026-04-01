"""Chapter Review API 集成测试"""
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
        "novel_id": "test-novel-review",
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

    chapter = Chapter(
        id="chapter-1",
        novel_id=NovelId("test-novel-review"),
        number=1,
        title="第一章",
        content="这是第一章的内容。\n\n这是第二段。",
        status=ChapterStatus.DRAFT
    )

    _test_chapter_service.chapter_repository.save(chapter)
    return chapter


class TestGetChapterReview:
    """测试获取章节审阅端点"""

    def test_get_review_not_exists(self, test_chapter):
        """测试获取不存在的审阅"""
        response = client.get("/api/v1/novels/test-novel-review/chapters/1/review")
        assert response.status_code == 200
        data = response.json()
        # 应该返回默认值
        assert data["status"] == "draft"
        assert data["memo"] == ""

    def test_get_review_after_save(self, test_chapter):
        """测试保存后获取审阅"""
        # 先保存审阅
        save_response = client.put(
            "/api/v1/novels/test-novel-review/chapters/1/review",
            json={
                "status": "reviewed",
                "memo": "需要修改开头"
            }
        )
        assert save_response.status_code == 200

        # 再获取审阅
        response = client.get("/api/v1/novels/test-novel-review/chapters/1/review")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["memo"] == "需要修改开头"
        assert "created_at" in data
        assert "updated_at" in data


class TestSaveChapterReview:
    """测试保存章节审阅端点"""

    def test_save_review_success(self, test_chapter):
        """测试成功保存审阅"""
        response = client.put(
            "/api/v1/novels/test-novel-review/chapters/1/review",
            json={
                "status": "reviewed",
                "memo": "整体不错，需要调整节奏"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["memo"] == "整体不错，需要调整节奏"
        assert "created_at" in data
        assert "updated_at" in data

    def test_save_review_update_existing(self, test_chapter):
        """测试更新已存在的审阅"""
        # 第一次保存
        client.put(
            "/api/v1/novels/test-novel-review/chapters/1/review",
            json={
                "status": "reviewed",
                "memo": "初稿"
            }
        )

        # 第二次更新
        response = client.put(
            "/api/v1/novels/test-novel-review/chapters/1/review",
            json={
                "status": "approved",
                "memo": "修改后通过"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["memo"] == "修改后通过"

    def test_save_review_invalid_status(self, test_chapter):
        """测试无效的状态"""
        response = client.put(
            "/api/v1/novels/test-novel-review/chapters/1/review",
            json={
                "status": "invalid_status",
                "memo": "测试"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_save_review_chapter_not_found(self, test_novel):
        """测试章节不存在"""
        response = client.put(
            "/api/v1/novels/test-novel-review/chapters/999/review",
            json={
                "status": "reviewed",
                "memo": "测试"
            }
        )
        assert response.status_code == 404


class TestAIReviewChapter:
    """测试 AI 审阅章节端点"""

    def test_ai_review_chapter_not_found(self, test_novel):
        """测试章节不存在"""
        response = client.post("/api/v1/novels/test-novel-review/chapters/999/review-ai")
        assert response.status_code == 404

    def test_ai_review_empty_content(self, test_novel):
        """测试空内容章节"""
        from domain.novel.entities.chapter import Chapter, ChapterStatus
        from domain.novel.value_objects.novel_id import NovelId

        chapter = Chapter(
            id="chapter-empty",
            novel_id=NovelId("test-novel-review"),
            number=2,
            title="空章节",
            content="",
            status=ChapterStatus.DRAFT
        )
        _test_chapter_service.chapter_repository.save(chapter)

        response = client.post("/api/v1/novels/test-novel-review/chapters/2/review-ai")
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

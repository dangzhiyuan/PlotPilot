"""Chapter Structure API 集成测试"""
import pytest
from fastapi.testclient import TestClient
import shutil
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
        "novel_id": "test-novel-structure",
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

    content = """第一章 开始

"你好，世界！"他说道。

这是一个新的开始。每个人都在期待着什么。

"我们该怎么办？"她问。

他思考了一会儿，然后回答："我们继续前进。"

---

第二场景开始了。

时间流逝，事情在变化。人们在成长。

"这就是生活。"他们说。
"""

    chapter = Chapter(
        id="chapter-1",
        novel_id=NovelId("test-novel-structure"),
        number=1,
        title="第一章",
        content=content,
        status=ChapterStatus.DRAFT
    )

    _test_chapter_service.chapter_repository.save(chapter)
    return chapter


class TestGetChapterStructure:
    """测试获取章节结构端点"""

    def test_get_structure_success(self, test_chapter):
        """测试成功获取章节结构"""
        response = client.get("/api/v1/novels/test-novel-structure/chapters/1/structure")
        assert response.status_code == 200
        data = response.json()

        # 验证返回的字段
        assert "word_count" in data
        assert "paragraph_count" in data
        assert "dialogue_ratio" in data
        assert "scene_count" in data
        assert "pacing" in data

        # 验证数据类型
        assert isinstance(data["word_count"], int)
        assert isinstance(data["paragraph_count"], int)
        assert isinstance(data["dialogue_ratio"], float)
        assert isinstance(data["scene_count"], int)
        assert data["pacing"] in ["slow", "medium", "fast"]

        # 验证基本逻辑
        assert data["word_count"] > 0
        assert data["paragraph_count"] > 0
        assert 0.0 <= data["dialogue_ratio"] <= 1.0

    def test_get_structure_empty_chapter(self, test_novel):
        """测试空章节的结构分析"""
        from domain.novel.entities.chapter import Chapter, ChapterStatus
        from domain.novel.value_objects.novel_id import NovelId

        chapter = Chapter(
            id="chapter-empty",
            novel_id=NovelId("test-novel-structure"),
            number=2,
            title="空章节",
            content="",
            status=ChapterStatus.DRAFT
        )
        _test_chapter_service.chapter_repository.save(chapter)

        response = client.get("/api/v1/novels/test-novel-structure/chapters/2/structure")
        assert response.status_code == 200
        data = response.json()
        assert data["word_count"] == 0
        assert data["paragraph_count"] == 0

    def test_get_structure_chapter_not_found(self, test_novel):
        """测试章节不存在"""
        response = client.get("/api/v1/novels/test-novel-structure/chapters/999/structure")
        assert response.status_code == 404

    def test_get_structure_dialogue_heavy(self, test_novel):
        """测试对话密集的章节"""
        from domain.novel.entities.chapter import Chapter, ChapterStatus
        from domain.novel.value_objects.novel_id import NovelId

        content = """"你好。"
"你好。"
"今天天气不错。"
"是的。"
"我们去散步吧。"
"好的。"
"""

        chapter = Chapter(
            id="chapter-dialogue",
            novel_id=NovelId("test-novel-structure"),
            number=3,
            title="对话章节",
            content=content,
            status=ChapterStatus.DRAFT
        )
        _test_chapter_service.chapter_repository.save(chapter)

        response = client.get("/api/v1/novels/test-novel-structure/chapters/3/structure")
        assert response.status_code == 200
        data = response.json()
        # 对话比例应该很高
        assert data["dialogue_ratio"] > 0.5

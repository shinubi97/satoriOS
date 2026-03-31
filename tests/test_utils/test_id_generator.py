"""ID生成器模块测试."""
import pytest
from datetime import datetime
from obsidian_kb.utils.id_generator import generate_note_id, NoteId, parse_note_id


class TestIdGenerator:
    """ID生成器测试."""

    def test_generate_note_id_format(self):
        """测试生成的 ID 符合格式 kb-YYYYMMDD-HHMMSS-XXXX."""
        id_str = generate_note_id()

        # 验证格式
        assert id_str.startswith("kb-")
        parts = id_str.split("-")
        assert len(parts) == 4  # kb, YYYYMMDD, HHMMSS, XXXX

        # 验证日期部分
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 4  # 随机码

    def test_generate_note_id_unique(self):
        """测试生成的 ID 在并发情况下唯一."""
        ids = [generate_note_id() for _ in range(100)]

        # 所有 ID 应该唯一
        assert len(ids) == len(set(ids))

    def test_generate_note_id_contains_current_date(self):
        """测试 ID 包含当前日期."""
        now = datetime.now()
        expected_date_part = now.strftime("%Y%m%d")

        id_str = generate_note_id()
        assert expected_date_part in id_str

    def test_note_id_class(self):
        """测试 NoteId 类."""
        id_str = "kb-20250330-143052-a3f9"
        note_id = NoteId.from_string(id_str)

        assert note_id.prefix == "kb"
        assert note_id.date == "20250330"
        assert note_id.time == "143052"
        assert note_id.random == "a3f9"
        assert str(note_id) == id_str

    def test_note_id_to_datetime(self):
        """测试 NoteId 转换为 datetime."""
        id_str = "kb-20250330-143052-a3f9"
        note_id = NoteId.from_string(id_str)

        dt = note_id.to_datetime()
        assert dt.year == 2025
        assert dt.month == 3
        assert dt.day == 30
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 52

    def test_parse_note_id_valid(self):
        """测试解析有效的 ID."""
        id_str = "kb-20250330-143052-a3f9"
        note_id = parse_note_id(id_str)

        assert note_id is not None
        assert note_id.date == "20250330"

    def test_parse_note_id_invalid(self):
        """测试解析无效的 ID 返回 None."""
        invalid_ids = [
            "invalid-id",
            "kb-2025-14-30-a3f9",  # 格式错误
            "kb-20250330",  # 缺少部分
            "",
        ]

        for invalid_id in invalid_ids:
            assert parse_note_id(invalid_id) is None

    def test_note_id_sortable(self):
        """测试 ID 可按时间排序."""
        ids = [
            NoteId.from_string("kb-20250330-100000-a001"),
            NoteId.from_string("kb-20250330-143052-a3f9"),
            NoteId.from_string("kb-20250330-090000-b002"),
        ]

        sorted_ids = sorted(ids, key=lambda x: x.to_datetime())

        assert sorted_ids[0].time == "090000"
        assert sorted_ids[1].time == "100000"
        assert sorted_ids[2].time == "143052"

    def test_note_id_from_datetime(self):
        """测试从 datetime 创建 NoteId."""
        dt = datetime(2025, 3, 30, 14, 30, 52)
        note_id = NoteId.from_datetime(dt, random_code="test")

        assert note_id.date == "20250330"
        assert note_id.time == "143052"
        assert note_id.random == "test"
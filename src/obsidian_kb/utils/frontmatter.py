"""Frontmatter 解析器模块.

解析和处理 Obsidian 笔记的 YAML frontmatter。
支持所有笔记类型：project, research, brainstorm, moc, daily-note, archive.
"""
import re
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from obsidian_kb.utils.id_generator import generate_note_id


@dataclass
class Frontmatter:
    """Frontmatter 数据类."""

    # 核心必需字段
    id: str
    title: str
    type: str
    date: str

    # 时间戳字段
    created: Optional[str] = None
    updated: Optional[str] = None

    # 通用字段
    tags: List[str] = field(default_factory=list)

    # 扩展字段
    status: Optional[str] = None
    area: Optional[str] = None
    mocs: List[str] = field(default_factory=list)
    related_project: Optional[str] = None

    # 其他字段存储
    extra: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        """动态访问 extra 字段.

        Args:
            name: 字段名

        Returns:
            字段值

        Raises:
            AttributeError: 字段不存在
        """
        if name in self.extra:
            return self.extra[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            包含所有字段的字典
        """
        result = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "date": self.date,
        }

        # 添加可选字段
        if self.created:
            result["created"] = self.created
        if self.updated:
            result["updated"] = self.updated
        if self.tags:
            result["tags"] = self.tags
        if self.status:
            result["status"] = self.status
        if self.area:
            result["area"] = self.area
        if self.mocs:
            result["mocs"] = self.mocs
        if self.related_project:
            result["related_project"] = self.related_project

        # 添加额外字段
        result.update(self.extra)

        return result

    def to_yaml(self) -> str:
        """转换为 YAML 字符串.

        Returns:
            YAML 格式的 frontmatter（不含 --- 边界）
        """
        data = self.to_dict()
        return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def __str__(self) -> str:
        """转换为完整的 frontmatter 格式.

        Returns:
            包含 --- 边界的完整 frontmatter
        """
        return f"---\n{self.to_yaml()}---\n"


def find_frontmatter_bounds(content: str) -> Optional[Tuple[int, int]]:
    """查找 frontmatter 的边界位置.

    Args:
        content: 笔记内容

    Returns:
        (start, end) 元组，表示 frontmatter 的起始和结束位置
        如果没有找到返回 None
    """
    # frontmatter 必须在文件开头
    if not content.startswith("---"):
        return None

    # 查找第二个 ---
    # 第一个 --- 在位置 0，所以从位置 4 开始查找
    second_marker = content.find("\n---", 3)
    if second_marker == -1:
        return None

    # 返回边界：从第一个 --- 到第二个 --- 之后
    start = 0
    end = second_marker + 4  # 包含 "---\n"

    return (start, end)


def parse_frontmatter(content: str) -> Optional[Frontmatter]:
    """解析 frontmatter.

    Args:
        content: 笔记内容

    Returns:
        Frontmatter 实例，如果没有 frontmatter 返回 None

    Raises:
        ValueError: YAML 解析失败
    """
    bounds = find_frontmatter_bounds(content)
    if bounds is None:
        return None

    start, end = bounds

    # 提取 YAML 内容（去除 --- 边界）
    yaml_content = content[start + 4:end - 4].strip()

    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")

    # 解析必需字段
    id_val = data.get("id")
    title = data.get("title")
    type_val = data.get("type")
    date = data.get("date")

    if not all([id_val, title, type_val, date]):
        raise ValueError("Missing required fields: id, title, type, date")

    # 解析可选字段
    created = data.get("created")
    updated = data.get("updated")
    tags = data.get("tags", [])
    status = data.get("status")
    area = data.get("area")
    mocs = data.get("mocs", [])
    related_project = data.get("related_project")

    # 收集额外字段
    known_fields = {
        "id", "title", "type", "date", "created", "updated",
        "tags", "status", "area", "mocs", "related_project"
    }
    extra = {k: v for k, v in data.items() if k not in known_fields}

    return Frontmatter(
        id=str(id_val),
        title=str(title),
        type=str(type_val),
        date=str(date),
        created=str(created) if created else None,
        updated=str(updated) if updated else None,
        tags=list(tags) if tags else [],
        status=str(status) if status else None,
        area=str(area) if area else None,
        mocs=list(mocs) if mocs else [],
        related_project=str(related_project) if related_project else None,
        extra=extra
    )


def extract_frontmatter(content: str) -> Tuple[Optional[Frontmatter], str]:
    """提取 frontmatter 和正文.

    Args:
        content: 笔记内容

    Returns:
        (Frontmatter, body) 元组
        如果没有 frontmatter，返回 (None, content)
    """
    bounds = find_frontmatter_bounds(content)
    if bounds is None:
        return (None, content)

    start, end = bounds
    fm = parse_frontmatter(content)
    body = content[end:].strip()

    return (fm, body)


def update_frontmatter(content: str, updates: Dict[str, Any]) -> str:
    """更新 frontmatter 字段.

    Args:
        content: 笔记内容
        updates: 要更新的字段字典

    Returns:
        更新后的笔记内容

    Raises:
        ValueError: 没有找到 frontmatter
    """
    bounds = find_frontmatter_bounds(content)
    if bounds is None:
        raise ValueError("No frontmatter found in content")

    start, end = bounds

    # 解析现有 frontmatter
    fm = parse_frontmatter(content)
    if fm is None:
        raise ValueError("Failed to parse frontmatter")

    # 应用更新
    data = fm.to_dict()
    data.update(updates)

    # 生成新的 YAML
    new_yaml = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_frontmatter = f"---\n{new_yaml}---\n"

    # 提取正文并组合
    body = content[end:].strip()

    return new_frontmatter + "\n" + body


def create_frontmatter(
    note_type: str,
    title: str,
    area: str,
    date: str,
    **kwargs
) -> Frontmatter:
    """创建标准 frontmatter.

    Args:
        note_type: 笔记类型 (project, research, brainstorm, moc, daily-note, archive)
        title: 笔记标题
        area: 领域标签
        date: 日期字符串
        **kwargs: 其他可选字段

    Returns:
        Frontmatter 实例
    """
    # 生成 ID
    note_id = generate_note_id()

    # 根据类型设置默认值
    default_tags = get_default_tags(note_type, area)
    default_status = get_default_status(note_type)

    # 时间戳
    now = datetime.now()
    created = kwargs.get("created", now.strftime("%Y-%m-%d %H:%M"))

    # 合合用户提供的字段
    tags = kwargs.get("tags", default_tags)
    status = kwargs.get("status", default_status)

    return Frontmatter(
        id=note_id,
        title=title,
        type=note_type,
        date=date,
        created=created,
        updated=created,
        tags=tags,
        status=status,
        area=area,
        mocs=kwargs.get("mocs", []),
        related_project=kwargs.get("related_project"),
        extra=kwargs.get("extra", {})
    )


def get_default_tags(note_type: str, area: str) -> List[str]:
    """根据笔记类型获取默认标签.

    Args:
        note_type: 笔记类型
        area: 领域

    Returns:
        默认标签列表
    """
    type_tags = {
        "project": ["项目"],
        "research": ["研究"],
        "brainstorm": ["头脑风暴"],
        "moc": ["MOC"],
        "daily-note": ["日记"],
        "knowledge": ["知识"],
        "archive": ["归档"],
    }

    tags = type_tags.get(note_type, [])
    if area:
        tags.append(area)

    return tags


def get_default_status(note_type: str) -> str:
    """根据笔记类型获取默认状态.

    Args:
        note_type: 笔记类型

    Returns:
        默认状态字符串
    """
    status_map = {
        "project": "进行中",
        "research": "进行中",
        "brainstorm": "活跃",
        "moc": "活跃",
        "daily-note": "当日",
        "knowledge": "进行中",
        "archive": "已完成",
    }

    return status_map.get(note_type, "进行中")
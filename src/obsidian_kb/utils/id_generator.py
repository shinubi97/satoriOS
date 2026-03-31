"""笔记 ID 生成器模块.

生成唯一、可排序的笔记 ID。
格式: kb-YYYYMMDD-HHMMSS-XXXX (时间戳 + 4位随机码)

优势:
- 并发安全：无需读取现有文件
- 可排序：按时间顺序排列
- 简洁：固定长度，易于存储和引用
"""
import random
import string
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


# ID 格式常量
ID_PREFIX = "kb"
ID_FORMAT = "{prefix}-{date}-{time}-{random}"
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M%S"
RANDOM_LENGTH = 4


@dataclass
class NoteId:
    """笔记 ID 数据类."""

    prefix: str
    date: str  # YYYYMMDD
    time: str  # HHMMSS
    random: str  # 4位随机码

    @classmethod
    def from_string(cls, id_str: str) -> Optional["NoteId"]:
        """从字符串解析 ID.

        Args:
            id_str: 格式为 "kb-YYYYMMDD-HHMMSS-XXXX" 的字符串

        Returns:
            NoteId 实例，如果格式无效返回 None
        """
        parts = id_str.split("-")
        if len(parts) != 4:
            return None

        prefix, date, time, random_code = parts

        # 验证各部分格式
        if prefix != ID_PREFIX:
            return None
        if len(date) != 8 or not date.isdigit():
            return None
        if len(time) != 6 or not time.isdigit():
            return None
        if len(random_code) != RANDOM_LENGTH:
            return None

        return cls(prefix=prefix, date=date, time=time, random=random_code)

    @classmethod
    def from_datetime(cls, dt: datetime, random_code: Optional[str] = None) -> "NoteId":
        """从 datetime 创建 ID.

        Args:
            dt: datetime 实例
            random_code: 可选的随机码，默认自动生成

        Returns:
            NoteId 实例
        """
        if random_code is None:
            random_code = _generate_random_code()

        return cls(
            prefix=ID_PREFIX,
            date=dt.strftime(DATE_FORMAT),
            time=dt.strftime(TIME_FORMAT),
            random=random_code
        )

    def to_datetime(self) -> datetime:
        """转换为 datetime.

        Returns:
            datetime 实例（忽略随机码）
        """
        date_str = f"{self.date}{self.time}"
        return datetime.strptime(date_str, "%Y%m%d%H%M%S")

    def __str__(self) -> str:
        """转换为字符串格式."""
        return ID_FORMAT.format(
            prefix=self.prefix,
            date=self.date,
            time=self.time,
            random=self.random
        )

    def __repr__(self) -> str:
        return f"NoteId('{str(self)}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, NoteId):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


def _generate_random_code(length: int = RANDOM_LENGTH) -> str:
    """生成随机码.

    使用小写字母和数字，避免混淆字符（0/o, 1/l）。

    Args:
        length: 随机码长度

    Returns:
        随机字符串
    """
    # 使用不含混淆字符的字符集
    chars = string.ascii_lowercase.replace('o', '') + string.digits.replace('0', '').replace('1', '')
    return ''.join(random.choices(chars, k=length))


def generate_note_id(dt: Optional[datetime] = None) -> str:
    """生成唯一的笔记 ID.

    Args:
        dt: 可选的 datetime，默认使用当前时间

    Returns:
        格式为 "kb-YYYYMMDD-HHMMSS-XXXX" 的字符串
    """
    if dt is None:
        dt = datetime.now()

    note_id = NoteId.from_datetime(dt)
    return str(note_id)


def parse_note_id(id_str: str) -> Optional[NoteId]:
    """解析笔记 ID.

    Args:
        id_str: ID 字符串

    Returns:
        NoteId 实例，如果格式无效返回 None
    """
    return NoteId.from_string(id_str)


def is_valid_note_id(id_str: str) -> bool:
    """检查 ID 是否有效.

    Args:
        id_str: ID 字符串

    Returns:
        True 如果格式有效
    """
    return parse_note_id(id_str) is not None
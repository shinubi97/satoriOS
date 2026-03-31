"""研究笔记工作流.

创建研究笔记，支持不同研究深度。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, create_frontmatter


@dataclass
class ResearchDetails:
    """研究笔记详情。"""
    topic: str
    area: str
    depth: str  # "快速了解" | "深入学习" | "精通掌握"
    existing_research: Optional[str] = None


class ResearchWorkflow(BaseWorkflow):
    """研究笔记工作流。

    创建研究笔记，可选不同研究深度。

    工作流程：
    1. 检查是否已存在相同主题研究
    2. 创建研究笔记
    3. 返回结果，包含 MOC 链接建议
    """

    DEPTH_LEVELS = {
        "快速了解": {
            "description": "快速概览，了解基本概念",
            "sections": ["核心概念", "快速入门", "参考资料"]
        },
        "深入学习": {
            "description": "系统学习，掌握核心知识",
            "sections": ["核心概念", "详细说明", "实践笔记", "学习资源"]
        },
        "精通掌握": {
            "description": "全面精通，能够实践应用",
            "sections": ["核心概念", "深入原理", "最佳实践", "进阶主题", "项目实战"]
        }
    }

    def execute(
        self,
        topic: str,
        area: str = None,
        depth: str = "深入学习",
        link_to_moc: str = None
    ) -> WorkflowResult:
        """创建研究笔记。

        Args:
            topic: 研究主题
            area: 所属领域
            depth: 研究深度 ("快速了解" | "深入学习" | "精通掌握")
            link_to_moc: 要链接的 MOC 名称

        Returns:
            WorkflowResult 包含创建的研究笔记信息
        """
        # 确定领域
        area = self._ensure_area(area)

        # 标准化深度
        depth = self._normalize_depth(depth)

        # 1. 检查是否已存在
        existing = self._check_existing_research(topic, area)

        if existing:
            return WorkflowResult(
                success=True,
                message=f"已存在相关研究: {existing}",
                suggestions=["继续现有研究", "创建新研究笔记"],
                data={
                    "existing_research": existing,
                    "topic": topic,
                    "area": area
                }
            )

        # 2. 创建研究笔记
        note_path = self._create_research_note(topic, area, depth)

        if not note_path:
            return WorkflowResult(
                success=False,
                message=f"创建研究笔记失败: {topic}",
                suggestions=["检查目录权限"]
            )

        # 3. 构建结果
        suggestions = []
        if link_to_moc:
            suggestions.append(f"已链接到 MOC: {link_to_moc}")
        else:
            suggestions.append(f"考虑链接到 MOC: moc-{area}")

        details = ResearchDetails(
            topic=topic,
            area=area,
            depth=depth
        )

        return WorkflowResult(
            success=True,
            message=f"✅ 研究笔记已创建: {topic}",
            created_files=[note_path],
            suggestions=suggestions,
            data={
                "research": details,
                "note_path": note_path,
                "depth_config": self.DEPTH_LEVELS.get(depth, {})
            }
        )

    def _normalize_depth(self, depth: str) -> str:
        """标准化深度级别。

        Args:
            depth: 输入的深度描述

        Returns:
            标准化的深度级别
        """
        depth_lower = depth.lower()

        # 映射各种表达方式
        quick_keywords = ["快速", "概览", "了解", "入门", "quick", "overview"]
        deep_keywords = ["深入", "系统", "学习", "deep", "learn"]
        master_keywords = ["精通", "掌握", "专家", "master", "expert"]

        for kw in quick_keywords:
            if kw in depth_lower:
                return "快速了解"

        for kw in master_keywords:
            if kw in depth_lower:
                return "精通掌握"

        return "深入学习"  # 默认

    def _check_existing_research(self, topic: str, area: str) -> Optional[str]:
        """检查是否已存在相关研究。

        Args:
            topic: 研究主题
            area: 领域

        Returns:
            已存在的研究笔记路径，如果不存在返回 None
        """
        research_path = self.vault.path / "30_研究" / area

        if not research_path.exists():
            return None

        topic_lower = topic.lower()

        for md_file in research_path.glob("*.md"):
            file_name_lower = md_file.stem.lower()
            if topic_lower in file_name_lower or file_name_lower in topic_lower:
                return str(md_file.relative_to(self.vault.path))

        return None

    def _create_research_note(
        self,
        topic: str,
        area: str,
        depth: str
    ) -> Optional[str]:
        """创建研究笔记。

        Args:
            topic: 研究主题
            area: 领域
            depth: 深度级别

        Returns:
            创建的笔记路径
        """
        # 确保目录存在
        research_path = self.vault.path / "30_研究" / area
        research_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        today = date.today().strftime("%Y-%m-%d")
        safe_topic = self._sanitize_filename(topic)
        filename = f"{safe_topic}_{today}.md"

        note_file = research_path / filename

        # 如果文件已存在，添加时间戳
        counter = 1
        while note_file.exists():
            filename = f"{safe_topic}_{today}_{counter}.md"
            note_file = research_path / filename
            counter += 1

        # 获取深度配置
        depth_config = self.DEPTH_LEVELS.get(depth, self.DEPTH_LEVELS["深入学习"])
        sections = depth_config.get("sections", [])

        # 生成 frontmatter
        fm_obj = create_frontmatter(
            note_type="research",
            title=f"{topic} 研究笔记",
            area=area,
            date=today
        )

        # 构建内容
        sections_content = "\n\n".join(f"## {s}\n\n" for s in sections)

        content = f"""{fm_obj}
# {topic} 研究笔记

> 研究领域: {area} | 开始日期: {today}

---

## 研究概述

{depth_config.get('description', '')}

{sections_content}
## 学习资源

### 文章/教程
- [ ] ...

### 视频
- [ ] ...

## 核心知识提取

已提取到知识库:
- [[知识点 1]]

## 下一步行动

- [ ] ...

## 研究总结

（研究完成后填写）
"""

        try:
            note_file.write_text(content, encoding="utf-8")
            return str(note_file.relative_to(self.vault.path))
        except Exception:
            return None

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名中的特殊字符。"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()[:100]
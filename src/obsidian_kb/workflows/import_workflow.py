"""外部内容导入工作流.

从外部来源导入内容到知识库。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import re

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter, create_frontmatter


@dataclass
class ImportContent:
    """导入内容结构。"""
    source: str  # twitter, web, github, rss, local, skill
    title: str
    content: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    type_hint: Optional[str] = None  # article, tutorial, snippet, knowledge
    area_hint: Optional[str] = None


@dataclass
class ImportResult:
    """导入结果。"""
    note_path: str
    note_type: str
    area: str
    source: str


class ImportWorkflow(BaseWorkflow):
    """外部内容导入工作流。

    从外部来源导入内容到知识库。

    工作流程：
    1. 解析输入内容（JSON 或纯文本）
    2. 分析内容类型和存放位置
    3. 创建笔记
    4. 建议链接到 MOC
    """

    # 存放位置映射
    LOCATION_MAP = {
        "inbox": "00_收件箱",
        "research": "30_研究",
        "knowledge": "40_知识库",
        "project": "10_项目"
    }

    def execute(
        self,
        content: str,
        content_type: str = None,
        area: str = None
    ) -> WorkflowResult:
        """导入外部内容。

        Args:
            content: 外部内容（JSON 格式或纯文本）
            content_type: 内容类型提示
            area: 所属领域

        Returns:
            WorkflowResult 包含导入结果
        """
        # 1. 解析输入
        import_content = self._parse_input(content, content_type, area)

        if not import_content:
            return WorkflowResult(
                success=False,
                message="无法解析导入内容",
                suggestions=["检查内容格式是否正确"]
            )

        # 2. 分析存放位置
        location, note_type = self._analyze_location(import_content)
        target_area = import_content.area_hint or area or self._infer_area(import_content)
        target_area = self._ensure_area(target_area)

        # 3. 创建笔记
        note_path = self._create_note(
            import_content=import_content,
            location=location,
            note_type=note_type,
            area=target_area
        )

        if not note_path:
            return WorkflowResult(
                success=False,
                message="创建笔记失败",
                suggestions=["检查目录权限"]
            )

        result = ImportResult(
            note_path=note_path,
            note_type=note_type,
            area=target_area,
            source=import_content.source
        )

        return WorkflowResult(
            success=True,
            message=f"✅ 内容已导入: {import_content.title}",
            created_files=[note_path],
            suggestions=[
                f"已保存到: {note_path}",
                f"建议链接到 [[moc-{target_area}]]"
            ],
            data={
                "import": result
            }
        )

    def _parse_input(
        self,
        content: str,
        content_type: str = None,
        area: str = None
    ) -> Optional[ImportContent]:
        """解析输入内容。

        Args:
            content: 输入内容
            content_type: 内容类型
            area: 领域

        Returns:
            解析后的 ImportContent
        """
        # 尝试解析 JSON
        try:
            data = json.loads(content)
            return ImportContent(
                source=data.get("source", "unknown"),
                title=data.get("title", "未命名"),
                content=data.get("content", ""),
                source_url=data.get("source_url"),
                author=data.get("author"),
                date=data.get("date"),
                tags=data.get("tags", []),
                type_hint=data.get("type_hint") or content_type,
                area_hint=data.get("area_hint") or area
            )
        except json.JSONDecodeError:
            pass

        # 纯文本格式解析
        lines = content.strip().split("\n")
        if not lines:
            return None

        # 第一行作为标题
        title = lines[0].strip()
        if title.startswith("标题:"):
            title = title[3:].strip()

        # 剩余作为正文
        body = "\n".join(lines[1:]).strip()
        if body.startswith("正文:"):
            body = body[3:].strip()

        return ImportContent(
            source="text",
            title=title or "未命名笔记",
            content=body or content,
            type_hint=content_type,
            area_hint=area
        )

    def _analyze_location(
        self,
        import_content: ImportContent
    ) -> tuple:
        """分析存放位置。

        Args:
            import_content: 导入内容

        Returns:
            (location, note_type)
        """
        content_length = len(import_content.content)
        type_hint = import_content.type_hint

        # 根据类型提示决定
        if type_hint == "article" or type_hint == "tutorial":
            return "research", "research"
        elif type_hint == "knowledge":
            return "knowledge", "knowledge"
        elif type_hint == "snippet":
            return "inbox", "idea"

        # 根据内容长度判断
        if content_length < 500:
            # 短内容 -> 收件箱
            return "inbox", "idea"
        elif content_length < 2000:
            # 中等内容 -> 知识库
            return "knowledge", "knowledge"
        else:
            # 长内容 -> 研究
            return "research", "research"

    def _infer_area(self, import_content: ImportContent) -> str:
        """从内容推断领域。

        Args:
            import_content: 导入内容

        Returns:
            推断的领域
        """
        content_lower = import_content.content.lower()
        title_lower = import_content.title.lower()

        # 关键词映射
        area_keywords = {
            "编程": ["python", "javascript", "code", "编程", "代码", "开发", "api", "函数"],
            "工作": ["工作", "会议", "项目", "报告", "任务", "管理"],
            "学习": ["学习", "课程", "教程", "笔记", "复习"],
            "生活": ["生活", "健康", "运动", "饮食", "旅行"],
            "阅读": ["阅读", "书籍", "读书", "文章", "书评"]
        }

        for area, keywords in area_keywords.items():
            for kw in keywords:
                if kw in content_lower or kw in title_lower:
                    return area

        return "通用"

    def _create_note(
        self,
        import_content: ImportContent,
        location: str,
        note_type: str,
        area: str
    ) -> Optional[str]:
        """创建笔记。

        Args:
            import_content: 导入内容
            location: 存放位置
            note_type: 笔记类型
            area: 领域

        Returns:
            创建的笔记路径
        """
        # 确定目录
        if location == "inbox":
            target_dir = self.vault.path / "00_收件箱"
        elif location == "research":
            target_dir = self.vault.path / "30_研究" / area
        elif location == "knowledge":
            target_dir = self.vault.path / "40_知识库" / area
        else:
            target_dir = self.vault.path / "00_收件箱"

        target_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        today = date.today().strftime("%Y-%m-%d")
        safe_title = self._sanitize_filename(import_content.title)
        filename = f"{safe_title}_{today}.md"

        note_file = target_dir / filename

        # 处理文件名冲突
        counter = 1
        while note_file.exists():
            filename = f"{safe_title}_{today}_{counter}.md"
            note_file = target_dir / filename
            counter += 1

        # 生成 frontmatter
        fm_obj = create_frontmatter(
            note_type=note_type,
            title=import_content.title,
            area=area,
            date=today
        )

        # 构建内容
        source_info = ""
        if import_content.source_url:
            source_info = f"\n> 来源: [{import_content.source}]({import_content.source_url})"
        elif import_content.source:
            source_info = f"\n> 来源: {import_content.source}"

        author_info = ""
        if import_content.author:
            author_info = f"\n> 作者: {import_content.author}"

        tags_section = ""
        if import_content.tags:
            tags_str = ", ".join(f"#{tag}" for tag in import_content.tags)
            tags_section = f"\n\n标签: {tags_str}"

        content = f"""{fm_obj}
# {import_content.title}
{source_info}{author_info}{tags_section}

---

{import_content.content}
"""

        try:
            note_file.write_text(content, encoding="utf-8")
            return str(note_file.relative_to(self.vault.path))
        except Exception:
            return None

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名。"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()[:100]

    def import_from_url(
        self,
        url: str,
        area: str = None
    ) -> WorkflowResult:
        """从 URL 导入内容。

        Args:
            url: 来源 URL
            area: 领域

        Returns:
            导入结果
        """
        # 提取来源类型
        source = self._detect_source_from_url(url)

        import_content = ImportContent(
            source=source,
            title="从URL导入的内容",
            content=f"待获取内容\n\n来源: {url}",
            source_url=url,
            area_hint=area
        )

        return self.execute(
            content=json.dumps({
                "source": import_content.source,
                "title": import_content.title,
                "content": import_content.content,
                "source_url": import_content.source_url,
                "area_hint": import_content.area_hint
            }),
            area=area
        )

    def _detect_source_from_url(self, url: str) -> str:
        """从 URL 检测来源类型。"""
        url_lower = url.lower()

        if "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "github.com" in url_lower:
            return "github"
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        else:
            return "web"
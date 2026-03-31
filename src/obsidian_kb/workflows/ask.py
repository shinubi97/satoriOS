"""问答工作流.

基于知识库内容回答问题。
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult
from obsidian_kb.utils.frontmatter import parse_frontmatter
from obsidian_kb.parser import MarkdownParser


@dataclass
class SearchResult:
    """搜索结果。"""
    path: str
    title: str
    relevance: float
    snippet: str
    highlights: List[str] = field(default_factory=list)


@dataclass
class AskResult:
    """问答结果。"""
    question: str
    answer: str
    sources: List[SearchResult]
    confidence: str  # "high", "medium", "low"


class AskWorkflow(BaseWorkflow):
    """问答工作流。

    基于知识库内容回答问题。

    工作流程：
    1. 解析问题关键词
    2. 搜索相关笔记
    3. 排序和筛选结果
    4. 构建回答
    5. 返回结果和来源
    """

    def execute(
        self,
        question: str,
        max_results: int = 5
    ) -> WorkflowResult:
        """回答问题。

        Args:
            question: 用户问题
            max_results: 最大返回结果数

        Returns:
            WorkflowResult 包含回答和来源
        """
        # 1. 提取关键词
        keywords = self._extract_keywords(question)

        if not keywords:
            return WorkflowResult(
                success=False,
                message="无法从问题中提取关键词",
                suggestions=["尝试更具体的问题"]
            )

        # 2. 搜索相关笔记
        search_results = self._search_notes(keywords, max_results * 2)

        if not search_results:
            return WorkflowResult(
                success=True,
                message="在知识库中未找到相关内容",
                suggestions=[
                    "尝试不同的关键词",
                    "创建相关研究笔记"
                ],
                data={
                    "ask": AskResult(
                        question=question,
                        answer="知识库中没有找到相关信息。",
                        sources=[],
                        confidence="low"
                    )
                }
            )

        # 3. 排序结果
        sorted_results = self._rank_results(search_results, keywords)[:max_results]

        # 4. 构建回答
        answer = self._build_answer(question, sorted_results)

        ask_result = AskResult(
            question=question,
            answer=answer,
            sources=sorted_results,
            confidence=self._assess_confidence(sorted_results)
        )

        return WorkflowResult(
            success=True,
            message="✅ 找到相关内容",
            suggestions=[
                f"查看 [[{r.title}]] 了解更多" for r in sorted_results[:3]
            ],
            data={
                "ask": ask_result
            }
        )

    def _extract_keywords(self, question: str) -> List[str]:
        """从问题提取关键词。

        Args:
            question: 用户问题

        Returns:
            关键词列表
        """
        # 简单的关键词提取
        # 移除常见问题词
        stop_words = {
            "的", "是", "在", "有", "和", "了", "吗", "呢", "什么", "怎么",
            "如何", "为什么", "哪", "谁", "多少", "几", "可以", "能", "会"
        }

        # 分词（简单按空格和标点分割）
        import re
        words = re.split(r'[\s，。？！、；：""''（）【】]+', question)

        # 过滤关键词
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word.lower())

        return keywords

    def _search_notes(
        self,
        keywords: List[str],
        max_results: int
    ) -> List[SearchResult]:
        """搜索笔记，使用多因素评分。

        Args:
            keywords: 关键词列表
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        results = []

        # 搜索所有 .md 文件
        for md_file in self.vault.path.rglob("*.md"):
            # 跳过归档目录
            if "50_归档" in str(md_file):
                continue

            try:
                content = md_file.read_text(encoding="utf-8")

                # 提取标题
                fm_obj = parse_frontmatter(content)
                title = fm_obj.title if fm_obj else md_file.stem

                # 多因素相关性评分
                relevance = 0.0
                highlights = []

                for keyword in keywords:
                    kw_lower = keyword.lower()

                    # 标题匹配 (权重: 2.0) - 标题中的关键词更重要
                    if kw_lower in title.lower():
                        relevance += 2.0
                        highlights.append(keyword)

                    # 内容频率 (权重: 0.1)
                    count = content.lower().count(kw_lower)
                    if count > 0:
                        relevance += count * 0.1
                        if keyword not in highlights:
                            highlights.append(keyword)

                    # 标题匹配 (权重: 0.5) - 标题行中包含关键词
                    for line in content.split('\n'):
                        if line.startswith('#') and kw_lower in line.lower():
                            relevance += 0.5
                            break

                if relevance > 0:
                    # 归一化到 0-1
                    relevance = min(relevance / 10, 1.0)

                    # 提取摘要
                    snippet = self._extract_snippet(content, keywords)

                    results.append(SearchResult(
                        path=str(md_file.relative_to(self.vault.path)),
                        title=title,
                        relevance=relevance,
                        snippet=snippet,
                        highlights=highlights
                    ))

            except Exception:
                continue

        # 按相关性排序
        results.sort(key=lambda x: x.relevance, reverse=True)

        return results[:max_results]

    def _extract_snippet(
        self,
        content: str,
        keywords: List[str],
        length: int = 200
    ) -> str:
        """提取包含关键词的摘要。

        Args:
            content: 笔记内容
            keywords: 关键词列表
            length: 摘要长度

        Returns:
            摘要文本
        """
        # 去除 frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        # 找到第一个匹配的关键词位置
        best_pos = -1
        for keyword in keywords:
            pos = content.lower().find(keyword.lower())
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos

        if best_pos == -1:
            return content[:length].strip()

        # 提取上下文
        start = max(0, best_pos - 50)
        end = min(len(content), best_pos + length - 50)

        snippet = content[start:end].strip()

        # 添加省略号
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

        # 添加省略号
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _rank_results(
        self,
        results: List[SearchResult],
        keywords: List[str]
    ) -> List[SearchResult]:
        """排序搜索结果。

        Args:
            results: 搜索结果
            keywords: 关键词

        Returns:
            排序后的结果
        """
        # 已经在搜索时按相关性排序
        # 这里可以添加额外的排序因素
        return results

    def _build_answer(
        self,
        question: str,
        results: List[SearchResult]
    ) -> str:
        """构建回答。

        Args:
            question: 用户问题
            results: 搜索结果

        Returns:
            回答文本
        """
        if not results:
            return "知识库中没有找到相关信息。"

        # 构建摘要回答
        parts = []

        if len(results) == 1:
            parts.append(f"在 [[{results[0].title}]] 中找到了相关内容：")
        else:
            titles = [f"[[{r.title}]]" for r in results[:3]]
            parts.append(f"在 {', '.join(titles)} 等笔记中找到了相关内容。")

        # 添加摘要
        parts.append("\n" + results[0].snippet)

        return "\n".join(parts)

    def _assess_confidence(self, results: List[SearchResult]) -> str:
        """评估回答置信度。

        Args:
            results: 搜索结果

        Returns:
            置信度级别
        """
        if not results:
            return "low"

        top_relevance = results[0].relevance

        if top_relevance >= 0.7:
            return "high"
        elif top_relevance >= 0.3:
            return "medium"
        else:
            return "low"
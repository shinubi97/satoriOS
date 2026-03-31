"""Open note workflow - display any note using Obsidian CLI native capabilities."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import subprocess

from obsidian_kb.workflows.base import BaseWorkflow, WorkflowResult


@dataclass
class NoteDetail:
    """Note detail for open command."""
    path: str
    title: str
    note_type: str
    area: str
    status: str
    content_preview: str
    headings: List[str] = field(default_factory=list)
    outgoing_links: List[str] = field(default_factory=list)
    backlinks: List[str] = field(default_factory=list)


class OpenWorkflow(BaseWorkflow):
    """Open any note using Obsidian CLI native capabilities.

    Uses Obsidian CLI commands:
    - obsidian search: Find notes by name
    - obsidian read: Read file contents
    - obsidian outline: Get headings
    - obsidian links: Get outgoing links
    - obsidian backlinks: Get incoming links
    """

    def execute(self, note_name: str) -> WorkflowResult:
        """Open a note and return its details.

        Args:
            note_name: Note name (supports fuzzy matching via Obsidian search)

        Returns:
            WorkflowResult with NoteDetail
        """
        # 1. Search for note using Obsidian CLI
        search_result = self._search_note(note_name)

        if not search_result:
            return WorkflowResult(
                success=False,
                message=f"笔记不存在: {note_name}",
                suggestions=["检查路径是否正确", "使用 /ask 搜索相关内容"]
            )

        # 2. Get note details using Obsidian CLI
        detail = self._build_note_detail(search_result)

        if not detail:
            return WorkflowResult(
                success=False,
                message=f"无法读取笔记: {search_result}",
                suggestions=["检查文件权限"]
            )

        return WorkflowResult(
            success=True,
            message=f"📄 {detail.title}",
            suggestions=self._generate_suggestions(detail),
            data={"note": detail}
        )

    def _run_obsidian(self, *args) -> Optional[str]:
        """Run obsidian CLI command and return output.

        Args:
            *args: Command arguments

        Returns:
            Command output or None on failure
        """
        try:
            result = subprocess.run(
                ["obsidian"] + list(args),
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def _search_note(self, name: str) -> Optional[str]:
        """Search for note using Obsidian CLI.

        Args:
            name: Note name to search

        Returns:
            Note path or None
        """
        # First try local search (always works regardless of Obsidian state)
        local_result = self._local_search(name)
        if local_result:
            return local_result

        # Then try Obsidian CLI search for potential enhancements
        output = self._run_obsidian("search", f"query={name}", "limit=1", "format=json")

        if output:
            try:
                results = json.loads(output)
                if results and len(results) > 0:
                    # Obsidian search returns list of paths
                    result_path = results[0] if isinstance(results[0], str) else results[0].get("path")
                    # Check if this is an error message
                    if result_path and "not found" not in result_path.lower() and "error" not in result_path.lower():
                        return result_path
            except json.JSONDecodeError:
                # Fallback: try to parse as plain text
                lines = output.strip().split('\n')
                if lines and "not found" not in lines[0].lower():
                    return lines[0]

        return None

    def _local_search(self, name: str) -> Optional[str]:
        """Fallback local search when Obsidian CLI is unavailable.

        Args:
            name: Note name to search

        Returns:
            Note path or None
        """
        from pathlib import Path

        # First try exact path match
        exact_path = self.vault.path / name
        if exact_path.exists() and exact_path.suffix == '.md':
            return str(exact_path.relative_to(self.vault.path))

        # Try with .md extension
        if not name.endswith('.md'):
            exact_md = self.vault.path / (name + '.md')
            if exact_md.exists():
                return str(exact_md.relative_to(self.vault.path))

        # Then fuzzy match by filename
        name_lower = name.lower()
        matches = []

        for md_file in self.vault.path.rglob("*.md"):
            stem_lower = md_file.stem.lower()
            if name_lower in stem_lower:
                if stem_lower == name_lower:
                    return str(md_file.relative_to(self.vault.path))
                matches.append(str(md_file.relative_to(self.vault.path)))

        if matches:
            matches.sort(key=len)
            return matches[0]

        return None

    def _build_note_detail(self, note_path: str) -> Optional[NoteDetail]:
        """Build note detail using Obsidian CLI.

        Args:
            note_path: Path to note

        Returns:
            NoteDetail or None
        """
        from pathlib import Path

        # Read content using Obsidian CLI or fallback
        content = self._run_obsidian("read", f"file={note_path}")

        if not content or "not found" in (content or "").lower():
            # Fallback to local read
            try:
                full_path = self.vault.path / note_path
                if not full_path.exists():
                    return None
                content = full_path.read_text(encoding="utf-8")
            except Exception:
                return None

        # Parse frontmatter
        from obsidian_kb.utils.frontmatter import parse_frontmatter

        try:
            fm_obj = parse_frontmatter(content)
            fm = fm_obj.to_dict() if fm_obj else {}
        except (ValueError, Exception):
            # If parsing fails, use empty dict
            fm = {}

        # Extract body
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2].strip()

        # Preview
        preview = body[:500] + "..." if len(body) > 500 else body

        # Get headings using Obsidian CLI
        headings = []
        outline = self._run_obsidian("outline", f"file={note_path}", "format=json")
        if outline and "not found" not in outline.lower():
            try:
                outline_data = json.loads(outline)
                headings = [h.get("text", h) if isinstance(h, dict) else str(h) for h in outline_data[:5]]
            except json.JSONDecodeError:
                pass

        if not headings:
            # Fallback: extract from content
            for line in body.split("\n"):
                stripped = line.strip()
                if stripped.startswith("#"):
                    heading_text = stripped.lstrip("# ").strip()
                    if heading_text:
                        headings.append(heading_text)
            headings = headings[:5]

        # Get links using Obsidian CLI
        outgoing_links = []
        links_output = self._run_obsidian("links", f"file={note_path}")
        if links_output and "not found" not in links_output.lower():
            outgoing_links = [l.strip() for l in links_output.split('\n') if l.strip() and "not found" not in l.lower()][:10]

        # Fallback: extract links from content using regex
        if not outgoing_links:
            import re
            outgoing_links = re.findall(r'\[\[([^\]|]+)', body)
            outgoing_links = list(dict.fromkeys(outgoing_links))[:10]

        # Get backlinks using Obsidian CLI
        backlinks = []
        backlinks_output = self._run_obsidian("backlinks", f"file={note_path}", "format=json")
        if backlinks_output and "not found" not in backlinks_output.lower():
            try:
                bl_data = json.loads(backlinks_output)
                backlinks = [b.get("file", b) if isinstance(b, dict) else str(b) for b in bl_data[:5]]
            except json.JSONDecodeError:
                pass

        # Get title from path if not in frontmatter
        title = fm.get("title", Path(note_path).stem)

        return NoteDetail(
            path=note_path,
            title=title,
            note_type=fm.get("type", "note"),
            area=fm.get("area", ""),
            status=fm.get("status", ""),
            content_preview=preview,
            headings=headings,
            outgoing_links=outgoing_links,
            backlinks=backlinks
        )

    def _generate_suggestions(self, detail: NoteDetail) -> List[str]:
        """Generate suggestions based on note content."""
        suggestions = []

        if detail.note_type == "project":
            suggestions.append("使用 /review 查看项目详情")
        elif detail.note_type == "research":
            suggestions.append("使用 /research 继续研究")

        if detail.outgoing_links:
            suggestions.append(f"包含 {len(detail.outgoing_links)} 个外链")

        if detail.backlinks:
            suggestions.append(f"被 {len(detail.backlinks)} 个笔记引用")

        if detail.status:
            suggestions.append(f"当前状态: {detail.status}")

        return suggestions
# satoriOS

A Claude Code skill for Obsidian Knowledge Base management with PARA methodology.

## Overview

This skill provides comprehensive Obsidian knowledge base management capabilities:

- **Daily Planning**: Start your day with inbox review and project status
- **Project Management**: Kickoff new projects, track progress, archive completed work
- **Research Workflow**: Create research notes, extract knowledge
- **Brainstorming**: Facilitate brainstorming sessions with structured notes
- **MOC Management**: Manage Maps of Content for knowledge organization
- **Health Checks**: Detect orphans, dead links, and maintain knowledge base health

## Architecture

Based on PARA methodology:
- `00_收件箱/` - Inbox
- `10_项目/` - Projects
- `20_领域/` - Areas
- `30_研究/` - Research
- `40_知识库/` - Knowledge Base
- `50_归档/` - Archives

## Installation

```bash
# Install dependencies
pip install -e .

# Initialize configuration
obsidian-kb config init
```

## Commands

| Command | Description |
|---------|-------------|
| `/start-my-day` | Daily planning workflow |
| `/kickoff <name>` | Start new project |
| `/research <topic>` | Create research note |
| `/brainstorm <topic>` | Brainstorming session |
| `/archive <target>` | Archive notes |
| `/ask <question>` | Quick query |
| `/review [scope]` | Review status |
| `/health-check [type]` | Health check |
| `/mocs <subcmd>` | MOC management |
| `/moc-review` | MOC maintenance |
| `/import <content>` | Import external content |
| `/backup [target]` | Backup notes |
| `/restore [backup-id]` | Restore from backup |

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=obsidian_kb
```

## License

MIT
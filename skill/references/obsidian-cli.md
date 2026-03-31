# Obsidian CLI 使用指南

## 概述

Obsidian CLI 是 Obsidian 的命令行工具，用于与笔记库交互。本文档介绍常用命令和使用场景。

## 安装

```bash
# 通过 npm 安装
npm install -g obsidian

# 或使用 Homebrew (macOS)
brew install obsidian
```

## 基础命令

### 1. 打开笔记库

```bash
# 打开指定笔记库
obsidian open /path/to/vault

# 打开指定笔记
obsidian open /path/to/vault/note.md
```

### 2. 创建笔记

```bash
# 创建新笔记
obsidian create "笔记标题"

# 在指定文件夹创建
obsidian create "笔记标题" --folder="30_研究/编程"

# 使用模板创建
obsidian create "笔记标题" --template="templates/research.md"
```

### 3. 编辑笔记

```bash
# 追加内容
obsidian edit "笔记路径" --append="追加的内容"

# 追加多行内容
obsidian edit "笔记路径" --append="$(cat <<EOF
## 新章节

内容...
EOF
)"

# 替换内容
obsidian edit "笔记路径" --replace="旧内容" --with="新内容"
```

### 4. 搜索

```bash
# 搜索笔记内容
obsidian search "搜索词"

# 搜索文件名
obsidian search "文件名" --name-only

# 搜索标签
obsidian search "#标签"

# 搜索 frontmatter
obsidian search 'type: project' --frontmatter
```

### 5. 列出笔记

```bash
# 列出所有笔记
obsidian list

# 列出指定目录
obsidian list --folder="10_项目"

# 按标签过滤
obsidian list --tag="项目"

# 按类型过滤
obsidian list --type="project"
```

## 在工作流中使用

### 项目启动 (/kickoff)

```bash
# 1. 在收件箱中搜索想法
idea=$(obsidian search "想法名称" --folder="00_收件箱" --name-only)

# 2. 创建项目笔记
obsidian create "项目名称" \
  --folder="10_项目/领域" \
  --template="templates/project.md"

# 3. 移动原想法到归档
obsidian move "$idea" --destination="50_归档/$(date +%Y-%m)"
```

### 研究笔记 (/research)

```bash
# 检查是否已存在
obsidian search "主题" --folder="30_研究"

# 创建研究笔记
obsidian create "主题_研究笔记" \
  --folder="30_研究/领域" \
  --template="templates/research.md"
```

### 头脑风暴 (/brainstorm)

```bash
# 创建头脑风暴笔记
note_path=$(obsidian create "主题_头脑风暴" \
  --folder="30_研究/领域" \
  --template="templates/brainstorm.md")

# 多轮追加内容
obsidian edit "$note_path" --append="讨论内容..."

# 提取精华
obsidian edit "$note_path" --append="## 精华提取\n..."
```

### 每日规划 (/start-my-day)

```bash
# 获取今日日期
today=$(date +%Y-%m-%d)

# 检查今日笔记是否存在
if ! obsidian search "$today" --folder="Daily" --name-only; then
  # 创建今日笔记
  obsidian create "$today" \
    --folder="Daily" \
    --template="templates/daily.md"
fi

# 获取收件箱内容
obsidian list --folder="00_收件箱" --limit=5

# 获取进行中项目
obsidian search "status: 进行中" --frontmatter

# 获取未完成待办
obsidian search "- \[ \]" --folder="Daily" --limit=7
```

### 归档 (/archive)

```bash
# 移动到归档目录
archive_folder="50_归档/$(date +%Y-%m)"
obsidian move "笔记路径" --destination="$archive_folder"

# 更新 frontmatter 状态
obsidian edit "归档路径" --replace="status: 进行中" --with="status: 已完成"
```

## 高级用法

### 批量操作

```bash
# 批量添加标签
obsidian list --folder="10_项目" | while read note; do
  obsidian edit "$note" --append="\ntags: \n- 项目"
done

# 批量更新 frontmatter
obsidian list --type="project" | while read note; do
  obsidian edit "$note" --replace="status: 进行中" --with="status: 已归档"
done
```

### 与其他工具集成

```bash
# 使用 fzf 选择笔记
note=$(obsidian list | fzf)
obsidian open "$note"

# 使用 jq 处理 JSON 输出
obsidian search "关键词" --json | jq '.[].path'

# 与 ripgrep 集成
obsidian search "$(rg -l "内容" --type md)"
```

### 别名设置

在 `.zshrc` 或 `.bashrc` 中添加：

```bash
# Obsidian 快捷命令
alias ob='obsidian'
alias obn='obsidian create'  # new note
alias obe='obsidian edit'    # edit note
alias obs='obsidian search'  # search
alias obl='obsidian list'    # list notes

# 工作流快捷命令
alias today='obsidian open "$(date +%Y-%m-%d)" --folder="Daily"'
alias inbox='obsidian list --folder="00_收件箱"'
alias projects='obsidian list --folder="10_项目"'
```

## 常见问题

### Q: 如何在脚本中使用？

使用 `--json` 输出格式便于脚本处理：

```bash
# 获取笔记列表 JSON
notes=$(obsidian list --json)

# 使用 jq 处理
echo "$notes" | jq '.[] | .path'
```

### Q: 如何处理特殊字符？

使用引号包裹：

```bash
# 包含空格的文件名
obsidian open "My Note with spaces.md"

# 包含特殊字符的内容
obsidian edit "note.md" --append='Content with "quotes"'
```

### Q: 如何指定笔记库？

```bash
# 设置环境变量
export OBSIDIAN_VAULT="/path/to/vault"

# 或使用 --vault 参数
obsidian --vault="/path/to/vault" create "note"
```

## 参考链接

- Obsidian CLI 官方文档
- Obsidian API 文档
- 社区插件开发指南
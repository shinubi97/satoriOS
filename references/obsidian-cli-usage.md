# Obsidian CLI 使用指南

本技能依赖 Obsidian CLI 进行文件操作和链接查询。

## 安装

1. 打开 Obsidian 应用
2. 安装 "Obsidian CLI" 插件
3. 启用插件

## 常用命令

**注意**: CLI 参数使用 `key=value` 格式，不是 `key="value"`

### 文件操作

```bash
# 读取文件
obsidian read file=my-note

# 创建文件
obsidian create name="My Note" content="..."

# 追加内容
obsidian append file=my-note content="..."

# 移动文件
obsidian move file=my-note to=folder/new-name

# 删除文件
obsidian delete file=my-note
```

### 搜索

```bash
# 搜索内容
obsidian search query=关键词

# 按路径搜索
obsidian search query=Python path=10_项目

# 按标签搜索
obsidian search query=#进行中

# JSON 格式输出
obsidian search query=关键词 format=json
```

### 链接查询

```bash
# 反向链接（谁引用了我）
obsidian backlinks file=my-note format=json

# 出链（我引用了谁）
obsidian links file=my-note

# 死链（目标不存在）
obsidian unresolved format=json

# 孤儿笔记（没人引用我）
obsidian orphans
```

### 任务

```bash
# 获取待办任务
obsidian tasks todo

# 获取已完成任务
obsidian tasks done

# JSON 格式
obsidian tasks todo format=json
```

### 标签

```bash
# 列出所有标签
obsidian tags

# 标签统计
obsidian tags counts format=json
```

### 索引刷新

```bash
# 刷新 Vault 索引（直接文件操作后使用）
obsidian reload
```

### 属性操作

```bash
# 读取属性
obsidian property:read name=status file=my-note

# 设置属性
obsidian property:set name=status value=进行中 file=my-note

# 删除属性
obsidian property:remove name=status file=my-note
```

## 混合操作模式

本技能采用混合操作模式：

| 操作类型 | 实现方式 | 原因 |
|---------|---------|------|
| 文件读取 | CLI (`obsidian read`) | 利用 Obsidian 的文件解析 |
| 文件创建 | CLI (`obsidian create`) | 触发 Obsidian 索引更新 |
| 搜索/查询 | CLI (`obsidian search/backlinks/etc`) | 利用 Obsidian 的搜索索引 |
| 链接更新 | 直接文件操作 + `obsidian reload` | CLI 无原地替换能力，操作后需刷新索引 |
| 内容修改 | 直接文件操作 + `obsidian reload` | 精确控制，避免覆盖风险，操作后需刷新索引 |

**关键**: 直接文件操作后必须调用 `obsidian reload` 刷新索引，否则搜索和链接查询会返回过时结果。

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `CLI not available` | Obsidian 未运行 | 启动 Obsidian 应用 |
| `Vault not found` | 路径配置错误 | 运行 `obsidian-kb config init` |
| `Permission denied` | 权限不足 | 检查文件系统权限 |

## 本地后备模式

当 CLI 不可用时，技能会自动切换到本地文件操作模式：

- 使用 Python `pathlib` 进行文件操作
- 使用正则表达式解析链接
- 手动构建索引

**注意**: 本地模式功能有限，部分高级功能可能不可用。
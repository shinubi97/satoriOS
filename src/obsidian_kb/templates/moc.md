<!-- description: MOC (Map of Content) 模板 - 用于创建内容地图 -->

---
id: {{ id }}
title: '{{ title }} MOC'
type: moc
area: {{ area }}
date: '{{ date }}'
created: {{ created }}
updated: {{ updated }}
tags:
- MOC
- {{ area }}
status: 活跃
---

# {{ title }} MOC

> 领域: {{ area }} | 创建日期: {{ date }}

---

## 概述

{{ description }}

## 核心笔记

### 基础概念

- [[概念 1]]
- [[概念 2]]
- [[概念 3]]

### 核心主题

- [[主题 1]]
- [[主题 2]]

## 相关项目

{% for project in projects %}
- [[{{ project }}]]{% endfor %}

## 研究笔记

{% for research in researches %}
- [[{{ research }}]]{% endfor %}

## 头脑风暴

{% for brainstorm in brainstorms %}
- [[{{ brainstorm }}]]{% endfor %}

## 学习资源

### 教程

- [[教程 1]]
- [[教程 2]]

### 参考资料

- [[参考 1]]
- [[参考 2]]

## 实践案例

- [[案例 1]]
- [[案例 2]]

## 待探索

- [ ] 探索主题 1
- [ ] 探索主题 2
- [ ] 探索主题 3

## 关联 MOC

- [[相关 MOC 1]]
- [[相关 MOC 2]]

## 更新日志

### {{ date }}

- 创建 MOC

---

> 注: 此 MOC 由 Obsidian KB 自动维护，包含相关笔记的动态链接。
<!-- description: 项目启动模板 - 用于创建新项目笔记 -->

---
id: {{ id }}
title: {{ title }}
type: project
area: {{ area }}
date: '{{ date }}'
created: {{ created }}
updated: {{ updated }}
tags:
- 项目
- {{ area }}
status: 进行中
timeline: '{{ timeline }}'
---

# {{ title }}

{% if source %}> 来自: [[{{ source }}]]{% endif %}

---

## 项目目标

- [ ] 定义项目目标 1
- [ ] 定义项目目标 2

## 时间线

- **开始日期**: {{ date }}
- **目标完成**: {{ timeline }}

## 关键里程碑

- [ ] 里程碑 1: ...
- [ ] 里程碑 2: ...

## 进展记录

### {{ date }} - 项目启动

项目初始化，规划完成。

## 相关资源

- [[相关笔记]]
- [[参考资料]]

## 复盘总结

（项目完成后填写）

### 成功经验

-

### 待改进

-

### 下一步行动

- [ ] ...
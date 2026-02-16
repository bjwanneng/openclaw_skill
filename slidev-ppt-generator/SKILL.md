---
name: slidev-ppt-generator
description: 基于 Slidev 架构生成专业的代码驱动演示文稿。支持从长文章、大纲或文本自动生成结构化的 Slidev Markdown 文件，并提供导出 PDF/PPTX 的工作流。适用于技术分享、学术汇报、开发者演示等场景。当用户需要生成 PPT、创建演示文稿、将文章转为幻灯片、使用 Slidev 或代码驱动方式制作 PPT 时触发此技能。
---

# Slidev PPT 生成器

本 Skill 用于自动化生成基于 Slidev 的演示文稿。Slidev 是一个为开发者打造的演示文稿工具，使用 Markdown 编写，支持 Vue 组件和交互。

## 核心工作流

1. **内容解析**：将用户提供的文章或文本拆解为：
   - 标题与副标题
   - 核心章节大纲
   - 每页的要点（Bullets）
   - 代码块或图表（可选）

2. **生成 Markdown**：按照 Slidev 语法生成 `slides.md`。

3. **预览与调试**：运行 `npm run dev` 进行实时预览。

4. **导出**：使用 `npm run export` 导出为 PDF 或 PPTX。

## 快速开始

### 方式一：使用脚本自动生成（推荐）

```bash
# 1. 准备你的文章内容
export ARTICLE="你的长文章内容..."

# 2. 运行生成脚本
python /root/.openclaw/workspace/skills/slidev-ppt-generator/scripts/generate_slides.py "$ARTICLE"

# 3. 生成的 slides.md 会在当前目录
```

### 方式二：手动创建 Slidev 项目

```bash
# 1. 初始化项目
npm init slidev

# 2. 启动开发服务器
npm run dev

# 3. 编辑 slides.md 文件

# 4. 导出 PDF
npm run export
```

## Slidev 语法规范

### 基础结构

```markdown
---
theme: seriph
background: https://source.unsplash.com/collection/9473456/1920x1080
class: text-center
highlighter: shiki
lineNumbers: true
info: |
  ## 演示文稿标题
  副标题或说明
drawings:
  persist: false
transition: slide-left
title: 页面标题
---

# 第一页标题

第一页内容

---

# 第二页标题

第二页内容
```

### 常用布局

**居中对齐**：
```markdown
---
layout: center
class: text-center
---

# 居中大标题
```

**左右两栏**：
```markdown
---
layout: two-cols
---

# 左侧标题

左侧内容

::right::

# 右侧标题

右侧内容
```

**图片布局**：
```markdown
---
layout: image-right
image: /path/to/image.jpg
---

# 图片在右侧

文字内容在左侧
```

### 代码块

```markdown
```python
def hello():
    print("Hello, Slidev!")
```
```

### 演讲者备注

```markdown
<!-- 这是演讲者备注，观众看不到 -->
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器，实时预览 |
| `npm run build` | 构建静态网站 |
| `npm run export` | 导出为 PDF |
| `npx playwright install` | 首次导出前安装浏览器驱动 |

## 进阶技巧

### 自定义主题

```bash
# 使用社区主题
npm install @slidev/theme-apple-basic

# 在 frontmatter 中引用
theme: apple-basic
```

### 交互组件

Slidev 基于 Vue，可以直接在 Markdown 中使用 Vue 组件：

```markdown
<div class="p-4 bg-blue-100 rounded">
  <Counter :count="10" />
</div>
```

### 自动配图

可以使用 Unsplash 图片作为背景：

```markdown
---
background: https://source.unsplash.com/random/1920x1080?technology
---
```

## 相关资源

- **官方文档**: https://sli.dev/
- **GitHub**: https://github.com/slidevjs/slidev
- **主题市场**: https://sli.dev/resources/themes
- **示例合集**: https://sli.dev/showcases

## 故障排除

### 导出PDF失败

```bash
# 安装 Playwright 浏览器
npx playwright install chromium
```

### 中文显示问题

在 `style.css` 中添加：

```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');

body {
  font-family: 'Noto Sans SC', sans-serif;
}
```

### 端口被占用

```bash
npm run dev -- --port 3030
```

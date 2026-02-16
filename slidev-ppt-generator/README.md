# Slidev PPT 生成器 Skill

基于 Slidev 架构生成专业的代码驱动演示文稿。支持从长文章、大纲或文本自动生成结构化的 Slidev Markdown 文件，并提供导出 PDF/PPTX 的工作流。

## 什么是 Slidev？

Slidev 是一个为开发者打造的演示文稿工具：
- ✅ 使用 Markdown 编写
- ✅ 支持 Vue 组件和交互
- ✅ 代码高亮完美支持
- ✅ 可以导出 PDF/PPTX
- ✅ 实时预览，开发体验极佳

## 前置准备

1. 安装 Node.js 和 npm
2. 安装 Python（用于自动生成脚本）

## 快速开始

### 方式一：使用脚本自动生成（推荐）

```bash
# 进入 skill 目录
cd /path/to/slidev-ppt-generator

# 1. 准备你的文章内容
export ARTICLE="你的长文章内容..."

# 2. 运行生成脚本
python scripts/generate_slides.py "$ARTICLE"

# 3. 生成的 slides.md 会在当前目录
```

### 方式二：手动创建 Slidev 项目

```bash
# 1. 创建一个新目录并初始化
mkdir my-presentation
cd my-presentation
npm init slidev

# 2. 启动开发服务器
npm run dev

# 3. 在浏览器中打开 http://localhost:3030 预览
# 4. 编辑 slides.md 文件

# 5. 导出 PDF
npm run export
```

## 从现有模板开始

Skill 目录中提供了一个模板文件：[assets/slides-template.md](assets/slides-template.md)

你可以复制这个模板作为起点：

```bash
cp assets/slides-template.md my-slides.md
```

## Slidev 语法快速参考

### 基础页面结构

```markdown
---
theme: seriph
background: https://source.unsplash.com/collection/9473456/1920x1080
class: text-center
highlighter: shiki
lineNumbers: true
title: 演示文稿标题
---

# 第一页大标题

这是第一页的内容

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

左侧内容要点：
- 要点1
- 要点2
- 要点3

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

Slidev 完美支持代码高亮：

```markdown
```python
def hello():
    print("Hello, Slidev!")
    return "Welcome"
```
```

### 演讲者备注

```markdown
<!-- 这是演讲者备注，只有你能看到，观众看不到 -->
```

### 自动配图

使用 Unsplash 图片作为背景：

```markdown
---
background: https://source.unsplash.com/random/1920x1080?technology
---
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器，实时预览 |
| `npm run build` | 构建静态网站 |
| `npm run export` | 导出为 PDF |
| `npx playwright install` | 首次导出前安装浏览器驱动 |

## 从文章生成 PPT 的完整流程

1. **准备内容**：把你的文章、大纲或笔记整理成文本
2. **生成 Markdown**：运行 `generate_slides.py` 脚本
3. **预览调整**：启动 `npm run dev` 预览，手动调整内容
4. **导出交付**：运行 `npm run export` 导出 PDF

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

## 故障排除

### 导出 PDF 失败

```bash
# 安装 Playwright 浏览器
npx playwright install chromium
```

### 中文显示问题

在项目目录下创建 `style.css`：

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

## 相关资源

- **官方文档**: https://sli.dev/
- **GitHub**: https://github.com/slidevjs/slidev
- **主题市场**: https://sli.dev/resources/themes
- **示例合集**: https://sli.dev/showcases

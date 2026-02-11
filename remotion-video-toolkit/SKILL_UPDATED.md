---
name: remotion-video-toolkit
description: Complete toolkit for programmatic video creation with Remotion + React. Covers animations, timing, rendering (CLI/Node.js/Lambda/Cloud Run), captions, 3D, charts, text effects, transitions, and media handling. Use when writing Remotion code, building video generation pipelines, or creating data-driven video templates.
---

# Remotion Video Toolkit - 技术讲解视频生成

## 🎯 核心原则

### 1. TTS 引擎选择
**推荐：Microsoft Edge TTS**
- 引擎：`edge-tts`（已安装）
- 中文男声：`zh-CN-YunxiNeural`（云希，清晰自然）
- 中文女声：`zh-CN-XiaoxiaoNeural`（晓晓，温柔）
- 新闻播音：`zh-CN-YunyangNeural`（云扬）

**生成命令：**
```bash
edge-tts --voice zh-CN-YunxiNeural --text "解说词内容" --write-media output.mp3
```

### 2. 音画同步策略
**关键：先生成音频，再根据音频时长计算视频帧数**

```bash
# 1. 生成音频
edge-tts --voice zh-CN-YunxiNeural --text "..." --write-media slide1.mp3

# 2. 获取音频时长（秒）
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 slide1.mp3

# 3. 计算视频帧数（30fps）
frames = duration * 30
```

### 3. 动态高亮设计
**讲到哪里，高亮哪里**

```tsx
// 根据当前帧计算高亮状态
const frame = useCurrentFrame();
const fps = useVideoConfig().fps;

// 示例：第10-20秒高亮第一个要点
const highlight1 = frame >= 10*fps && frame < 20*fps;

<div style={{
  background: highlight1 ? 'rgba(0, 184, 148, 0.2)' : 'transparent',
  border: highlight1 ? '2px solid #00B894' : '1px solid rgba(255,255,255,0.1)',
  transform: highlight1 ? 'scale(1.05)' : 'scale(1)',
  transition: 'all 0.3s ease'
}}>
  要点内容
</div>
```

## 📋 工作流程

### Step 1: 内容审核
**在生成TTS和视频之前，先生成审核文档**

```markdown
# 视频内容审核文档

## Slide 1: 标题（20秒）

**画面文字：**
- 主标题：...
- 副标题：...
- 要点列表：...

**解说词：**
完整的解说词文本...

**动态效果：**
- 0-5秒：标题淡入
- 5-10秒：高亮第一个要点
- 10-15秒：高亮第二个要点
- 15-20秒：整体淡出
```

### Step 2: 生成TTS音频
**用户确认内容后，批量生成音频**

```bash
#!/bin/bash
# generate_audio.sh

slides=(
  "slide1:20:解说词1"
  "slide2:50:解说词2"
  # ...
)

for item in "${slides[@]}"; do
  IFS=':' read -r name duration text <<< "$item"
  edge-tts --voice zh-CN-YunxiNeural \
    --text "$text" \
    --write-media "public/audio/${name}.mp3"
  
  # 验证音频时长
  actual=$(ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 "public/audio/${name}.mp3")
  echo "$name: 预期${duration}秒, 实际${actual}秒"
done
```

### Step 3: 创建Remotion组件
**根据实际音频时长调整视频**

```tsx
import { Audio, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

export const Slide1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // 根据音频内容划分时间段
  const section1 = frame >= 0 && frame < 5*fps;      // 0-5秒
  const section2 = frame >= 5*fps && frame < 10*fps; // 5-10秒
  const section3 = frame >= 10*fps && frame < 15*fps; // 10-15秒
  
  return (
    <div style={{ width: 1920, height: 1080, background: '#1A1A2E' }}>
      <Audio src={staticFile('audio/slide1.mp3')} />
      
      {/* 标题 - 始终显示 */}
      <h1>主标题</h1>
      
      {/* 要点1 - 讲到时高亮 */}
      <div style={{
        background: section1 ? 'rgba(0,184,148,0.2)' : 'transparent',
        border: section1 ? '2px solid #00B894' : '1px solid rgba(255,255,255,0.1)',
        transform: section1 ? 'scale(1.05)' : 'scale(1)',
      }}>
        要点1内容
      </div>
      
      {/* 要点2 - 讲到时高亮 */}
      <div style={{
        background: section2 ? 'rgba(0,184,148,0.2)' : 'transparent',
        border: section2 ? '2px solid #00B894' : '1px solid rgba(255,255,255,0.1)',
        transform: section2 ? 'scale(1.05)' : 'scale(1)',
      }}>
        要点2内容
      </div>
    </div>
  );
};
```

### Step 4: 注册Composition
**使用实际音频时长**

```tsx
import { Composition } from 'remotion';

// 获取音频时长（秒）
const slide1Duration = 20.5; // 从ffprobe获取

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="Slide1"
        component={Slide1}
        durationInFrames={Math.ceil(slide1Duration * 30)} // 向上取整
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
```

### Step 5: 渲染视频
**使用独立session，不阻塞主session**

```typescript
// 在主session中调用
sessions_spawn({
  agentId: "video-render",
  label: "UG1292视频渲染",
  task: `渲染UG1292技术讲解视频，共12个slide。
  
项目路径：/root/.openclaw/workspace/projects/ug1292-video
音频已生成：public/audio/slide*.mp3
组件已创建：src/compositions/Slide*.tsx

请依次渲染每个slide，完成后合并成完整视频。`,
  cleanup: "keep"
});
```

## 🎨 视觉设计规范

### 配色方案
```typescript
const colors = {
  background: {
    primary: '#1A1A2E',
    secondary: '#16213E',
  },
  text: {
    primary: '#FFFFFF',
    secondary: '#B8B8D1',
    muted: '#7A7A9D',
  },
  accent: {
    primary: '#00B894',   // 主要强调色（绿色）
    secondary: '#0070C0', // 次要强调色（蓝色）
    warning: '#FF6B35',   // 警告色（橙色）
  },
};
```

### 布局规范
```typescript
const layout = {
  padding: '80px 120px',
  titleSize: 48,
  subtitleSize: 36,
  bodySize: 24,
  captionSize: 18,
  iconSize: 32,
  spacing: {
    small: 15,
    medium: 30,
    large: 50,
  },
};
```

### 动画时序
```typescript
// 淡入淡出
const fadeIn = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
const fadeOut = interpolate(frame, [durationInFrames-15, durationInFrames], [1, 0]);

// 滑入效果
const slideIn = interpolate(frame, [10, 30], [-50, 0], { extrapolateRight: 'clamp' });

// 高亮脉冲
const pulse = Math.sin(frame * 0.1) * 0.1 + 1; // 0.9-1.1之间波动
```

## 🔧 常见问题

### Q1: 音频和视频不同步
**原因：** 视频帧数与音频时长不匹配

**解决：**
```bash
# 1. 获取音频实际时长
duration=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 audio.mp3)

# 2. 计算精确帧数
frames=$(echo "$duration * 30" | bc | awk '{print int($1+0.5)}')

# 3. 更新Composition的durationInFrames
```

### Q2: 中文TTS发音不自然
**解决：** 使用Edge TTS的中文专用声音

```bash
# 列出所有中文声音
edge-tts --list-voices | grep zh-CN

# 推荐声音
zh-CN-YunxiNeural      # 男声，清晰
zh-CN-XiaoxiaoNeural   # 女声，温柔
zh-CN-YunyangNeural    # 男声，新闻播音
```

### Q3: 渲染速度慢
**优化策略：**
1. 使用`--concurrency`参数并行渲染
2. 先渲染单个slide预览，确认无误后再渲染全部
3. 使用独立session，避免阻塞主session

```bash
# 并行渲染（4个worker）
npx remotion render src/index.tsx MainVideo out/video.mp4 --concurrency=4
```

## 📦 完整示例

参考项目：`/root/.openclaw/workspace/projects/ug1292-video/`

**项目结构：**
```
ug1292-video/
├── src/
│   ├── index.tsx              # 注册所有Composition
│   └── compositions/
│       ├── Slide1.tsx         # 封面页
│       ├── Slide2.tsx         # UG1292定位
│       └── ...
├── public/
│   └── audio/
│       ├── slide1.mp3         # Edge TTS生成
│       ├── slide2.mp3
│       └── ...
├── out/
│   ├── slide1.mp4             # 单个slide渲染结果
│   └── final.mp4              # 合并后的完整视频
├── REVIEW.md                  # 内容审核文档
└── VIDEO_PLAN.md              # 视频规划文档
```

## 🚀 快速开始

```bash
# 1. 创建项目
npx create-video --blank my-video
cd my-video

# 2. 生成审核文档（让用户确认内容）
# 编写 REVIEW.md

# 3. 生成TTS音频
./scripts/generate_audio.sh

# 4. 创建Remotion组件
# 编写 src/compositions/*.tsx

# 5. 渲染预览（单个slide）
npx remotion render src/index.tsx Slide1 out/slide1.mp4

# 6. 用户确认后，渲染全部（使用独立session）
sessions_spawn({
  agentId: "video-render",
  task: "渲染完整视频"
});
```

## 📚 相关资源

- Remotion官方文档：https://www.remotion.dev/docs
- Edge TTS文档：https://github.com/rany2/edge-tts
- FFmpeg音频处理：https://ffmpeg.org/ffmpeg-formats.html

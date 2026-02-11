# Remotion Video Toolkit

Complete toolkit for programmatic video creation with Remotion + React. Write React components, get real MP4 videos.

## What is this?

An OpenClaw AgentSkill that teaches AI agents how to build production-ready videos with Remotion — from simple animations to complex multi-scene presentations, data visualizations, and automated video generation pipelines.

## What you can build

- **Personalized videos at scale** — Spotify Wrapped style, one template → thousands of unique outputs
- **Automated social media clips** — Pull live data, render daily/weekly posts
- **Dynamic presentations** — Multi-page slideshows with audio sync
- **Animated data visualizations** — Turn dashboards into shareable video clips
- **TikTok/Reels captions** — Word-by-word highlighted subtitles
- **Product showcase videos** — Auto-generate from database
- **Video generation as a service** — HTTP endpoint that returns MP4 files

## Quick start

```bash
# Scaffold a project
npx create-video@latest my-video

# Preview in browser
cd my-video && npm start

# Render to MP4
npx remotion render src/index.ts MyComposition out/video.mp4

# Pass dynamic data
npx remotion render src/index.ts MyComposition out.mp4 --props '{"title": "Hello"}'
```

## Key features covered

### Core concepts
- **Compositions** — Define videos, stills, folders, default props
- **Multi-scene structure** ⭐ — Build presentations and slideshows correctly
- **Rendering** — CLI, Node.js API, AWS Lambda, Cloud Run
- **Calculate metadata** — Dynamic duration and dimensions

### Animation & timing
- Animations (fade, scale, rotate, slide)
- Timing (interpolation, easing, spring physics)
- Sequencing (delay, chain, orchestrate)
- Transitions (scene-to-scene)
- Trimming (cut start/end)

### Text & typography
- Text animations (typewriter, word highlight, reveal)
- Fonts (Google Fonts, local fonts)
- Measuring text (fit to containers, detect overflow)

### Media handling
- Videos (embed, trim, speed, volume, loop)
- Audio (import, trim, fade, volume control)
- Images & GIFs (timeline-synced playback)
- Assets (importing any media)

### Captions & subtitles
- Transcribe captions (Whisper, Deepgram, AssemblyAI)
- Display captions (TikTok-style word highlighting)
- Import SRT files

### Data visualization
- Charts (animated bar charts, line graphs)

### Advanced
- 3D content (Three.js, React Three Fiber)
- Lottie animations
- TailwindCSS styling
- DOM measurement

## 🎯 Multi-scene structure (Important!)

When building videos with multiple pages or scenes (presentations, slideshows), use the **correct architecture**:

### ✅ Correct: Separate Compositions

```tsx
// Root.tsx
<Composition id="Slide01" component={Slide01} durationInFrames={866} fps={30} width={1920} height={1080} />
<Composition id="Slide02" component={Slide02} durationInFrames={650} fps={30} width={1920} height={1080} />
```

```bash
# Render each scene
npx remotion render Slide01 out/slide01.mp4
npx remotion render Slide02 out/slide02.mp4

# Concatenate with ffmpeg
cat > filelist.txt << EOF
file 'slide01.mp4'
file 'slide02.mp4'
EOF
ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4
```

### ❌ Wrong: Frame range rendering

```tsx
// DON'T DO THIS - all slides will overlap!
export const Video = () => (
  <>
    <Slide01 />
    <Slide02 />
  </>
);

// This renders ALL slides for frames 0-865
npx remotion render Video out.mp4 --frames=0-865
```

**Why it fails:** Remotion renders the entire component for each frame. Frame ranges only control output, not which components render.

**Read more:** [rules/multi-scene-structure.md](rules/multi-scene-structure.md)

## Documentation structure

All rules are in the `rules/` directory:

```
rules/
├── compositions.md          # Define videos and compositions
├── multi-scene-structure.md # ⭐ Multi-page/multi-scene architecture
├── rendering.md             # CLI, API, serverless rendering
├── animations.md            # Fade, scale, rotate, slide
├── timing.md                # Interpolation and easing
├── sequencing.md            # Delay and chain animations
├── text-animations.md       # Typewriter, word highlight
├── videos.md                # Embed and control videos
├── audio.md                 # Audio handling
├── display-captions.md      # TikTok-style captions
├── charts.md                # Animated data visualizations
└── ... (29 rules total)
```

## Requirements

- **Node.js** 18+
- **React** 18+
- **Remotion** — `npx create-video@latest`
- **FFmpeg** — ships with `@remotion/renderer`

## Real-world example: 12-slide presentation

```tsx
// Root.tsx
const slides = [
  { id: 'Slide01', component: Slide01, audio: 'audio/slide01.mp3', frames: 866 },
  { id: 'Slide02', component: Slide02, audio: 'audio/slide02.mp3', frames: 650 },
  // ... more slides
];

export const RemotionRoot = () => (
  <>
    {slides.map(({ id, component, audio, frames }) => (
      <Composition
        key={id}
        id={id}
        component={() => (
          <AbsoluteFill>
            {React.createElement(component)}
            <Audio src={staticFile(audio)} />
          </AbsoluteFill>
        )}
        durationInFrames={frames}
        fps={30}
        width={1920}
        height={1080}
      />
    ))}
  </>
);
```

**Render script:**

```bash
#!/bin/bash
for i in {01..12}; do
  npx remotion render "Slide$i" "out/slide$i.mp4" --codec h264
done

# Concatenate
cat > out/filelist.txt << EOF
$(for i in {01..12}; do echo "file 'slide$i.mp4'"; done)
EOF

ffmpeg -f concat -safe 0 -i out/filelist.txt -c copy out/final.mp4
```

## Use with OpenClaw

This is an OpenClaw AgentSkill. When your AI agent needs to build videos with Remotion, it will automatically reference these rules.

**Skill location:** `/root/.openclaw/workspace/skills/remotion-video-toolkit/`

## Contributing

Missing something? Found a better approach? Open a PR — new rules, improved examples, bug fixes all welcome.

**Source:** [github.com/shreefentsar/remotion-video-toolkit](https://github.com/shreefentsar/remotion-video-toolkit)

## License

MIT

---

Built by [Zone 99](https://99.zone) | Enhanced for OpenClaw by the community

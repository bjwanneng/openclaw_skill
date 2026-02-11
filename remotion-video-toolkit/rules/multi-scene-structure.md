# Multi-scene and multi-page video structure

When building videos with multiple distinct scenes or pages (like presentations, slideshows, or chapter-based content), you have two architectural choices. Pick the right one based on your use case.

---

## Two approaches

### Approach 1: Separate Compositions (recommended for independent scenes)

**Use when:**
- Each scene can be rendered independently
- You want to render individual scenes for testing
- Scenes have different durations, dimensions, or frame rates
- You're building a presentation or slideshow where each slide is self-contained

**Structure:**

```tsx
// Root.tsx
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Slide01"
        component={Slide01}
        durationInFrames={866}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="Slide02"
        component={Slide02}
        durationInFrames={650}
        fps={30}
        width={1920}
        height={1080}
      />
      {/* More slides... */}
    </>
  );
};
```

**Rendering:**

```bash
# Render individual scenes
npx remotion render Slide01 out/slide01.mp4
npx remotion render Slide02 out/slide02.mp4

# Concatenate with ffmpeg
cat > filelist.txt << EOF
file 'slide01.mp4'
file 'slide02.mp4'
EOF
ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4
```

**Pros:**
- Test each scene independently
- Parallel rendering possible
- Easy to update individual scenes
- Clear separation of concerns

**Cons:**
- Need to concatenate videos afterward
- Slightly more complex build process

---

### Approach 2: Single Composition with Sequences

**Use when:**
- Scenes share timing or need synchronized transitions
- You want a single render command
- Scenes flow continuously without hard cuts
- You're building a narrative video with chapters

**Structure:**

```tsx
// Video.tsx
export const Video: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      <Sequence from={0} durationInFrames={866}>
        <Slide01 />
      </Sequence>
      <Sequence from={866} durationInFrames={650}>
        <Slide02 />
      </Sequence>
      <Sequence from={1516} durationInFrames={622}>
        <Slide03 />
      </Sequence>
      {/* More sequences... */}
      
      {/* Audio for each scene */}
      <Sequence from={0} durationInFrames={866}>
        <Audio src={staticFile('audio/slide01.mp3')} />
      </Sequence>
      <Sequence from={866} durationInFrames={650}>
        <Audio src={staticFile('audio/slide02.mp3')} />
      </Sequence>
    </AbsoluteFill>
  );
};

// Root.tsx
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="FullVideo"
      component={Video}
      durationInFrames={8176} // Sum of all scenes
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

**Rendering:**

```bash
# Single render command
npx remotion render FullVideo out/video.mp4
```

**Pros:**
- Single render command
- No concatenation needed
- Easy to add transitions between scenes
- Shared timing and synchronization

**Cons:**
- Must render entire video to test one scene
- Harder to update individual scenes
- Longer render times for small changes

---

## Common mistake: Frame range rendering

**❌ WRONG:**

```tsx
// This does NOT work as expected!
// Video.tsx contains all 12 slides
export const Video: React.FC = () => {
  return (
    <>
      <Slide01 />
      <Slide02 />
      <Slide03 />
      {/* ... all slides */}
    </>
  );
};

// Trying to render just the first slide
// This will render ALL slides for frames 0-865!
npx remotion render Video out/slide01.mp4 --frames=0-865
```

**Why it fails:**
- Remotion renders the ENTIRE component for each frame
- Frame range only controls which frames are output, not which components are rendered
- All 12 slides will be visible/overlapping in frames 0-865

**✅ CORRECT:**

Use `<Sequence>` with proper `from` and `durationInFrames`:

```tsx
export const Video: React.FC = () => {
  return (
    <>
      <Sequence from={0} durationInFrames={866}>
        <Slide01 />
      </Sequence>
      <Sequence from={866} durationInFrames={650}>
        <Slide02 />
      </Sequence>
      {/* Slide02 won't render during frames 0-865 */}
    </>
  );
};
```

Or create separate Compositions (see Approach 1).

---

## Audio synchronization

### With separate Compositions:

```tsx
// Each composition includes its own audio
const SlideWithAudio: React.FC<{ 
  SlideComponent: React.FC; 
  audioFile: string 
}> = ({ SlideComponent, audioFile }) => {
  return (
    <AbsoluteFill>
      <SlideComponent />
      <Audio src={staticFile(audioFile)} />
    </AbsoluteFill>
  );
};

// In Root.tsx
<Composition
  id="Slide01"
  component={() => (
    <SlideWithAudio 
      SlideComponent={Slide01} 
      audioFile="audio/slide01.mp3" 
    />
  )}
  durationInFrames={866}
  fps={30}
  width={1920}
  height={1080}
/>
```

### With single Composition:

```tsx
export const Video: React.FC = () => {
  return (
    <AbsoluteFill>
      {/* Video sequences */}
      <Sequence from={0} durationInFrames={866}>
        <Slide01 />
      </Sequence>
      <Sequence from={866} durationInFrames={650}>
        <Slide02 />
      </Sequence>
      
      {/* Audio sequences - must match video timing */}
      <Sequence from={0} durationInFrames={866}>
        <Audio src={staticFile('audio/slide01.mp3')} />
      </Sequence>
      <Sequence from={866} durationInFrames={650}>
        <Audio src={staticFile('audio/slide02.mp3')} />
      </Sequence>
    </AbsoluteFill>
  );
};
```

---

## Calculating durations from audio

```tsx
import { getAudioDurationInSeconds } from '@remotion/media-utils';
import { staticFile } from 'remotion';

// In calculateMetadata or component
const audioDuration = await getAudioDurationInSeconds(
  staticFile('audio/slide01.mp3')
);
const durationInFrames = Math.ceil(audioDuration * fps);
```

---

## Decision matrix

| Requirement | Separate Compositions | Single Composition |
|-------------|----------------------|-------------------|
| Test individual scenes | ✅ Easy | ❌ Must render all |
| Single render command | ❌ Need concat | ✅ One command |
| Parallel rendering | ✅ Possible | ❌ Sequential |
| Scene transitions | ⚠️ Limited | ✅ Full control |
| Update one scene | ✅ Fast | ❌ Slow |
| Shared timing/sync | ⚠️ Manual | ✅ Automatic |

---

## Best practices

1. **For presentations/slideshows**: Use separate Compositions
2. **For narrative videos**: Use single Composition with Sequences
3. **Always use `<Sequence>`** when combining multiple scenes in one Composition
4. **Match audio and video durations** exactly to avoid sync issues
5. **Test individual scenes** before rendering the full video
6. **Use `calculateMetadata`** to set durations dynamically from audio files

---

## Example: 12-slide presentation

```tsx
// Root.tsx
import { Composition } from 'remotion';
import { Slide01, Slide02, /* ... */ Slide12 } from './slides';
import { AbsoluteFill, Audio, staticFile } from 'remotion';

const SlideWithAudio: React.FC<{
  SlideComponent: React.FC;
  audioFile: string;
}> = ({ SlideComponent, audioFile }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#0a1929' }}>
      <SlideComponent />
      <Audio src={staticFile(audioFile)} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  const slides = [
    { id: 'Slide01', component: Slide01, audio: 'audio/slide01.mp3', frames: 866 },
    { id: 'Slide02', component: Slide02, audio: 'audio/slide02.mp3', frames: 650 },
    // ... more slides
  ];

  return (
    <>
      {slides.map(({ id, component, audio, frames }) => (
        <Composition
          key={id}
          id={id}
          component={() => (
            <SlideWithAudio 
              SlideComponent={component} 
              audioFile={audio} 
            />
          )}
          durationInFrames={frames}
          fps={30}
          width={1920}
          height={1080}
        />
      ))}
    </>
  );
};
```

**Render script:**

```bash
#!/bin/bash
# render-all.sh

for i in {01..12}; do
  npx remotion render "Slide$i" "out/slide$i.mp4" --codec h264
done

# Concatenate
cat > out/filelist.txt << EOF
$(for i in {01..12}; do echo "file 'slide$i.mp4'"; done)
EOF

ffmpeg -f concat -safe 0 -i out/filelist.txt -c copy out/final.mp4
```

---

## Summary

- **Separate Compositions** = independent scenes, easy testing, need concatenation
- **Single Composition with Sequences** = unified timeline, single render, harder to test
- **Never** rely on frame ranges to isolate scenes - use `<Sequence>` or separate Compositions
- **Always** match audio and video durations exactly
- **Choose** based on your workflow: testing flexibility vs. render simplicity

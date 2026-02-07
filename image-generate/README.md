# Image Generate Skill

OpenClaw 图片生成技能，支持多种图片生成模型。

## 功能特性

- ✅ 支持火山引擎豆包图片生成模型
- ✅ 支持 Gemini 3 Pro 图片生成模型
- ✅ 环境变量配置，安全可靠
- ✅ 自动保存生成的图片

## 支持的模型

### 1. 火山引擎豆包 (Doubao Seedream)

**模型**: `doubao-seedream-4-5-251128`

**使用方法**:
```bash
export ARK_API_KEY="your-ark-api-key"
export MODEL_IMAGE_NAME="doubao-seedream-4-5-251128"
python scripts/image_generate.py "一只可爱的猫"
```

### 2. Gemini 3 Pro Image Preview

**模型**: `gemini-3-pro-image-preview`

**使用方法**:
```bash
export GEMINI_IMAGE_API_KEY="your-api-key"
export GEMINI_IMAGE_BASE_URL="https://open.xiaojingai.com"
export GEMINI_IMAGE_MODEL="gemini-3-pro-image-preview"
python scripts/image_generate_gemini.py "未来科技感的城市夜景"
```

## 环境变量配置

### 火山引擎配置

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `ARK_API_KEY` | 火山引擎 API Key | ✅ |
| `MODEL_IMAGE_NAME` | 模型名称 | ❌ (默认: doubao-seedream-4-5-251128) |
| `IMAGE_DOWNLOAD_DIR` | 图片保存目录 | ❌ (默认: ./) |

### Gemini 配置

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `GEMINI_IMAGE_API_KEY` | Gemini API Key | ✅ |
| `GEMINI_IMAGE_BASE_URL` | API 基础 URL | ❌ (默认: https://open.xiaojingai.com) |
| `GEMINI_IMAGE_MODEL` | 模型名称 | ❌ (默认: gemini-3-pro-image-preview) |
| `IMAGE_DOWNLOAD_DIR` | 图片保存目录 | ❌ (默认: ./) |

## 使用示例

### 生成简单图片
```bash
python scripts/image_generate_gemini.py "一只可爱的橘猫"
```

### 生成复杂场景
```bash
python scripts/image_generate_gemini.py "未来科技感的城市夜景，赛博朋克风格，霓虹灯光，高楼大厦，科幻氛围，4K高清"
```

### 指定保存目录
```bash
export IMAGE_DOWNLOAD_DIR="/path/to/save"
python scripts/image_generate_gemini.py "一只猫"
```

## 输出格式

生成的图片会保存为：
- 文件名格式: `gemini_image_{timestamp}.{ext}`
- 默认保存位置: 当前目录
- 支持格式: JPEG, PNG

## 注意事项

1. **API Key 安全**: 不要将 API Key 硬编码到代码中，使用环境变量
2. **超时时间**: 图片生成可能需要 1-2 分钟，请耐心等待
3. **网络要求**: 需要稳定的网络连接
4. **模型激活**: 火山引擎模型需要在控制台激活后才能使用

## 技能集成

在 OpenClaw 中使用此技能：

```markdown
当用户需要生成图片时，调用 image_generate_gemini.py 脚本。
```

## 许可证

Apache License 2.0

## 作者

老张头 & 有事忙 🐝

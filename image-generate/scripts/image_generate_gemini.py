#!/usr/bin/env python3
"""
Gemini 3 Pro Image Generation Script
使用小镜AI的Gemini 3 Pro模型生成图片
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse

def image_generate_gemini(prompt: str):
    """使用 Gemini 3 Pro 生成图片
    
    Args:
        prompt: 图片描述文本
    """
    if not prompt:
        print("错误：prompt 不能为空")
        return
    
    # 从环境变量读取配置
    base_url = os.getenv("GEMINI_IMAGE_BASE_URL", "https://open.xiaojingai.com")
    api_key = os.getenv("GEMINI_IMAGE_API_KEY")
    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
    
    if not api_key:
        print("错误：未设置 GEMINI_IMAGE_API_KEY 环境变量")
        print("请设置：export GEMINI_IMAGE_API_KEY='your-token'")
        return
    
    # 构建请求
    url = f"{base_url}/v1/models/{model}:generateContent"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # 发送请求
        print(f"正在生成图片: {prompt}")
        print(f"API端点: {url}")
        print(f"模型: {model}")
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        print("发送请求中...")
        with urllib.request.urlopen(req, timeout=120) as response:
            print(f"收到响应，状态码: {response.status}")
            result = json.loads(response.read().decode('utf-8'))
        
        # 解析响应
        if 'candidates' not in result:
            print(f"错误：响应格式异常: {result}")
            return
        
        # 提取图片URL
        image_urls = []
        for candidate in result.get('candidates', []):
            for part in candidate.get('content', {}).get('parts', []):
                if 'inlineData' in part:
                    # Base64 编码的图片数据
                    image_data = part['inlineData']['data']
                    mime_type = part['inlineData']['mimeType']
                    
                    # 保存图片
                    download_dir = os.getenv("IMAGE_DOWNLOAD_DIR", "./")
                    if not os.path.exists(download_dir):
                        os.makedirs(download_dir, exist_ok=True)
                    
                    timestamp = int(time.time())
                    ext = mime_type.split('/')[-1]
                    filename = f"gemini_image_{timestamp}.{ext}"
                    filepath = os.path.join(download_dir, filename)
                    
                    # 解码并保存
                    import base64
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(image_data))
                    
                    print(f"✅ 图片已保存: {filepath}")
                    image_urls.append(filepath)
                
                elif 'fileData' in part:
                    # 文件引用
                    file_uri = part['fileData']['fileUri']
                    print(f"✅ 图片URL: {file_uri}")
                    image_urls.append(file_uri)
        
        if not image_urls:
            print("警告：未找到生成的图片")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return image_urls
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP错误 {e.code}: {error_body}")
    except Exception as e:
        print(f"生成图片失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python image_generate_gemini.py <prompt>")
        print("示例: python image_generate_gemini.py '一只可爱的猫'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    image_generate_gemini(prompt)

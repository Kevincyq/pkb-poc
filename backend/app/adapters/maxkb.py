import os, httpx

# MaxKB 配置
MAXKB_BASE_URL = os.getenv("MAXKB_BASE_URL", "http://maxkb:8080").rstrip("/")
MAXKB_API_KEY = os.getenv("MAXKB_API_KEY", "")
MAXKB_APPLICATION_ID = os.getenv("MAXKB_APPLICATION_ID", "")

# 构建完整的 API URL（基于你提供的实际 URL 格式）
if MAXKB_APPLICATION_ID:
    CHAT_API_URL = f"{MAXKB_BASE_URL}/api/application/{MAXKB_APPLICATION_ID}/chat/completions"
else:
    CHAT_API_URL = f"{MAXKB_BASE_URL}/api/chat/completions"

async def ensure_collection():
    # 若你的 MaxKB 需要显式创建集合，可在此调用管理接口。
    return True

async def upsert_document(text: str, meta: dict) -> dict:
    """
    通过 MaxKB Chat API 发送文档内容进行索引
    """
    if not MAXKB_API_KEY or not MAXKB_APPLICATION_ID:
        print(f"MaxKB not configured: API_KEY={bool(MAXKB_API_KEY)}, APP_ID={bool(MAXKB_APPLICATION_ID)}")
        return {"ok": False, "error": "MaxKB not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MAXKB_API_KEY}"
        }
        
        # 使用 Chat API 发送文档内容，让 MaxKB 学习和索引
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "请学习和记住以下文档内容，以便后续回答相关问题。"
                },
                {
                    "role": "user", 
                    "content": f"文档标题：{meta.get('title', '未知')}\n文档来源：{meta.get('source_uri', '未知')}\n文档内容：{text}"
                }
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
            
            if resp.status_code >= 400:
                print(f"MaxKB upsert error: {resp.status_code} - {resp.text}")
                return {"ok": False, "error": resp.text}
            
            print(f"MaxKB upsert success: text_length={len(text)}")
            return {"ok": True, "response": resp.json()}
            
    except Exception as e:
        print(f"MaxKB upsert error: {e}")
        return {"ok": False, "error": str(e)}

async def semantic_search(query: str, top_k: int = 8) -> list[dict]:
    """
    使用 MaxKB OpenAI 兼容 API 进行语义搜索
    返回 [{score, text, metadata, source_uri}, ...]
    """
    if not MAXKB_API_KEY or not MAXKB_APPLICATION_ID:
        print(f"MaxKB not configured: API_KEY={bool(MAXKB_API_KEY)}, APP_ID={bool(MAXKB_APPLICATION_ID)}")
        return []
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MAXKB_API_KEY}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",  # MaxKB 兼容格式
            "messages": [
                {
                    "role": "user",
                    "content": f"搜索相关内容：{query}"
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(CHAT_API_URL, json=payload, headers=headers)
            
            if resp.status_code >= 400:
                print(f"MaxKB API error: {resp.status_code} - {resp.text}")
                return []
            
            data = resp.json()
            
            # 解析 OpenAI 格式的响应
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                
                # 简单的结果格式化（实际使用中可能需要更复杂的解析）
                return [{
                    "score": 0.9,
                    "text": content,
                    "metadata": {"query": query, "source": "maxkb"},
                    "source_uri": "maxkb://search"
                }]
            
            return []
            
    except Exception as e:
        print(f"MaxKB search error: {e}")
        return []


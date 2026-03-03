from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

app = FastAPI(title="HKJC Proxy API")

# 1. 解決 CORS 跨域限制的關鍵設定
# 允許所有來源 (origins="*") 訪問這個 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "HKJC Proxy API is running!"}

@app.get("/api/odds")
async def get_odds(date: str, venue: str, raceno: str):
    """
    接收前端請求，代替前端向 HKJC 發送請求，然後將結果返回。
    前端只需要呼叫: /api/odds?date=20260304&venue=HV&raceno=1
    """
    hkjc_url = f"https://bet.hkjc.com/racing/getJSON.aspx?type=winplace&date={date}&venue={venue}&raceno={raceno}"
    
    # 加入 Header 偽裝成普通瀏覽器，避免被馬會阻擋
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://bet.hkjc.com/",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }

    try:
        # 使用 httpx 進行異步請求 (比 requests 更適合 FastAPI)
        async with httpx.AsyncClient() as client:
            response = await client.get(hkjc_url, headers=headers, timeout=10.0)
            
            # 如果馬會返回錯誤狀態碼
            response.raise_for_status()
            
            # 將馬會的 JSON 數據直接轉發給前端
            return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"請求 HKJC 失敗: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"HKJC 返回錯誤狀態: {exc.response.status_code}")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"發生未知錯誤: {str(e)}")

# 本地測試用
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


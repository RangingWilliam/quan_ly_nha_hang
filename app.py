import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
from google import genai
from google.genai import types

app = FastAPI(title="Lamar Davis Restaurant API")

# Cấu hình CORS để tệp index.html chạy trên trình duyệt có quyền gọi tới API Backend này
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu trúc dữ liệu JSON để ép buộc Gemini trích xuất món ăn chính xác
class OrderItem(BaseModel):
    item_name: str = Field(description="Tên chính xác của món ăn khớp 100% với thực đơn")
    quantity: int = Field(description="Số lượng món ăn khách hàng muốn đặt")

class BotResponseStructure(BaseModel):
    reply: str = Field(description="Lời thoại phản hồi, tư vấn cho khách hàng bằng tiếng Việt")
    ordered_items: List[OrderItem] = Field(default=[], description="Danh sách các món ăn khách chốt đặt. Nếu khách chỉ hỏi hoặc chưa chốt mua, hãy để mảng rỗng []")

# Cấu trúc dữ liệu yêu cầu gửi từ Trình duyệt lên Server
class ChatRequest(BaseModel):
    message: str
    api_key: str
    use_mock: bool
    model_name: str

# Tự động khởi tạo dữ liệu menu tĩnh nếu chưa tồn tại file csv
def init_menu_file():
    menu_path = Path("menu.csv")
    if not menu_path.exists():
        sample_menu = pd.DataFrame([
            {"name": "Yee-Yee Ass Burger", "description": "Chiếc burger bò phô mai siêu to khổng lồ giúp bạn vứt ngay cái kiểu tóc quê mùa.", "ingredients": "bánh mì burger, thịt bò nướng, phô mai cheddar", "notes": "Món ăn bán chạy nhất tại tiệm."},
            {"name": "LD Organics Herbal Pizza", "description": "Bánh Pizza đế mỏng giòn rụm được phủ một lớp thảo mộc đặc biệt màu xanh.", "ingredients": "đế pizza, sốt cà chua, phô mai mozzarella, thảo mộc LD", "notes": "Chống chỉ định ăn trước khi gặp cảnh sát."},
            {"name": "Chop's Heavyweight Hotdog", "description": "Chiếc hotdog siêu dài kẹp xúc xích xông khói cỡ bự đặt theo tên chú chó lực lưỡng.", "ingredients": "bánh mì hotdog, xúc xích béc-giê siêu to, mù tạt vàng", "notes": "Cẩn thận giữ chắc tay kẻo bị táp mất!"},
            {"name": "Chamberlain Hills Fried Chicken", "description": "Gà rán giòn rụm kiểu miền Nam nước Mỹ mang màu sắc của khu phố Chamberlain Hills.", "ingredients": "cánh và đùi gà, bột chiên xù bí mật, sốt BBQ cay", "notes": "Món ăn lý tưởng cho các buổi tụ họp băng đảng."}
        ])
        sample_menu.to_csv(menu_path, index=False, encoding="utf-8")
    return pd.read_csv(menu_path)

menu_df = init_menu_file()

def build_menu_context(df: pd.DataFrame) -> str:
    lines = []
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        desc = str(row.get("description", "")).strip()
        ing = str(row.get("ingredients", "")).strip()
        lines.append(f"- {name}: {desc} Thành phần: {ing}.")
    return "\n".join(lines)

MENU_CONTEXT = build_menu_context(menu_df)
OUT_OF_SCOPE_MSG = "Tôi đang không hỗ trợ chức năng này. Xin vui lòng liên hệ nhân viên nhà hàng qua hotline 318-237-3870 để được trợ giúp."

SYSTEM_INSTRUCTION = f"""
Bạn tên là LDBot, một trợ lý AI thông minh, nhiệt tình của nhà hàng Lamar Davis Restaurant.
Dưới đây là thông tin thực đơn của nhà hàng:
{MENU_CONTEXT}

Quy tắc trả lời BẮT BUỘC:
1. Luôn luôn trả lời bằng tiếng Việt, giọng điệu vui vẻ, hiếu khách.
2. Chỉ tư vấn và trả lời dựa trên thực đơn được cung cấp. Không tự bịa ra món ăn ngoài danh sách.
3. Khi khách chốt mua hoặc muốn đặt món cụ thể kèm số lượng, hãy trích xuất chính xác tên món và số lượng vào mảng 'ordered_items'.
4. Nếu khách hàng hỏi những câu nằm ngoài phạm vi nhà hàng/ẩm thực (ví dụ: công nghệ, mua điện thoại, thời tiết, giải toán...), bạn PHẢI điền chính xác vào trường 'reply' câu sau: "{OUT_OF_SCOPE_MSG}"
"""

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    # Xử lý chế độ Mock Mode giả lập không cần gọi API Key
    if payload.use_mock or not payload.api_key:
        mock_items = []
        msg_lower = payload.message.lower()
        if "burger" in msg_lower:
            mock_items = [{"item_name": "Yee-Yee Ass Burger", "quantity": 1}]
        elif "pizza" in msg_lower:
            mock_items = [{"item_name": "LD Organics Herbal Pizza", "quantity": 1}]
        elif "chicken" in msg_lower or "gà" in msg_lower:
            mock_items = [{"item_name": "Chamberlain Hills Fried Chicken", "quantity": 1}]
            
        if any(keyword in msg_lower for keyword in ["iphone", "thời tiết", "máy tính", "giải toán"]):
            return {"reply": OUT_OF_SCOPE_MSG, "ordered_items": []}
            
        return {
            "reply": "👩🏿‍🦲 **[Mock Mode - Server]**: Chào bạn! Hệ thống nhận diện từ khóa thành công tại Backend. Khi có API Key thật, Gemini sẽ tự động xử lý thông minh hơn!",
            "ordered_items": mock_items
        }

    # Xử lý gọi Gemini API thực tế
    try:
        client = genai.Client(api_key=payload.api_key)
        response = client.models.generate_content(
            model=payload.model_name,
            contents=payload.message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=BotResponseStructure,
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Gemini API: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


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

# Cấu trúc dữ liệu JSON để ép buộc Gemini trích xuất món ăn chính xác sang giỏ hàng
class OrderItem(BaseModel):
    item_name: str = Field(description="Tên chính xác của món ăn khớp 100% với thực đơn")
    quantity: int = Field(description="Số lượng món ăn khách hàng muốn đặt")

class BotResponseStructure(BaseModel):
    reply: str = Field(description="Lời thoại phản hồi, tư vấn cho khách hàng bằng tiếng Việt")
    ordered_items: List[OrderItem] = Field(default=[], description="Danh sách các món ăn khách chốt đặt. Nếu khách chỉ hỏi hoặc chưa chốt mua, hãy để mảng rỗng []")

# Cấu trúc dữ liệu yêu cầu gửi từ Trình duyệt (index.html) lên Server Python
class ChatRequest(BaseModel):
    message: str
    api_key: str
    use_mock: bool
    model_name: str

# TỰ ĐỘNG KHỞI TẠO FILE THỰC ĐƠN ĐẦY ĐỦ 12 MÓN CHUẨN CỦA BẠN
def init_menu_file():
    menu_path = Path("menu.csv")
    if not menu_path.exists():
        sample_menu = pd.DataFrame([
            {"name": "Yee-Yee Ass Burger", "description": "Chiếc burger bò phô mai siêu to khổng lồ giúp bạn vứt ngay cái kiểu tóc quê mùa.", "ingredients": "bánh mì burger, thịt bò nướng, phô mai cheddar, xà lách, cà chua, sốt đặc chế LD", "notes": "Món ăn bán chạy nhất tại tiệm."},
            {"name": "LD Organics Herbal Pizza", "description": "Bánh Pizza đế mỏng giòn rụm được phủ một lớp thảo mộc đặc biệt màu xanh từ chính nông trại.", "ingredients": "đế pizza, sốt cà chua, phô mai mozzarella, xúc xích pepperoni, thảo mộc LD Organics", "notes": "Chống chỉ định ăn trước khi lái xe làm nhiệm vụ."},
            {"name": "Chop's Heavyweight Hotdog", "description": "Chiếc hotdog siêu dài kẹp xúc xích xông khói cỡ bự đặt theo tên chú chó lực lưỡng.", "ingredients": "bánh mì hotdog, xúc xích béc-giê siêu to, hành tây ngào đường, mù tạt vàng", "notes": "Cẩn thận giữ chắc tay kẻo bị chú chó Chop nhảy vào táp mất!"},
            {"name": "Chamberlain Hills Fried Chicken", "description": "Gà rán giòn rụm kiểu miền Nam nước Mỹ mang màu sắc của khu phố Chamberlain Hills.", "ingredients": "cánh và đùi gà, bột chiên xù bí mật, súp lơ xanh ăn kèm, sốt BBQ cay", "notes": "Món ăn lý tưởng cho các buổi tụ họp của băng đảng Families."},
            {"name": "Simeon's Repo Mac & Cheese", "description": "Mì ống nướng phô mai béo ngậy, dính chặt và đậm đặc như cái cách lão sếp Simeon lừa lọc quỵt tiền.", "ingredients": "mì ống macaroni, phô mai parmesan, phô mai cheddar, bơ, thịt xông khói vụn", "notes": "Ăn để giải tỏa ức chế sau khi bị lão sếp Simeon quỵt tiền công."},
            {"name": "Bacon 'Apache Chief' Sandwich", "description": "Sandwich kẹp đẫm thịt ba chỉ xông khói áp chảo giòn tan thể hiện sự thống trị đường phố.", "ingredients": "bánh mì gối nướng, thịt ba chỉ xông khói xém cạnh, trứng ốp la, sốt mayonnaise", "notes": "Ăn nhanh gọn ngay trên xe trong lúc chờ Franklin đột nhập."},
            {"name": "Streets of Los Santos Loaded Fries", "description": "Khoai tây chiên ngập dầu phủ sốt phô mai béo ngậy, hỗn loạn hệt như giao thông trung tâm Los Santos.", "ingredients": "khoai tây cắt dài, sốt phô mai ấm, thịt bò băm vị taco, hành lá, ớt ngâm", "notes": "Phù hợp làm món ăn kèm cho các gã gangster đang thèm đồ béo."},
            {"name": "Stretch's Backstabbing Pasta", "description": "Mì Ý sốt cà chua thịt băm cay nồng đậm vị, nhắc nhở bạn không được tin tưởng bất cứ gã nào vừa ra tù.", "ingredients": "mì sợi dài spaghetti, sốt cà chua cay, thịt bò băm, tỏi, ớt bột", "notes": "Vị cay xé lưỡi nhắc nhở bạn không được tin tưởng kẻ đâm sau lưng."},
            {"name": "Ballas-Busting Buffalo Wings", "description": "Cánh gà chiên giòn sốt Buffalo chua cay nồng, ăn vào là muốn đi dẹp sạch bọn băng đảng Ballas màu tím.", "ingredients": "cánh gà, sốt ớt cayenne cay nồng, bơ nhạt, giấm, sốt phô mai xanh", "notes": "Món ăn có độ cay cực cao, ăn xong là máu chiến đầy người."},
            {"name": "Green Gang Ribs BBQ", "description": "Sườn heo nướng tảng sốt BBQ mang đậm phong cách tiệc nướng sân sau tại Grove Street.", "ingredients": "sườn non heo, sốt BBQ mật ong, bột tỏi, tiêu đen, màu thực phẩm xanh organic", "notes": "Ăn món này là phải dùng tay không để gặm, đúng chất dân đường phố."},
            {"name": "Vanilla Unicorn Tacos", "description": "Bánh taco vỏ giòn kẹp thịt gà xé, món ăn khuya khoái khẩu của Lamar sau mỗi đêm quẩy banh nóc.", "ingredients": "vỏ bánh taco nướng giòn, thịt gà xé, bắp cải bào, sốt kem chua, hành tây", "notes": "Ăn kèm một lát chanh vắt thẳng vào nhân để tăng hương vị bùng nổ."},
            {"name": "Wasted Fudge Brownie", "description": "Bánh sô-cô-la brownie đậm đặc, ngọt đắng đan xen hệt như khi bạn lỡ tay kích nổ quả bom dính trong game.", "ingredients": "sô-cô-la đen, bơ, bột mì, trứng, hạt óc chó, vụn bánh sô-cô-la", "notes": "Món tráng miệng hoàn hảo để kết thúc một ngày dài chạy trốn FIB."}
        ])
        sample_menu.to_csv(menu_path, index=False, encoding="utf-8")
        
    config_path = Path("config.json")
    if not config_path.exists():
        sample_config = {
            "restaurant_name": "LD Restaurant",
            "restaurant_address": "67 Chamberlain Hills, Los Santos, USA",
            "hotline": "318-237-3870",
            "functions": ["giới thiệu nhà hàng", "giới thiệu menu", "giải đáp câu hỏi về món ăn"],
            "out_of_scope_message": "Tôi đang không hỗ trợ chức năng này. Xin vui lòng liên hệ nhân viên nhà hàng qua hotline 318-237-3870 để được trợ giúp."
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(sample_config, f, ensure_ascii=False, indent=2)
            
    df = pd.read_csv(menu_path)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return df, cfg

menu_df, config = init_menu_file()

def build_menu_context(df: pd.DataFrame) -> str:
    lines = []
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        desc = str(row.get("description", "")).strip()
        ing = str(row.get("ingredients", "")).strip()
        notes = str(row.get("notes", "")).strip()
        lines.append(f"- {name}: {desc} Thành phần: {ing}. Ghi chú: {notes}")
    return "\n".join(lines)

MENU_CONTEXT = build_menu_context(menu_df)
OUT_OF_SCOPE_MSG = config.get("out_of_scope_message", "Tôi đang không hỗ trợ chức năng này.")

SYSTEM_INSTRUCTION = f"""
Bạn tên là LDBot, một trợ lý AI thông minh, nhiệt tình của nhà hàng {config.get('restaurant_name')}.
Địa chỉ quán: {config.get('restaurant_address')}.

Dưới đây là thông tin thực đơn của nhà hàng:
{MENU_CONTEXT}

Quy tắc trả lời BẮT BUỘC:
1. Luôn luôn trả lời bằng tiếng Việt, giọng điệu vui vẻ, hiếu khách.
2. Chỉ tư vấn và trả lời dựa trên thực đơn được cung cấp. Không tự bịa ra món ăn ngoài danh sách.
3. Khi khách chốt mua hoặc muốn đặt món cụ thể kèm số lượng, hãy trích xuất chính xác tên món và số lượng vào mảng 'ordered_items'.
4. Nếu khách hàng hỏi những câu nằm ngoài phạm vi nhà hàng/ẩm thực (ví dụ: công nghệ, mua điện thoại, thời tiết, giải toán...), bạn PHẢI điền chính xác vào trường 'reply' câu sau: "{OUT_OF_SCOPE_MSG}"
"""

# API Cung cấp danh sách 12 món ăn cho file index.html hiển thị ở cột bên trái
@app.get("/api/menu")
async def get_menu():
    # Chuyển đổi dữ liệu bảng DataFrame thành dạng danh sách để JavaScript dễ đọc
    return menu_df.to_dict(orient="records")

# API Tiếp nhận tin nhắn trò chuyện và xử lý đơn đặt hàng bằng AI
@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    if payload.use_mock or not payload.api_key:
        mock_items = []
        msg_lower = payload.message.lower()
        if "burger" in msg_lower:
            mock_items = [{"item_name": "Yee-Yee Ass Burger", "quantity": 1}]
        elif "pizza" in msg_lower:
            mock_items = [{"item_name": "LD Organics Herbal Pizza", "quantity": 1}]
            
        if any(keyword in msg_lower for keyword in ["iphone", "thời tiết", "máy tính", "giải toán"]):
            return {"reply": OUT_OF_SCOPE_MSG, "ordered_items": []}
            
        return {
            "reply": "👩🏿‍🦲 **[Mock Mode - Server]**: Chào bạn! Hệ thống nhận diện từ khóa thành công tại Backend. Khi có API Key thật, Gemini sẽ tự động bóc tách đơn hàng chính xác vào giỏ hàng!",
            "ordered_items": mock_items
        }

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

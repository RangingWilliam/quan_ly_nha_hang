import os
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# 1. CẤU HÌNH TRANG WEB STREAMLIT
st.set_page_config(
    page_title="LDBot - Lamar Davis AI",
    page_icon="🍀",
    layout="wide"
)

# 2. TỰ ĐỘNG KHỞI TẠO DỮ LIỆU MENU & CONFIG
@st.cache_data
def init_data():
    menu_path = Path("menu.csv")
    if not menu_path.exists():
        # ĐÃ SỬA: Đưa trực tiếp danh sách các Dict vào DataFrame để tạo thành 12 dòng dữ liệu chuẩn
        sample_menu_data = pd.DataFrame([
            {
                "name": "Yee-Yee Ass Burger",
                "description": "Chiếc burger bò phô mai siêu to khổng lồ, ngon đến mức giúp bạn vứt ngay cái kiểu tóc quê mùa 'yee-yee ass haircut' để ra đường tán tỉnh mấy cô nàng nóng bỏng.",
                "ingredients": "bánh mì burger, thịt bò nướng, phô mai cheddar, xà lách, cà chua, sốt đặc chế LD",
                "notes": "Món ăn bán chạy nhất tại tiệm, khuyên dùng cho những ai đang bị bạn thân kỳ thị ngoại hình."
            },
            {
                "name": "LD Organics Herbal Pizza",
                "description": "Bánh Pizza đế mỏng giòn rụm được phủ ngập ngụa phô mai và một lớp 'thảo mộc đặc biệt' màu xanh từ chính nông trại LD Organics của Lamar.",
                "ingredients": "đế pizza, sốt cà chua, phô mai mozzarella, xúc xích pepperoni, thảo mộc LD Organics",
                "notes": "Ăn một miếng là thấy thư giãn, chống chỉ định ăn trước khi lái xe làm nhiệm vụ hoặc khi gặp cảnh sát."
            },
            {
                "name": "Chop's Heavyweight Hotdog",
                "description": "Chiếc hotdog siêu dài kẹp xúc xích xông khói cỡ bự, được đặt tên theo chú chó Chop lực lưỡng của Franklin mà Lamar cực kỳ khoái dắt đi quậy phá.",
                "ingredients": "bánh mì hotdog, xúc xích béc-giê siêu to, hành tây ngào đường, mù tạt vàng, tương cà",
                "notes": "Cẩn thận giữ chắc tay, kẻo bị chú chó Chop nhảy vào táp mất!"
            },
            {
                "name": "Chamberlain Hills Fried Chicken",
                "description": "Gà rán giòn rụm kiểu miền Nam nước Mỹ mang màu sắc của khu phố Chamberlain Hills, lớp da ngoài giòn rần rật, bên trong thịt ngọt mọng nước.",
                "ingredients": "cánh và đùi gà, bột chiên xù bí mật, súp lơ xanh ăn kèm, sốt BBQ cay",
                "notes": "Món ăn lý tưởng cho các buổi tụ họp của băng đảng Families trước khi đi 'thu hồi' xe."
            },
            {
                "name": "Simeon's Repo Mac & Cheese",
                "description": "Mì ống nướng phô mai béo ngậy, dính chặt và đậm đặc như cái cách lão Simeon bắt Lamar và Franklin đi đòi nợ thuê mà không trả đủ lương.",
                "ingredients": "mì ống macaroni, phô mai parmesan, phô mai cheddar, bơ, thịt xông khói vụn",
                "notes": "Ăn để giải tỏa ức chế sau khi bị lão sếp Simeon lừa lọc quỵt tiền công."
            },
            {
                "name": "Bacon 'Apache Chief' Sandwich",
                "description": "Sandwich kẹp đẫm thịt ba chỉ xông khói áp chảo giòn tan, lấy danh nghĩa biệt danh 'Apache Chief' tự phong của Lamar để thể hiện sự thống trị đường phố.",
                "ingredients": "bánh mì gối nướng, thịt ba chỉ xông khói xém cạnh, trứng ốp la, sốt mayonnaise",
                "notes": "Ăn nhanh gọn ngay trên xe trong lúc chờ Franklin đột nhập vào biệt thự của mục tiêu."
            },
            {
                "name": "Streets of Los Santos Loaded Fries",
                "description": "Khoai tây chiên ngập dầu được phủ một lớp nước sốt phô mai chảy béo ngậy, thịt bò băm và hành lá, hỗn loạn hệt như giao thông tại trung tâm Los Santos.",
                "ingredients": "khoai tây cắt dài, sốt phô mai ấm, thịt bò băm vị taco, hành lá, ớt ngâm",
                "notes": "Phù hợp làm món ăn kèm cho trẻ em hoặc cho mấy gã gangster đang thèm đồ béo."
            },
            {
                "name": "Stretch's Backstabbing Pasta",
                "description": "Mì Ý sốt cà chua thịt băm cay nồng đậm vị, được đặt tên theo gã Stretch - kẻ luôn tìm cách đâm sau lưng anh em Families.",
                "ingredients": "mì sợi dài spaghetti, sốt cà chua cay (arrabbiata), thịt bò băm, tỏi, ớt bột",
                "notes": "Vị cay xé lưỡi nhắc nhở bạn không được tin tưởng bất cứ gã nào vừa mới ra tù."
            },
            {
                "name": "Ballas-Busting Buffalo Wings",
                "description": "Cánh gà chiên giòn sốt Buffalo chua cay nồng, ăn vào là muốn đi 'thần sầu' dẹp sạch bọn băng đảng Ballas màu tím ở khu đối diện.",
                "ingredients": "cánh gà, sốt ớt cayenne cay nồng, bơ nhạt, giấm, ăn kèm cần tây và sốt phô mai xanh",
                "notes": "Món ăn có độ cay cực cao, ăn xong là máu chiến đầy người."
            },
            {
                "name": "Green Gang Ribs BBQ",
                "description": "Sườn heo nướng tảng sốt BBQ mang đậm phong cách tiệc nướng sân sau tại Grove Street, thịt mềm rực xương, đượm mùi khói than hoa.",
                "ingredients": "sườn non heo, sốt BBQ mật ong, bột tỏi, tiêu đen, màu thực phẩm xanh organic tạo điểm nhấn",
                "notes": "Ăn món này là phải dùng tay không để gặm, thể hiện đúng chất hoang dã của dân đường phố."
            },
            {
                "name": "Vanilla Unicorn Tacos",
                "description": "Bánh taco vỏ giòn rụm kẹp thịt gà xé đậm vị, món ăn khuya khoái khẩu của Lamar sau mỗi đêm quẩy banh nóc tại câu lạc bộ thoát y Vanilla Unicorn.",
                "ingredients": "vỏ bánh taco nướng giòn, thịt gà xé, bắp cải bào, sốt kem chua, hành tây",
                "notes": "Ăn kèm một lát chanh vắt thẳng vào nhân để tăng hương vị bùng nổ."
            },
            {
                "name": "Wasted Fudge Brownie",
                "description": "Bánh sô-cô-la brownie đậm đặc, ngọt đắng đan xen, ăn xong một miếng là muốn nằm gục 'WASTED' như khi bạn lỡ tay kích nổ quả bom dính trong game.",
                "ingredients": "sô-cô-la đen, bơ, bột mì, trứng, hạt óc chó, vụn bánh sô-cô-la",
                "notes": "Món tráng miệng hoàn hảo để kết thúc một ngày dài chạy trốn khỏi đặc vụ FIB."
            }
        ])
        sample_menu_data.to_csv(menu_path, index=False, encoding="utf-8")
        
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

menu_df, config = init_data()

# Khởi tạo giỏ hàng ban đầu trong session_state nếu chưa có
if "cart" not in st.session_state:
    st.session_state.cart = {}

# 3. CÁC HÀM LOGIC AI
def build_menu_context(df: pd.DataFrame) -> str:
    lines = []
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        desc = str(row.get("description", "")).strip()
        ing = str(row.get("ingredients", "")).strip()
        notes = str(row.get("notes", "")).strip()
        lines.append(f"- {name}: {desc} Thành phần: {ing}. Ghi chú: {notes}")
    return "\n".join(lines)

def build_system_instruction(cfg: dict) -> str:
    restaurant_name = cfg.get("restaurant_name", "LD Restaurant")
    restaurant_address = cfg.get("restaurant_address", "")
    functions = ", ".join(cfg.get("functions", ["tư vấn món ăn"]))
    out_of_scope_message = cfg.get("out_of_scope_message", "")
    return f"""
Bạn tên là LDBot, một trợ lý AI thông minh, nhiệt tình và lịch sự của nhà hàng {restaurant_name}. Địa chỉ quán: {restaurant_address}. 
Các nhiệm vụ được hỗ trợ: {functions}.

Quy tắc trả lời BẮT BUỘC:
1. Luôn trả lời bằng tiếng Việt, giọng điệu vui vẻ, niềm nở và hiếu khách.
2. Chỉ tư vấn và trả lời dựa trên thông tin thực đơn trong dữ liệu được cung cấp. Tuyệt đối KHÔNG tự bịa ra món ăn không có trong danh sách.
3. Khi khách hỏi hoặc muốn chốt đặt một món nào đó, hãy giới thiệu thêm thành phần và ghi chú món để tăng tính thuyết phục.
4. LẮT BẮT ĐẶT MÓN: Khi khách hàng nêu rõ ý định muốn mua/đặt/lấy món ăn cụ thể kèm số lượng (hoặc ngầm định số lượng là 1), hãy ghi nhận thông tin món ăn đó thật chính xác vào danh sách cấu trúc dữ liệu `ordered_items`.
5. Nếu khách hàng hỏi những câu nằm NGOÀI phạm vi nhà hàng/ẩm thực, hãy trả lời ĐÚNG câu sau: "{out_of_scope_message}"
6. Giữ câu trả lời súc tích, mạch lạc, dễ đọc.
""".strip()

menu_context = build_menu_context(menu_df)
system_instruction = build_system_instruction(config)

def ask_bot(question: str, api_key: str, use_mock: bool, model_name: str) -> dict:
    """Trả về dict gồm 'reply' (Văn bản) và 'ordered_items' (Danh sách món được đặt)"""
    if use_mock or not api_key:
        # Giả lập hành vi đặt món nếu bấm vào câu hỏi mẫu đặt hàng ở Mock Mode
mock_ordered = []
if "burger" in question.lower() or "đặc sản" in question.lower():
mock_ordered = [{"item_name": "Yee-Yee Ass Burger", "quantity": 1}]
return {
"reply": (
"👩🏿‍🦲 [Mock Mode]: Chào bạn! Hệ thống nhận diện từ khóa thành công. "
"Nếu bạn ở chế độ có API Key thực tế, Gemini sẽ bóc tách đơn hàng tự động để nạp thẳng vào giỏ hàng thanh bên trái!"
),
"ordered_items": mock_ordered
}
user_prompt = f"""
Dưới đây là thông tin thực đơn của nhà hàng:
{menu_context}
Khách hàng hỏi: "{question}"
Hãy trả lời khách hàng theo đúng vai trò LDBot và trả về đúng định dạng JSON cấu trúc yêu cầu.
"""
try:
client = genai.Client(api_key=api_key)
# Sử dụng tính năng response_schema để nhận cấu trúc dữ liệu JSON sạch
response = client.models.generate_content(
model=model_name,
contents=user_prompt,
config=types.GenerateContentConfig(
system_instruction=system_instruction,
temperature=0.2,
response_mime_type="application/json",
response_schema=BotResponseStructure,
)
)
# Ép kiểu kết quả JSON chuỗi trả về từ Model thành Dictionary Python
return json.loads(response.text)
except Exception as e:
return {
"reply": f"⚠️ Không gọi được Gemini API ({e}). Vui lòng kiểm tra lại API Key hoặc bật Mock Mode.",
"ordered_items": []
}

4. GIAO DIỆN THANH BÊN TRÁI (SIDEBAR)

with st.sidebar:
st.title(f"🍀 {config['restaurant_name']}")
st.markdown(f"📍 Địa chỉ: {config['restaurant_address']}")
st.markdown(f"📞 Hotline: {config['hotline']}")
st.divider()
# --- TÍNH NĂNG MỚI: HIỂN THỊ GIỎ HÀNG (CART) ---
st.subheader("🛒 Giỏ Hàng Của Bạn")
if not st.session_state.cart:
st.info("Giỏ hàng trống. Hãy chat đặt món với LDBot nhé!")
else:
for name, qty in list(st.session_state.cart.items()):
col_item, col_btn = st.columns([4])
col_item.markdown(f"🔹 {name} x {qty}")
if col_btn.button("❌", key=f"del_{name}"):
del st.session_state.cart[name]
st.rerun()
st.success(f"Tổng số món: {sum(st.session_state.cart.values())}")
if st.button("🔔 Gửi đơn hàng tới nhà bếp", type="primary", use_container_width=True):
st.toast("🎉 Đơn hàng đã được chuyển tới nhà bếp thành công!")
st.session_state.cart = {}
st.rerun()
st.divider()
st.subheader("⚙️ Cấu hình AI")
default_key = ""
try:
default_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
default_key = os.getenv("GEMINI_API_KEY", "")
api_key_input = st.text_input(
"🔑 Gemini API Key:",
value=default_key,
type="password",
placeholder="Dán GEMINI_API_KEY vào đây..."
)
model_choice = st.selectbox("Mô hình:", ["gemini-2.5-flash", "gemini-2.5-flash-lite"])
use_mock = st.toggle("🧪 Chế độ Mock Mode", value=(not bool(api_key_input)))
st.divider()
if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
st.session_state.messages = []
st.rerun()

5. GIAO DIỆN CHÍNH (MAIN CHAT UI)

st.title("👦🏿 Trợ Lý Ẩm Thực LDBot - Lamar Davis AI")
st.caption("Bài mẫu Dự Án Cuối Khóa CSI: Chatbot AI Đặt Món Thông Minh & Giỏ Hàng")
with st.expander("📋 Xem bảng Thực Đơn Nhà Hàng (menu.csv)", expanded=False):
st.dataframe(menu_df, use_container_width=True, hide_index=True)
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
st.session_state.messages = [
{
"role": "assistant",
"content": (
f"Dạ LDBot xin chào quý khách! 🍀✨\n\n"
f"Em là trợ lý AI của nhà hàng {config['restaurant_name']}.\n"
f"Quý khách có thể xem menu và bảo em: 'Lấy cho anh 2 cái Yee-Yee Ass Burger', em sẽ tự bỏ vào giỏ hàng ngay!"
)
}
]
st.markdown("💡 Bấm thử nhanh các tình huống kiểm thử:")
c1, c2, c3, c4 = st.columns(4)
quick_question = None
if c1.button("🛒 Đặt thử 1 Burger", use_container_width=True):
quick_question = "Lấy cho tôi một phần Yee-Yee Ass Burger để trải nghiệm thử xem nào!"
if c2.button("🍕 Đặt 2 Pizza & 1 Chicken", use_container_width=True):
quick_question = "Tôi muốn mua 2 cái LD Organics Herbal Pizza và 1 đĩa Chamberlain Hills Fried Chicken nhé."
if c3.button("📍 Địa chỉ nhà hàng", use_container_width=True):
quick_question = "Cho mình xin địa chỉ nhà hàng?"
if c4.button("📱 Hỏi mua iPhone (Lạc đề)", use_container_width=True):
quick_question = "iPhone đắt nhất hiện nay là gì?"
st.divider()

Hiển thị lịch sử chat

for msg in st.session_state.messages:
avatar = "👩🏿‍🦲" if msg["role"] == "assistant" else "👤"
with st.chat_message(msg["role"], avatar=avatar):
st.markdown(msg["content"])
chat_input = st.chat_input("Nhập câu hỏi hoặc gọi món tại đây...")
user_question = quick_question or chat_input
if user_question:
st.session_state.messages.append({"role": "user", "content": user_question})
with st.chat_message("user", avatar="👤"):
st.markdown(user_question)
with st.chat_message("assistant", avatar="👩🏿‍🦲"):
with st.spinner("⏳ LDBot đang phân tích và xử lý đơn hàng..."):
# Gọi API nhận về dạng Dictionary chứa cả văn bản phản hồi và mảng món đặt
result_dict = ask_bot(
question=user_question,
api_key=api_key_input,
use_mock=use_mock,
model_name=model_choice
)
bot_reply = result_dict.get("reply", "")
ordered_items = result_dict.get("ordered_items", [])
# Nếu có món ăn được bot bóc tách ra từ câu thoại, cập nhật vào giỏ hàng Streamlit
if ordered_items:
for item in ordered_items:
name = item.get("item_name")
qty = item.get("quantity", 1)
# Kiểm tra tên món khớp thực tế mới cho vào giỏ
if name in menu_df['name'].values:
st.session_state.cart[name] = st.session_state.cart.get(name, 0) + qty
st.toast(f"📥 Đã thêm {qty}x {name} vào giỏ hàng!")
st.markdown(bot_reply)
st.session_state.messages.append({"role": "assistant", "content": bot_reply})
if quick_question or ordered_items:
st.rerun()

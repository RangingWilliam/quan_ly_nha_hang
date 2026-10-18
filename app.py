import os
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# 1. CẤU HÌNH TRANG WEB STREAMLIT
st.set_page_config(
    page_title="PhoBot - Viet Cuisine AI",
    page_icon="🍜",
    layout="wide"
)

# 2. TỰ ĐỘNG KHỞI TẠO DỮ LIỆU MENU & CONFIG (Chuẩn Bước 5 - Bài 7)
@st.cache_data
def init_data():
    menu_path = Path("menu.csv")
    if not menu_path.exists():
        sample_menu_data = pd.DataFrame([
            {
                "name": "Gỏi Cuốn",
                "description": "Mỗi chiếc gỏi cuốn được cuốn cẩn thận trong lá bánh tráng mềm mại, kết hợp với các loại rau sống, thịt hoặc tôm tươi, thưởng thức cùng nước mắm chua ngọt.",
                "ingredients": "bún, bánh tráng, tôm, thịt bò phi lê, rau sống",
                "notes": "Món gỏi cuốn thường được phục vụ tươi và phải ăn liền sau khi cuốn để trải nghiệm hương vị tốt nhất."
            },
            {
                "name": "Phở Việt Nam",
                "description": "Nổi tiếng với hương vị đậm đà và hương thơm của gia vị tự nhiên. Mỗi tô phở được chế biến từ nước dùng thơm ngon, kết hợp sợi bánh mềm mại và thịt bò thơm ngọt.",
                "ingredients": "bún phở, thịt bò, thịt gà, hành tây, hành phi, rau sống, giá đỗ, ớt",
                "notes": "Thịt bò có thể chọn giữa tái và chín theo ý thích của khách."
            },
            {
                "name": "Cơm Tấm",
                "description": "Món ăn đường phố trứ danh gồm cơm nấu từ gạo tấm thơm dẻo, kết hợp thịt heo nướng than hoa, trứng hấp, chả, dưa leo và nước mắm chua ngọt.",
                "ingredients": "gạo tấm, thịt heo nướng, trứng, chả, dưa leo, nước mắm chua ngọt",
                "notes": "Thích hợp cho cả bữa trưa và bữa tối no bụng."
            },
            {
                "name": "Bún Bò",
                "description": "Đặc sản ẩm thực miền Trung Việt Nam, nổi tiếng với nước dùng cay thơm nồng nàn hương sả và mắm ruốc, cùng sợi bún to dai mềm.",
                "ingredients": "bún, thịt bò, hành tây, hành tím, rau sống",
                "notes": "Thịt bò có thể chọn giữa tái, nạm, bắp bò, giò heo."
            },
            {
                "name": "Khoai Tây Chiên",
                "description": "Món ăn phổ biến với lớp vỏ giòn rụm bên ngoài và khoai mềm bùi bên trong, chấm cùng tương cà hoặc sốt cay.",
                "ingredients": "khoai tây, dầu thực vật, muối",
                "notes": "Thích hợp dùng làm món khai vị hoặc ăn kèm cho trẻ em."
            },
            {
                "name": "Phở Bò",
                "description": "Phở bò là món ăn truyền thống nổi tiếng của Việt Nam với nước dùng thơm ngon, bánh phở mềm và những lát thịt bò mỏng. Món ăn thường được dùng nóng cùng rau thơm và các loại gia vị.",
                "ingredients": "bánh phở, thịt bò, xương bò, hành lá, rau thơm, gừng, quế, hồi",
                "notes": "Phở bò ngon nhất khi được dùng nóng, có thể ăn kèm chanh, ớt và rau thơm tùy khẩu vị."
            },
            {
                "name": "Bánh Xèo",
                "description": "Bánh xèo có lớp vỏ vàng giòn được làm từ bột gạo, bên trong là nhân tôm, thịt và giá đỗ. Khi ăn thường cuốn cùng rau sống và chấm với nước mắm chua ngọt.",
                "ingredients": "bột gạo, tôm, thịt heo, giá đỗ, hành lá, rau sống, nước mắm",
                "notes": "Bánh xèo nên được thưởng thức ngay sau khi chiên để giữ được độ nóng và giòn của lớp vỏ."
            }
        ])
        sample_menu_data.to_csv(menu_path, index=False, encoding="utf-8")

    config_path = Path("config.json")
    if not config_path.exists():
        sample_config = {
            "restaurant_name": "Viet Cuisine",
            "restaurant_address": "329 Scottmouth, Georgia, USA",
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

# 3. CÁC HÀM LOGIC AI (Từ Bước 6, 7, 8 - Bài 7)
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
    restaurant_name = cfg.get("restaurant_name", "Viet Cuisine")
    restaurant_address = cfg.get("restaurant_address", "")
    functions = ", ".join(cfg.get("functions", ["tư vấn món ăn"]))
    out_of_scope_message = cfg.get("out_of_scope_message", "")

    return f"""
Bạn tên là PhoBot, một trợ lý AI thông minh, nhiệt tình và lịch sự của nhà hàng {restaurant_name}.
Địa chỉ quán: {restaurant_address}.
Các nhiệm vụ được hỗ trợ: {functions}.

Quy tắc trả lời BẮT BUỘC:
1. Luôn trả lời bằng tiếng Việt, giọng điệu vui vẻ, niềm nở và hiếu khách.
2. Chỉ tư vấn và trả lời dựa trên thông tin thực đơn trong dữ liệu được cung cấp. Tuyệt đối KHÔNG tự bịa ra món ăn không có trong danh sách.
3. Khi khách hỏi món nào đó, hãy giới thiệu thêm thành phần và ghi chú món để khách thấy hấp dẫn.
4. Nếu khách hàng hỏi những câu nằm NGOÀI phạm vi nhà hàng/ẩm thực (ví dụ: công nghệ, đồ điện tử, thời tiết, giải toán...), hãy trả lời ĐÚNG câu sau:
   "{out_of_scope_message}"
5. Giữ câu trả lời súc tích, mạch lạc, dễ đọc.
""".strip()

menu_context = build_menu_context(menu_df)
system_instruction = build_system_instruction(config)

def ask_bot(question: str, api_key: str, use_mock: bool, model_name: str) -> str:
    if use_mock or not api_key:
        return (
            "🤖 **[Mock Mode - Phản hồi giả lập]**: Chào bạn! Đây là câu trả lời mẫu khi ở chế độ Mock. "
            f"Nhà hàng **{config['restaurant_name']}** (*{config['restaurant_address']}*) hiện có 7 món: "
            f"**{', '.join(menu_df['name'].tolist())}**. "
            "Khi có API Key hợp lệ ở thanh bên trái, Gemini Flash sẽ phân tích và trả lời cực kỳ thông minh!"
        )

    user_prompt = f"""
Dưới đây là thông tin thực đơn của nhà hàng:
{menu_context}

Khách hàng hỏi:
"{question}"

Hãy trả lời khách hàng theo đúng vai trò PhoBot và các quy tắc đã được hướng dẫn.
"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3
            )
        )
        return response.text
    except Exception as e:
        return f"⚠️ Không gọi được Gemini API ({e}). Vui lòng kiểm tra lại API Key hoặc bật Mock Mode."

# 4. GIAO DIỆN THANH BÊN TRÁI (SIDEBAR)
with st.sidebar:
    st.title(f"🍜 {config['restaurant_name']}")
    st.markdown(f"📍 **Địa chỉ:** {config['restaurant_address']}")
    st.markdown(f"☎️ **Hotline:** `{config['hotline']}`")
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
    model_choice = st.selectbox("🤖 Mô hình:", ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"])
    use_mock = st.toggle("🧪 Chế độ Mock Mode", value=(not bool(api_key_input)))

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 5. GIAO DIỆN CHÍNH (MAIN CHAT UI)
st.title("🍜 Trợ Lý Ẩm Thực PhoBot - Viet Cuisine")
st.caption("Bài mẫu Dự Án Cuối Khóa CSI: Xây dựng Chatbot AI với Gemini & Streamlit")

with st.expander("📋 Xem bảng Thực Đơn Nhà Hàng (menu.csv)", expanded=False):
    st.dataframe(menu_df, use_container_width=True, hide_index=True)

# Khởi tạo lịch sử hội thoại bằng st.session_state (Chuẩn kiến thức Bài 8)
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                f"Dạ PhoBot xin chào quý khách! 🍜✨\n\n"
                f"Em là trợ lý AI của nhà hàng **{config['restaurant_name']}** "
                f"(tại *{config['restaurant_address']}*).\n"
                f"Quý khách muốn em giới thiệu thực đơn hay tư vấn món ngon nào hôm nay ạ?"
            )
        }
    ]

# Hàng nút bấm câu hỏi mẫu (Kịch bản kiểm thử Bước 9 & 10)
st.markdown("💡 **Bấm thử nhanh các tình huống kiểm thử:**")
c1, c2, c3, c4 = st.columns(4)
quick_question = None

if c1.button("🌟 Món đặc sản?", use_container_width=True):
    quick_question = "Món nào là đặc sản hoặc được gọi nhiều nhất?"
if c2.button("🌶️ Không ăn được cay", use_container_width=True):
    quick_question = "Nếu tôi không ăn được đồ cay hoặc có một số nguyên liệu không thích, nhà hàng có thể điều chỉnh món ăn theo yêu cầu không?"
if c3.button("📍 Địa chỉ nhà hàng", use_container_width=True):
    quick_question = "Cho mình xin địa chỉ nhà hàng?"
if c4.button("📱 Hỏi mua iPhone (Lạc đề)", use_container_width=True):
    quick_question = "iPhone đắt nhất hiện nay là gì?"

st.divider()

# Hiển thị bong bóng chat lịch sử bằng st.chat_message
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Ô nhập tin nhắn bằng st.chat_input
chat_input = st.chat_input("Nhập câu hỏi của bạn tại đây...")
user_question = quick_question or chat_input

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("⏳ PhoBot đang soạn câu trả lời..."):
            bot_reply = ask_bot(
                question=user_question,
                api_key=api_key_input,
                use_mock=use_mock,
                model_name=model_choice
            )
            st.markdown(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    if quick_question:
        st.rerun()

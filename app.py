import streamlit as st
import requests
import re
from PIL import Image
import io

# 頁面基本設定
st.set_page_config(page_title="投資組合再投資與多帳戶零股計算器", layout="wide", page_icon="📈")

# 建立分頁標籤
tab1, tab2 = st.tabs(["📸 賣出成交圖掃描與再投資分配", "👥 多帳戶獨立買進計算器"])

# ==============================================================================
# 分頁 1: 賣出成交圖掃描與再投資分配
# ==============================================================================
with tab1:
    st.title("📈 賣出成交圖自動掃描與再投資試算")

    # 1. 截圖上傳區
    st.header("第一步：上傳愛利得賣出成交截圖")
    st.caption("請上傳包含「成交價金」的賣出交割紀錄截圖，系統將自動擷取各檔股票金額。")

    uploaded_file = st.file_uploader("選擇上傳截圖檔案", type=["png", "jpg", "jpeg"], key="tab1_uploader")

    if "scanned_items" not in st.session_state:
        st.session_state["scanned_items"] = []

    if uploaded_file is not None:
        st.image(uploaded_file, caption="已上傳之成交截圖", width=400)
        
        if st.button("🔍 辨識截圖並自動帶入股票與金額", type="primary", key="btn_scan_t1"):
            with st.spinner("正在裁切標頭並進行文字辨識..."):
                try:
                    # 裁切上方 9% 區域以去除總結文字（避免誤判金額）
                    img = Image.open(uploaded_file)
                    width, height = img.size
                    cropped_img = img.crop((0, int(height * 0.09), width, height))
                    
                    img_byte_arr = io.BytesIO()
                    cropped_img.save(img_byte_arr, format='PNG')
                    cropped_bytes = img_byte_arr.getvalue()

                    payload = {
                        'apikey': 'helloworld',
                        'language': 'cht',
                        'scale': 'true',
                        'isTable': 'true',
                        'OCREngine': '2'
                    }
                    
                    files = {'file': ('screenshot.png', cropped_bytes, 'image/png')}
                    response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                    result = response.json()
                    
                    extracted_list = []
                    
                    if "ParsedResults"

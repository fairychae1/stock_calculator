import streamlit as st
import requests
import re

# Page configuration
st.set_page_config(page_title="Portfolio Budget Allocator", layout="wide", page_icon="📈")
st.title("📈 Auto-Scan & Rebalance Calculator")

# 1. Screenshot OCR Auto-Extraction
st.header("Step 1: Upload Sales Screenshot")
st.caption("Upload a screenshot from 愛利得 showing 成交價金.")

uploaded_file = st.file_uploader("Upload screenshot", type=["png", "jpg", "jpeg"])

if "scanned_items" not in st.session_state:
    st.session_state["scanned_items"] = []

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Screenshot", width=400)
    
    if st.button("🔍 Scan Screenshot & Populate Stocks", type="primary"):
        with st.spinner("Extracting stock numbers and 成交價金 from image..."):
            try:
                payload = {
                    'apikey': 'helloworld',
                    'language': 'cht',
                    'scale': 'true',
                    'isTable': 'true',
                    'OCREngine': '2'
                }
                
                file_bytes = uploaded_file.getvalue()
                file_type = uploaded_file.type.split('/')[-1] if uploaded_file.type else 'png'
                files = {'file': (f'screenshot.{file_type}', file_bytes, uploaded_file.type)}
                
                response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                result = response.json()
                
                extracted_list = []
                
                if "ParsedResults" in result and result["ParsedResults"]:
                    parsed_text = result['ParsedResults'][0].get('ParsedText', '')
                    
                    # 1. Extract ALL currency amounts (e.g., 298,584 or 1,322,500)
                    raw_amounts = re.findall(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{5,8}\b', parsed_text)
                    clean_amounts = [float(a.replace(',', '')) for a in raw_amounts if float(a.replace(',', '')) > 100]
                    
                    # 2. Extract ALL 4-digit stock tickers (excluding zero-padded numbers like 0000)
                    raw_tickers = re.findall(r'\b[1-9]\d{3}\b', parsed_text)
                    
                    # 3. Match tickers and amounts in sequential order
                    for i, amt in enumerate(clean_amounts):
                        stock_num = raw_tickers[i] if i < len(raw_tickers) else f"Row {i+1}"
                        extracted_list.append({"number": stock_num, "amount":

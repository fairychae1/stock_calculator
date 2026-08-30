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
        with st.spinner("Extracting stock names and 成交價金 from image..."):
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
                    lines = parsed_text.split('\r\n')
                    
                    for line in lines:
                        # Extract currency-formatted numbers like 298,584 or 1,322,500
                        amounts = re.findall(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{5,8}\b', line)
                        tickers = re.findall(r'\b\d{4}\b', line)
                        
                        if amounts:
                            clean_amt = float(amounts[-1].replace(',', ''))
                            ticker_name = tickers[0] if tickers else ""
                            extracted_list.append({"name": ticker_name, "amount": clean_amt})
                    
                    st.session_state["scanned_items"] = extracted_list
                    if extracted_list:
                        st.success(f"Successfully detected {len(extracted_list)} stocks with amounts!")
                    else:
                        st.warning("Could not automatically parse rows. Please enter

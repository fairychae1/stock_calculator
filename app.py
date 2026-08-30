import streamlit as st
import requests
import re
from PIL import Image
import io

# Page configuration
st.set_page_config(page_title="Portfolio Rebalance & Multi-Account Stock Allocator", layout="wide", page_icon="📈")

# Create Navigation Tabs
tab1, tab2 = st.tabs(["📸 Sales Rebalance Allocator", "👥 Multi-Person Budget Calculator"])

# ==============================================================================
# TAB 1: SALES REBALANCE ALLOCATOR (MULTI-GROUP SUPPORT)
# ==============================================================================
with tab1:
    st.title("📈 Screenshot Auto-Scan & Multi-Group Rebalance Allocator")

    # 1. Screenshot Upload & OCR Section
    st.header("Step 1: Upload Sales Screenshot")
    st.caption("Upload a screenshot from your broker app showing your Trade Amount (成交價金).")

    uploaded_file = st.file_uploader("Choose Screenshot File", type=["png", "jpg", "jpeg"], key="tab1_uploader")

    if "scanned_items" not in st.session_state:
        st.session_state["scanned_items"] = []

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Screenshot", width=400)
        
        if st.button("🔍 Scan Screenshot & Populate Stocks", type="primary", key="btn_scan_t1"):
            with st.spinner("Cropping header and scanning table rows..."):
                try:
                    # Crop top 9% to remove summary headers and prevent false amount matches
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
                    
                    if "ParsedResults" in result and result["ParsedResults"]:
                        parsed_text = result['ParsedResults'][0].get('ParsedText', '')
                        all_tickers = re.findall(r'\b[1-9]\d{3}\b', parsed_text)
                        
                        lines = parsed_text.split('\r\n')
                        ticker_idx = 0
                        
                        for line in lines:
                            amounts = re.findall(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{5,8}\b', line)
                            
                            if amounts:
                                clean_amt = float(amounts[-1].replace(',', ''))
                                if clean_amt > 100:
                                    line_tickers = re.findall(r'\b[1-9]\d{3}\b', line)
                                    if line_tickers:
                                        stock_num = line_tickers[0]
                                    elif ticker_idx < len(all_tickers):
                                        stock_num = all_tickers[ticker_idx]
                                        ticker_idx += 1
                                    else:
                                        stock_num = ""
                                        
                                    extracted_list.append({"number": stock_num, "amount": clean_amt})
                        
                        st.session_state["scanned_items"] = extracted_list
                        if extracted_list:
                            st.success(f"Successfully extracted {len(extracted_list)} stocks with prices!")
                        else:
                            st.warning("Could not automatically parse rows. Please enter values manually below.")
                    else:
                        st.error("OCR server busy

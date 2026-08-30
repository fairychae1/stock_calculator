import streamlit as st
import easyocr
from PIL import Image
import numpy as np

# Page configuration
st.set_page_config(page_title="Proceeds Stock Allocator", layout="centered", page_icon="📈")
st.title("📸 Stock Sales Proceeds Calculator")

# 1. Load OCR Reader (Cached so it loads quickly)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_tra', 'en'])

with st.spinner("Initializing image scanner..."):
    reader = load_ocr()

# 2. Upload Screenshot Section
st.header("Step 1: Upload Sales Screenshot")
uploaded_file = st.file_uploader("Upload screenshot from 愛利得 showing 成交價金", type=["png", "jpg", "jpeg"])

extracted_proceeds = 0.0

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded App Screenshot", use_container_width=True)
    
    with st.spinner("Scanning image for values..."):
        img_np = np.array(image)
        results = reader.readtext(img_np, detail=0)
        
        st.write("---")
        st.subheader("Detected Text Preview:")
        st.write(results)
        
    extracted_proceeds = st.number_input(
        "Confirm or edit total money gained (成交價金) in NTD:", 
        value=50000.0, 
        step=1000.0
    )

# 3. Allocation & Stock Setup
st.write("---")
st.header("Step 2: Set Allocation & Stock Details")

col1, col2 = st.columns(2)
with col1:
    portion = st.slider("Percentage of proceeds to use (%)", min_value=1, max_value=100, value=25)
with col2:
    target_stock = st.text_input("Target Stock Code/Name", value="2330")

calculated_budget = extracted_proceeds * (portion / 100.0)
st.info(f"Target Budget ({portion}% of NT$ {extracted_proceeds:,.0f}): **NT$ {calculated_budget:,.0f}**")

# 4. Manual Price Input & Calculation
st.write("---")
st.header("Step 3: Calculate Share Purchase")

manual_price = st.number_input(f"Enter set price for {target_stock} (NTD):", min_value=0.1, value=950.0, step=0.5)

if st.button("Calculate Shares to Buy", type="primary"):
    if calculated_budget <= 0:
        st.error("Target budget must be greater than zero.")
    elif manual_price <= 0:
        st.error("Stock price must be greater than zero.")
    else:
        # Calculate maximum whole shares (odd-lot / 零股)
        shares = int(calculated_budget // manual_price)
        total_cost = shares * manual_price
        leftover = calculated_budget - total_cost
        
        st.success("Calculation Complete!")
        st.metric(label=f"Shares to Buy of {target_stock} (零股)", value=f"{shares:,} shares")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric(label="Total Expenditure", value=f"NT$ {total_cost:,.0f}")
        with col_b:
            st.metric(label="Remaining Unused Budget", value=f"NT$ {leftover:,.0f}")

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
                    lines = parsed_text.split('\r\n')
                    
                    for line in lines:
                        # Extract currency-formatted numbers like 298,584 or 1,322,500
                        amounts = re.findall(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{5,8}\b', line)
                        # Extract 4-digit Taiwan stock codes (e.g., 2376, 3231, 6664)
                        tickers = re.findall(r'\b\d{4}\b', line)
                        
                        if amounts:
                            clean_amt = float(amounts[-1].replace(',', ''))
                            # Use detected 4-digit stock number
                            stock_num = tickers[0] if tickers else ""
                            extracted_list.append({"number": stock_num, "amount": clean_amt})
                    
                    st.session_state["scanned_items"] = extracted_list
                    if extracted_list:
                        st.success(f"Successfully detected {len(extracted_list)} stocks with amounts!")
                    else:
                        st.warning("Could not automatically parse rows. Please enter values manually below.")
                else:
                    st.error("OCR server busy. Please enter values manually below.")
            except Exception as e:
                st.error(f"Scan error: {e}")

st.write("---")

# 2. Selectable Sold Stocks Section
st.header("Step 2: Select Sold Stocks to Include in Budget")
st.caption("Check the boxes for the specific stock numbers you sold today.")

sold_total = 0.0

if st.session_state["scanned_items"]:
    st.subheader("📋 Detected Stocks from Screenshot")
    
    for idx, item in enumerate(st.session_state["scanned_items"]):
        stock_code = item['number'] if item['number'] else f"Stock #{idx+1}"
        
        # Displays "Include 2376 (NT$ 298,584)" instead of generic names
        use_stock = st.checkbox(
            label=f"Include **{stock_code}** — NT$ {item['amount']:,.0f}", 
            value=True, 
            key=f"chk_stock_num_{idx}"
        )
        
        if use_stock:
            sold_total += item["amount"]

    st.write("---")

# Manual Override Section
with st.expander("➕ Manually Input Stock Numbers & Amounts", expanded=not bool(st.session_state["scanned_items"])):
    col_left, col_right = st.columns(2)
    manual_total = 0.0
    
    for i in range(1, 11):
        target_col = col_left if i <= 5 else col_right
        with target_col:
            s1, s2 = st.columns([1, 2])
            with s1:
                st.text_input(f"Stock Number #{i}", placeholder="e.g. 2376", key=f"m_num_{i}")
            with s2:
                amt = st.number_input(f"Stock #{i} 成交價金 (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"m_amt_num_{i}")
                manual_total += amt
                
    sold_total += manual_total

st.metric(label="Total Selected Sales Earnings (Proceeds Budget)", value=f"NT$ {sold_total:,.0f}")

st.write("---")

# 3. Overall Reinvestment Budget Allocation
st.header("Step 3: Reinvestment Budget Allocation")

portfolio_pct = st.slider("Percentage of total sales earnings to reinvest (%)", min_value=1, max_value=100, value=100)
total_reinvest_budget = sold_total * (portfolio_pct / 100.0)

st.info(f"Available Reinvestment Budget ({portfolio_pct}% of NT$ {sold_total:,.0f}): **NT$ {total_reinvest_budget:,.0f}**")

st.write("---")

# 4. Target Buy Allocation Section (Up to 6 Stocks)
st.header("Step 4: Target Buy Allocation (Up to 6 Stocks)")
st.caption("Enter up to 6 target stock numbers, set buy price, and budget allocation percentage.")

buy_rows = []
total_weight = 0.0

for i in range(1, 7):
    b1, b2, b3 = st.columns([2, 2, 3])
    with b1:
        b_name = st.text_input(f"Target Stock Number #{i}", placeholder=f"e.g. 2330", key=f"buy_num_{i}")
    with b2:
        b_price = st.number_input(f"Target #{i} Set Price (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"buy_price_num_{i}")
    with b3:
        b_pct = st.number_input(f"Target #{i} Budget Allocation (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key=f"buy_pct_num_{i}")
    
    if b_price > 0 and b_pct > 0:
        buy_rows.append({
            "slot": i,
            "name": b_name if b_name else f"Target #{i}",
            "price": b_price,
            "pct": b_pct
        })
        total_weight += b_pct

if total_weight > 100.0:
    st.error(f"⚠️ Total target allocation is {total_weight:.1f}%, which exceeds 100%!")
elif total_weight < 100.0 and len(buy_rows) > 0:
    st.warning(f"ℹ️ Total target allocation is {total_weight:.1f}%. Unallocated budget: {100.0 - total_weight:.1f}%")

st.write("---")

# 5. Output Results
if st.button("Calculate Share Allocations", type="primary"):
    if total_reinvest_budget <= 0:
        st.error("Total reinvestment budget must be greater than zero.")
    elif len(buy_rows) == 0:
        st.error("Please enter at least one target stock with a price > 0 and allocation % > 0.")
    elif total_weight > 100.0:
        st.error("Cannot calculate while total allocation exceeds 100%.")
    else:
        st.subheader("📊 Purchase Plan Summary")
        
        grand_total_spent = 0.0
        res_cols = st.columns(min(len(buy_rows), 3))
        
        for index, item in enumerate(buy_rows):
            col_target = res_cols[index % len(res_cols)]
            
            allocated_funds = total_reinvest_budget * (item["pct"] / 100.0)
            shares = int(allocated_funds // item["price"])
            cost = shares * item["price"]
            leftover = allocated_funds - cost
            grand_total_spent += cost
            
            with col_target:
                st.markdown(f"### 🎯 Stock {item['name']}")
                st.write(f"**Allocated Budget ({item['pct']}%):** NT$ {allocated_funds:,.0f}")
                st.write(f"**Target Price:** NT$ {item['price']:,.2f}")
                st.metric(label="Shares to Buy (零股)", value=f"{shares:,} 股")
                st.write(f"**Total Cost:** NT$ {cost:,.0f}")
                st.write(f"**Leftover Cash:** NT$ {leftover:,.0f}")
                st.divider()
                
        total_leftover_cash = total_reinvest_budget - grand_total_spent
        
        st.success("✅ Allocation Calculation Complete!")
        summary_c1, summary_c2, summary_c3 = st.columns(3)
        with summary_c1:
            st.metric("Total Reinvestment Budget", f"NT$ {total_reinvest_budget:,.0f}")
        with summary_c2:
            st.metric("Total Capital Spent", f"NT$ {grand_total_spent:,.0f}")
        with summary_c3:
            st.metric("Total Unused Cash Remaining", f"NT$ {total_leftover_cash:,.0f}")

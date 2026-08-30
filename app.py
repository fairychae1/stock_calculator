import streamlit as st
import requests
import re
from PIL import Image
import io

# Page configuration
st.set_page_config(page_title="Portfolio & Multi-Person Stock Allocator", layout="wide", page_icon="📈")

# Create Navigation Tabs
tab1, tab2 = st.tabs(["📸 Sales Rebalance Allocator", "👥 Multi-Person Budget Calculator"])

# ==============================================================================
# TAB 1: SALES REBALANCE ALLOCATOR (EXISTING FEATURE)
# ==============================================================================
with tab1:
    st.title("📈 Auto-Scan & Rebalance Calculator")

    # 1. Screenshot OCR Auto-Extraction
    st.header("Step 1: Upload Sales Screenshot")
    st.caption("Upload a screenshot from 愛利得 showing 成交價金.")

    uploaded_file = st.file_uploader("Upload screenshot", type=["png", "jpg", "jpeg"], key="tab1_uploader")

    if "scanned_items" not in st.session_state:
        st.session_state["scanned_items"] = []

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Screenshot", width=400)
        
        if st.button("🔍 Scan Screenshot & Populate Stocks", type="primary", key="btn_scan_t1"):
            with st.spinner("Cropping header and scanning table rows..."):
                try:
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
            stock_code = item['number'] if item['number'] else f"{idx+1}"
            use_stock = st.checkbox(
                label=f"Include Stock **{stock_code}** — NT$ {item['amount']:,.0f}", 
                value=True, 
                key=f"chk_stock_num_v8_{idx}"
            )
            if use_stock:
                sold_total += item["amount"]
        st.write("---")

    with st.expander("➕ Manually Input Stock Numbers & Amounts", expanded=not bool(st.session_state["scanned_items"])):
        col_left, col_right = st.columns(2)
        manual_total = 0.0
        for i in range(1, 11):
            target_col = col_left if i <= 5 else col_right
            with target_col:
                s1, s2 = st.columns([1, 2])
                with s1:
                    st.text_input(f"Stock Code/Name #{i}", placeholder="e.g. 2376", key=f"m_num_v8_{i}")
                with s2:
                    amt = st.number_input(f"Stock #{i} 成交價金 (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"m_amt_num_v8_{i}")
                    manual_total += amt
        sold_total += manual_total

    st.metric(label="Total Selected Sales Earnings (Proceeds Budget)", value=f"NT$ {sold_total:,.0f}")
    st.write("---")

    # 3. Overall Reinvestment Budget Allocation
    st.header("Step 3: Reinvestment Budget Allocation")
    portfolio_pct = st.slider("Percentage of total sales earnings to reinvest (%)", min_value=1, max_value=100, value=100, key="slider_t1")
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
            b_name = st.text_input(f"Target Stock Code/Name #{i}", placeholder="e.g. 2330", key=f"buy_num_v8_{i}")
        with b2:
            b_price = st.number_input(f"Target #{i} Set Price (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"buy_price_num_v8_{i}")
        with b3:
            b_pct = st.number_input(f"Target #{i} Budget Allocation (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key=f"buy_pct_num_v8_{i}")
        
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

    if st.button("Calculate Share Allocations", type="primary", key="btn_calc_t1"):
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


# ==============================================================================
# TAB 2: MULTI-PERSON BUDGET CALCULATOR (NEW FEATURE)
# ==============================================================================
with tab2:
    st.title("👥 Multi-Person Stock Purchase Allocator")
    st.caption("Calculate share allocations for Person 1 (Primary Budget) and Persons 2–5 using daily ratio multipliers.")

    # 1. Stock & Primary Budget Input
    st.header("Step 1: Target Stock & Primary Budget")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        target_stock_t2 = st.text_input("Target Stock Code/Name", value="2330", key="t2_stock_code")
    with col_t2:
        p1_budget = st.number_input("Person 1 Allocated Budget (NTD)", min_value=100.0, value=30000.0, step=1000.0, key="t2_p1_budget")
    with col_t3:
        target_price_t2 = st.number_input("Set Stock Price (NTD)", min_value=0.1, value=950.0, step=0.5, key="t2_stock_price")

    st.write("---")

    # 2. Ratio Multipliers for Persons 2 to 5
    st.header("Step 2: Person 2–5 Budget Ratio Multipliers")
    st.caption("Enter the decimal multipliers for each person relative to Person 1's budget (e.g. 0.266 = 26.6% of Person 1).")

    col_r2, col_r3, col_r4, col_r5 = st.columns(4)
    with col_r2:
        ratio_p2 = st.number_input("Person 2 Ratio", min_value=0.0, max_value=5.0, value=0.266, step=0.001, format="%.4f", key="t2_r2")
    with col_r3:
        ratio_p3 = st.number_input("Person 3 Ratio", min_value=0.0, max_value=5.0, value=0.150, step=0.001, format="%.4f", key="t2_r3")
    with col_r4:
        ratio_p4 = st.number_input("Person 4 Ratio", min_value=0.0, max_value=5.0, value=0.200, step=0.001, format="%.4f", key="t2_r4")
    with col_r5:
        ratio_p5 = st.number_input("Person 5 Ratio", min_value=0.0, max_value=5.0, value=0.100, step=0.001, format="%.4f", key="t2_r5")

    st.write("---")

    # 3. Execution & Allocation Table
    if st.button("Calculate All People Shares", type="primary", key="btn_calc_t2"):
        if target_price_t2 <= 0:
            st.error("Stock price must be greater than zero.")
        elif p1_budget <= 0:
            st.error("Person 1 budget must be greater than zero.")
        else:
            st.subheader(f"📊 Purchase Summary for Stock: {target_stock_t2} (@ NT$ {target_price_t2:,.2f})")
            
            people_data = [
                {"name": "Person 1 (Original)", "ratio": 1.0, "budget": p1_budget},
                {"name": "Person 2", "ratio": ratio_p2, "budget": p1_budget * ratio_p2},
                {"name": "Person 3", "ratio": ratio_p3, "budget": p1_budget * ratio_p3},
                {"name": "Person 4", "ratio": ratio_p4, "budget": p1_budget * ratio_p4},
                {"name": "Person 5", "ratio": ratio_p5, "budget": p1_budget * ratio_p5},
            ]

            p_cols = st.columns(5)
            total_group_spent = 0.0
            total_group_budget = 0.0

            for idx, person in enumerate(people_data):
                p_budget = person["budget"]
                shares = int(p_budget // target_price_t2)
                cost = shares * target_price_t2
                leftover = p_budget - cost
                
                total_group_budget += p_budget
                total_group_spent += cost

                with p_cols[idx]:
                    st.markdown(f"### 👤 {person['name']}")
                    st.caption(f"Multiplier: **{person['ratio']:.4f}x**")
                    st.write(f"**Budget:** NT$ {p_budget:,.2f}")
                    st.metric(label="Shares to Buy (零股)", value=f"{shares:,} 股")
                    st.write(f"**Total Cost:** NT$ {cost:,.2f}")
                    st.write(f"**Leftover Cash:** NT$ {leftover:,.2f}")
                    st.divider()

            st.success("✅ Multi-Person Allocation Complete!")
            
            g1, g2, g3 = st.columns(3)
            with g1:
                st.metric("Combined Group Budget", f"NT$ {total_group_budget:,.2f}")
            with g2:
                st.metric("Combined Group Expenditure", f"NT$ {total_group_spent:,.2f}")
            with g3:
                st.metric("Combined Unused Cash", f"NT$ {total_group_budget - total_group_spent:,.2f}")

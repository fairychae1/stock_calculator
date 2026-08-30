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

    # Manual Fallback Input Section
    with st.expander("➕ Manually Add or Adjust Sold Stock Database", expanded=not bool(st.session_state["scanned_items"])):
        col_m1, col_m2 = st.columns(2)
        for i in range(1, 11):
            target_col = col_m1 if i <= 5 else col_m2
            with target_col:
                sm1, sm2 = st.columns([1, 2])
                with sm1:
                    m_code = st.text_input(f"Manual Stock #{i} Code", placeholder="e.g. 2376", key=f"m_code_v16_{i}")
                with sm2:
                    m_amt = st.number_input(f"Manual Stock #{i} Trade Amount", min_value=0.0, value=0.0, step=1000.0, key=f"m_amt_v16_{i}")
                    if m_amt > 0 and m_code:
                        if not any(x["number"] == m_code and x["amount"] == m_amt for x in st.session_state["scanned_items"]):
                            st.session_state["scanned_items"].append({"number": m_code, "amount": m_amt})

    # 2. Multi-Group Budget Allocation Section
    st.header("Step 2: Define Independent Funding Groups & Target Buys")
    st.caption("You can separate sold stocks (e.g. Stocks A & B) into Group 1 to buy C & D, and (Stocks E & F) into Group 2 to buy C, D, G, & H.")

    if "group_count" not in st.session_state:
        st.session_state["group_count"] = 2

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("➕ Add Funding Group"):
            st.session_state["group_count"] += 1
            st.rerun()
    with col_btn2:
        if st.session_state["group_count"] > 1:
            if st.button("➖ Remove Funding Group"):
                st.session_state["group_count"] -= 1
                st.rerun()

    all_groups_data = []

    for g in range(1, st.session_state["group_count"] + 1):
        st.markdown(f"### 📂 Funding Group #{g}")
        
        st.subheader(f"Group #{g}: Select Source Sold Stocks")
        g_sold_total = 0.0
        
        if st.session_state["scanned_items"]:
            sold_cols = st.columns(min(len(st.session_state["scanned_items"]), 4))
            for idx, item in enumerate(st.session_state["scanned_items"]):
                c_target = sold_cols[idx % len(sold_cols)]
                stock_code = item['number'] if item['number'] else f"Row {idx+1}"
                with c_target:
                    use_item = st.checkbox(
                        f"Group #{g}: Include **{stock_code}** (NT$ {item['amount']:,.0f})", 
                        value=(g == 1),
                        key=f"g{g}_chk_v16_{idx}"
                    )
                    if use_item:
                        g_sold_total += item["amount"]
        else:
            st.info("Upload a screenshot above or enter stocks manually.")

        st.metric(f"Group #{g} Subtotal Proceeds", f"NT$ {g_sold_total:,.0f}")

        g_pct = st.slider(f"Group #{g} Reinvestment Budget Percentage (%)", min_value=1, max_value=100, value=100, key=f"g{g}_pct_v16")
        g_reinvest_budget = g_sold_total * (g_pct / 100.0)
        st.info(f"Group #{g} Available Reinvestment Budget ({g_pct}%): **NT$ {g_reinvest_budget:,.0f}**")

        st.write(f"**Group #{g}: Set Target Buy Stocks (Up to 4)**")
        g_buy_targets = []
        g_total_weight = 0.0

        for b in range(1, 5):
            b1, b2, b3 = st.columns([2, 2, 3])
            with b1:
                b_code = st.text_input(f"Group #{g} Buy #{b} Code", placeholder="e.g. 2330", key=f"g{g}_b_code_v16_{b}")
            with b2:
                b_price = st.number_input(f"Group #{g} Buy #{b} Set Price", min_value=0.0, value=0.0, step=0.5, key=f"g{g}_b_price_v16_{b}")
            with b3:
                b_weight = st.number_input(f"Group #{g} Buy #{b} Budget Allocation (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key=f"g{g}_b_weight_v16_{b}")

            if b_price > 0 and b_weight > 0:
                g_buy_targets.append({
                    "code": b_code if b_code else f"Target #{b}",
                    "price": b_price,
                    "weight": b_weight
                })
                g_total_weight += b_weight

        if g_total_weight > 100.0:
            st.error(f"⚠️ Group #{g} total target allocation is {g_total_weight:.1f}%, which exceeds 100%!")

        all_groups_data.append({
            "group_num": g,
            "budget": g_reinvest_budget,
            "targets": g_buy_targets,
            "weight_total": g_total_weight
        })

        st.divider()

    # 3. Calculation Output
    if st.button("Calculate All Groups Share Allocations", type="primary", key="btn_calc_all_groups_v16"):
        st.subheader("📊 Purchase Plan Summary Across All Groups")
        
        has_error = False
        for grp in all_groups_data:
            if grp["weight_total"] > 100.0:
                st.error(f"Group #{grp['group_num']} allocation exceeds 100%. Please adjust percentages.")
                has_error = True

        if not has_error:
            grand_total_reinvest = 0.0
            grand_total_spent = 0.0

            for grp in all_groups_data:
                g_num = grp["group_num"]
                g_budget = grp["budget"]
                grand_total_reinvest += g_budget
                
                st.markdown(f"#### 📂 Funding Group #{g_num} Calculation Results (Budget: NT$ {g_budget:,.0f})")
                
                if len(grp["targets"]) == 0:
                    st.caption("No target stocks entered for this group.")
                else:
                    res_cols = st.columns(min(len(grp["targets"]), 4))
                    g_spent = 0.0

                    for idx, target in enumerate(grp["targets"]):
                        col_target = res_cols[idx]
                        allocated_funds = g_budget * (target["weight"] / 100.0)
                        shares = int(allocated_funds // target["price"])
                        cost = shares * target["price"]
                        leftover = allocated_funds - cost
                        g_spent += cost

                        with col_target:
                            st.markdown(f"**🎯 Stock {target['code']}**")
                            st.write(f"**Allocated Budget ({target['weight']}%):** NT$ {allocated_funds:,.0f}")
                            st.write(f"**Set Price:** NT$ {target['price']:,.2f}")
                            st.metric(label="Shares to Buy (零股)", value=f"{shares:,} 股")
                            st.write(f"**Total Cost:** NT$ {cost:,.0f}")
                            st.write(f"**Leftover Cash:** NT$ {leftover:,.0f}")

                    grand_total_spent += g_spent
                    st.caption(f"💡 **Group #{g_num} Total Expenditure:** NT$ {g_spent:,.0f} | **Group Leftover Cash:** NT$ {g_budget - g_spent:,.0f}")
                st.write("---")

            st.success("✅ Multi-Group Share Allocations Complete!")
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Overall Reinvestment Budget", f"NT$ {grand_total_reinvest:,.0f}")
            with s2:
                st.metric("Overall Estimated Expenditure", f"NT$ {grand_total_spent:,.0f}")
            with s3:
                st.metric("Overall Unused Remaining Cash", f"NT$ {grand_total_reinvest - grand_total_spent:,.0f}")


# ==============================================================================
# TAB 2: MULTI-PERSON MULTI-STOCK BUDGET CALCULATOR
# ==============================================================================
with tab2:
    st.title("👥 Multi-Person & Multi-Stock Purchase Allocator")
    st.caption("Set up to 10 stocks with individual set prices and 舅舅 baseline budgets, plus daily ratio multipliers for 奶奶, 姨婆, 爸爸, and Lina.")

    # 1. Daily Ratio Multipliers
    st.header("Step 1: Daily Ratio Multipliers")
    st.caption("These multipliers scale 舅舅's baseline budget for each individual stock (e.g. 0.266 = 26.6% of 舅舅).")

    col_r2, col_r3, col_r4, col_r5 = st.columns(4)
    with col_r2:
        ratio_nainai = st.number_input("奶奶 Multiplier", min_value=0.0, max_value=5.0, value=0.266, step=0.001, format="%.4f", key="t2_r_nainai_v16")
    with col_r3:
        ratio_yipo = st.number_input("姨婆 Multiplier", min_value=0.0, max_value=5.0, value=0.150, step=0.001, format="%.4f", key="t2_r_yipo_v16")
    with col_r4:
        ratio_baba = st.number_input("爸爸 Multiplier", min_value=0.0, max_value=5.0, value=0.200, step=0.001, format="%.4f", key="t2_r_baba_v16")
    with col_r5:
        ratio_lina = st.number_input("Lina Multiplier", min_value=0.0, max_value=5.0, value=0.100, step=0.001, format="%.4f", key="t2_r_lina_v16")

    st.write("---")

    # 2. Multi-Stock Rows Input (Up to 10 Stocks)
    st.header("Step 2: Enter Stocks, Individual Prices, and 舅舅 Budgets (Up to 10 Stocks)")
    st.caption("Enter the parameters for up to 10 target stocks you plan to buy today.")

    stocks_to_buy = []

    for i in range(1, 11):
        c1, c2, c3 = st.columns([2, 2, 3])
        with c1:
            stk_code = st.text_input(f"Stock #{i} Code/Name", placeholder="e.g. 2330", key=f"t2_code_v16_{i}")
        with c2:
            stk_price = st.number_input(f"Stock #{i} Set Price (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"t2_price_v16_{i}")
        with c3:
            stk_budget = st.number_input(f"Stock #{i} 舅舅 Budget (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"t2_budget_v16_{i}")

        if stk_price > 0 and stk_budget > 0:
            stocks_to_buy.append({
                "row": i,
                "code": stk_code if stk_code else f"Stock #{i}",
                "price": stk_price,
                "jiujiu_budget": stk_budget
            })

    st.write("---")

    # 3. Execution & Output Table
    if st.button("Calculate All People & Stock Shares", type="primary", key="btn_calc_t2_v16"):
        if len(stocks_to_buy) == 0:
            st.error("Please enter at least one stock with a price > 0 and 舅舅 budget > 0.")
        else:
            people_info = [
                {"name": "舅舅 (Baseline)", "ratio": 1.0},
                {"name": "奶奶", "ratio": ratio_nainai},
                {"name": "姨婆", "ratio": ratio_yipo},
                {"name": "爸爸", "ratio": ratio_baba},
                {"name": "Lina", "ratio": ratio_lina},
            ]
            
            for stk in stocks_to_buy:
                st.subheader(f"📌 Stock Code: {stk['code']} (@ NT$ {stk['price']:,.2f})")
                
                people_cols = st.columns(5)
                stk_total_budget = 0.0
                stk_total_spent = 0.0

                for idx, person in enumerate(people_info):
                    r = person["ratio"]
                    p_budget = stk["jiujiu_budget"] * r
                    shares = int(p_budget // stk["price"])
                    cost = shares * stk["price"]
                    leftover = p_budget - cost

                    stk_total_budget += p_budget
                    stk_total_spent += cost

                    with people_cols[idx]:
                        st.markdown(f"#### 👤 {person['name']}")
                        st.caption(f"Multiplier: **{r:.4f}x**")
                        st.write(f"**Budget:** NT$ {p_budget:,.2f}")
                        st.metric(label="Shares to Buy (零股)", value=f"{shares:,} 股")
                        st.write(f"**Total Cost:** NT$ {cost:,.2f}")
                        st.write(f"**Leftover Cash:** NT$ {leftover:,.2f}")

                st.caption(f"💡 **Stock {stk['code']} Total Group Budget:** NT$ {stk_total_budget:,.2f} | **Total Group Cost:** NT$ {stk_total_spent:,.2f}")
                st.divider()

            st.success("✅ Multi-Person & Multi-Stock Share Allocations Complete!")

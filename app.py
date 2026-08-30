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
# 分頁 1: 賣出成交圖自動掃描與多組獨立再投資分配
# ==============================================================================
with tab1:
    st.title("📈 賣出成交圖自動掃描與多組獨立再投資試算")

    # 1. 截圖上傳與辨識區
    st.header("第一步：上傳愛利得賣出成交截圖")
    st.caption("請上傳賣出交割紀錄截圖，系統將自動擷取所有賣出股票與成交價金。")

    uploaded_file = st.file_uploader("選擇上傳截圖檔案", type=["png", "jpg", "jpeg"], key="tab1_uploader")

    if "scanned_items" not in st.session_state:
        st.session_state["scanned_items"] = []

    if uploaded_file is not None:
        st.image(uploaded_file, caption="已上傳之成交截圖", width=400)
        
        if st.button("🔍 辨識截圖並自動帶入股票資料", type="primary", key="btn_scan_t1"):
            with st.spinner("正在裁切標頭並進行文字辨識..."):
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
                            st.success(f"成功擷取 {len(extracted_list)} 筆股票與成交價金資料！")
                        else:
                            st.warning("未能自動辨識表格內容，請於下方手動輸入。")
                    else:
                        st.error("辨識伺服器忙碌中，請於下方手動輸入資料。")
                except Exception as e:
                    st.error(f"辨識發生錯誤：{e}")

    st.write("---")

    # 手動備用輸入區
    with st.expander("➕ 手動新增或修正賣出股票資料庫", expanded=not bool(st.session_state["scanned_items"])):
        col_m1, col_m2 = st.columns(2)
        for i in range(1, 11):
            target_col = col_m1 if i <= 5 else col_m2
            with target_col:
                sm1, sm2 = st.columns([1, 2])
                with sm1:
                    m_code = st.text_input(f"手動股票 #{i} 代號", placeholder="例如：2376", key=f"m_code_v14_{i}")
                with sm2:
                    m_amt = st.number_input(f"手動股票 #{i} 成交價金", min_value=0.0, value=0.0, step=1000.0, key=f"m_amt_v14_{i}")
                    if m_amt > 0 and m_code:
                        # 避免重複手動新增
                        if not any(x["number"] == m_code and x["amount"] == m_amt for x in st.session_state["scanned_items"]):
                            st.session_state["scanned_items"].append({"number": m_code, "amount": m_amt})

    # 2. 多組獨立資金分配區
    st.header("第二步：設定獨立資金組與買入目標（可新增多組獨立計算）")
    st.caption("您可以將特定的賣出股票（如 A、B）歸為一組分配給 C、D；另將（E、F）歸為另一組按不同比例分配給 C、D、G、H。")

    if "group_count" not in st.session_state:
        st.session_state["group_count"] = 2  # 預設提供 2 組

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("➕ 新增資金組別"):
            st.session_state["group_count"] += 1
            st.rerun()
    with col_btn2:
        if st.session_state["group_count"] > 1:
            if st.button("➖ 減少資金組別"):
                st.session_state["group_count"] -= 1
                st.rerun()

    all_groups_data = []

    for g in range(1, st.session_state["group_count"] + 1):
        st.markdown(f"### 📂 資金組別 #{g}")
        
        # 選擇此組包含的賣出股票
        st.subheader(f"組別 #{g}：選擇來源賣出股票")
        g_sold_total = 0.0
        
        if st.session_state["scanned_items"]:
            sold_cols = st.columns(min(len(st.session_state["scanned_items"]), 4))
            for idx, item in enumerate(st.session_state["scanned_items"]):
                c_target = sold_cols[idx % len(sold_cols)]
                stock_code = item['number'] if item['number'] else f"Row {idx+1}"
                with c_target:
                    use_item = st.checkbox(
                        f"組別#{g} 納入 **{stock_code}** (NT$ {item['amount']:,.0f})", 
                        value=(g == 1), # 預設組別1全選，其餘組別手動勾選
                        key=f"g{g}_chk_{idx}"
                    )
                    if use_item:
                        g_sold_total += item["amount"]
        else:
            st.info("請先上傳截圖或於下方手動輸入賣出股票資訊。")

        st.metric(f"組別 #{g} 賣出金額小計", f"NT$ {g_sold_total:,.0f}")

        # 設定再投資比例
        g_pct = st.slider(f"組別 #{g} 投入再投資比例 (%)", min_value=1, max_value=100, value=100, key=f"g{g}_pct")
        g_reinvest_budget = g_sold_total * (g_pct / 100.0)
        st.info(f"組別 #{g} 實際可用再投資預算（{g_pct}%）：**NT$ {g_reinvest_budget:,.0f}**")

        # 設定買入目標（最多 4 檔）
        st.write(f"**組別 #{g}：設定預計買入股票（最多 4 檔）**")
        g_buy_targets = []
        g_total_weight = 0.0

        for b in range(1, 5):
            b1, b2, b3 = st.columns([2, 2, 3])
            with b1:
                b_code = st.text_input(f"組別#{g} 買入#{b} 代號", placeholder="例如：2330", key=f"g{g}_b_code_{b}")
            with b2:
                b_price = st.number_input(f"組別#{g} 買入#{b} 掛單單價", min_value=0.0, value=0.0, step=0.5, key=f"g{g}_b_price_{b}")
            with b3:
                b_weight = st.number_input(f"組別#{g} 買入#{b} 分配比例 (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key=f"g{g}_b_weight_{b}")

            if b_price > 0 and b_weight > 0:
                g_buy_targets.append({
                    "code": b_code if b_code else f"目標 #{b}",
                    "price": b_price,
                    "weight": b_weight
                })
                g_total_weight += b_weight

        if g_total_weight > 100.0:
            st.error(f"⚠️ 組別 #{g} 的買入分配比例總和為 {g_total_weight:.1f}%，已超過 100%！")

        all_groups_data.append({
            "group_num": g,
            "budget": g_reinvest_budget,
            "targets": g_buy_targets,
            "weight_total": g_total_weight
        })

        st.divider()

    # 3. 執行全案總算
    if st.button("計算所有組別委託買入股數", type="primary", key="btn_calc_all_groups"):
        st.subheader("📊 各組別委託下單計畫總表")
        
        has_error = False
        for grp in all_groups_data:
            if grp["weight_total"] > 100.0:
                st.error(f"組別 #{grp['group_num']} 的分配比例超過 100%，請修正後再試算。")
                has_error = True

        if not has_error:
            grand_total_reinvest = 0.0
            grand_total_spent = 0.0

            for grp in all_groups_data:
                g_num = grp["group_num"]
                g_budget = grp["budget"]
                grand_total_reinvest += g_budget
                
                st.markdown(f"#### 📂 資金組別 #{g_num} 試算結果（可用預算：NT$ {g_budget:,.0f}）")
                
                if len(grp["targets"]) == 0:
                    st.caption("此組別未設定買入目標。")
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
                            st.markdown(f"**🎯 股票 {target['code']}**")
                            st.write(f"**分配預算 ({target['weight']}%):** NT$ {allocated_funds:,.0f}")
                            st.write(f"**掛單價:** NT$ {target['price']:,.2f}")
                            st.metric(label="可買入零股股數", value=f"{shares:,} 股")
                            st.write(f"**成交價金:** NT$ {cost:,.0f}")
                            st.write(f"**剩餘現金:** NT$ {leftover:,.0f}")

                    grand_total_spent += g_spent
                    st.caption(f"💡 **組別 #{g_num} 預估總花費：** NT$ {g_spent:,.0f} | **組別剩餘現金：** NT$ {g_budget - g_spent:,.0f}")
                st.write("---")

            st.success("✅ 全案多組別零股下單試算完成！")
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("全案再投資總預算", f"NT$ {grand_total_reinvest:,.0f}")
            with s2:
                st.metric("全案預估總支出金額", f"NT$ {grand_total_spent:,.0f}")
            with s3:
                st.metric("全案剩餘未用現金", f"NT$ {grand_total_reinvest - grand_total_spent:,.0f}")


# ==============================================================================
# 分頁 2: 多帳戶獨立買進計算器
# ==============================================================================
with tab2:
    st.title("👥 多帳戶獨立標的零股買進計算器")
    st.caption("設定最多 10 檔股票之單價與「舅舅」基準預算，並依照每日比例自動試算「奶奶、姨婆、爸爸、Lina」之買進股數。")

    # 1. 每日倍率設定區
    st.header("第一步：設定各帳戶相對於「舅舅」之預算倍率")
    st.caption("輸入各帳戶相對於舅舅預算的浮點數倍率（例如 0.266 代表舅舅預算之 26.6%）。")

    col_r2, col_r3, col_r4, col_r5 = st.columns(4)
    with col_r2:
        ratio_nainai = st.number_input("奶奶 倍率", min_value=0.0, max_value=5.0, value=0.266, step=0.001, format="%.4f", key="t2_r_nainai_v14")
    with col_r3:
        ratio_yipo = st.number_input("姨婆 倍率", min_value=0.0, max_value=5.0, value=0.150, step=0.001, format="%.4f", key="t2_r_yipo_v14")
    with col_r4:
        ratio_baba = st.number_input("爸爸 倍率", min_value=0.0, max_value=5.0, value=0.200, step=0.001, format="%.4f", key="t2_r_baba_v14")
    with col_r5:
        ratio_lina = st.number_input("Lina 倍率", min_value=0.0, max_value=5.0, value=0.100, step=0.001, format="%.4f", key="t2_r_lina_v14")

    st.write("---")

    # 2. 多股票獨立輸入區 (最多 10 檔)
    st.header("第二步：輸入買進股票代號、掛單單價與「舅舅」個案預算（最多 10 檔）")
    st.caption("請填寫今日預計下單之各股票詳細參數。")

    stocks_to_buy = []

    for i in range(1, 11):
        c1, c2, c3 = st.columns([2, 2, 3])
        with c1:
            stk_code = st.text_input(f"股票 #{i} 代號/名稱", placeholder="例如：2330", key=f"t2_code_v14_{i}")
        with c2:
            stk_price = st.number_input(f"股票 #{i} 掛單單價 (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"t2_price_v14_{i}")
        with c3:
            stk_budget = st.number_input(f"股票 #{i} 舅舅預算 (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"t2_budget_v14_{i}")

        if stk_price > 0 and stk_budget > 0:
            stocks_to_buy.append({
                "row": i,
                "code": stk_code if stk_code else f"股票 #{i}",
                "price": stk_price,
                "jiujiu_budget": stk_budget
            })

    st.write("---")

    # 3. 執行試算與多帳戶結果顯示
    if st.button("計算全帳戶委託股數", type="primary", key="btn_calc_t2_v14"):
        if len(stocks_to_buy) == 0:
            st.error("請至少輸入一檔買入單價 > 0 且舅舅預算 > 0 的股票。")
        else:
            people_info = [
                {"name": "舅舅（基準）", "ratio": 1.0},
                {"name": "奶奶", "ratio": ratio_nainai},
                {"name": "姨婆", "ratio": ratio_yipo},
                {"name": "爸爸", "ratio": ratio_baba},
                {"name": "Lina", "ratio": ratio_lina},
            ]
            
            for stk in stocks_to_buy:
                st.subheader(f"📌 股票代號：{stk['code']}（預計掛單價：NT$ {stk['price']:,.2f}）")
                
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
                        st.caption(f"分配倍率：**{r:.4f}x**")
                        st.write(f"**分配預算:** NT$ {p_budget:,.2f}")
                        st.metric(label="可買入零股股數", value=f"{shares:,} 股")
                        st.write(f"**實際花費:** NT$ {cost:,.2f}")
                        st.write(f"**剩餘未用現金:** NT$ {leftover:,.2f}")

                st.caption(f"💡 **股票 {stk['code']} 全帳戶合計預算：** NT$ {stk_total_budget:,.2f} | **全帳戶合計花費：** NT$ {stk_total_spent:,.2f}")
                st.divider()

            st.success("✅ 多帳戶零股下單試算完畢！")

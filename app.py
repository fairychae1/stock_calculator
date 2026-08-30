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

    # 2. 選擇計入預算之賣出股票
    st.header("第二步：勾選今日欲納入再投資預算的賣出股票")
    st.caption("請勾選今日實際賣出且欲將資金投入新股票的項目。")

    sold_total = 0.0

    if st.session_state["scanned_items"]:
        st.subheader("📋 截圖辨識結果")
        for idx, item in enumerate(st.session_state["scanned_items"]):
            stock_code = item['number'] if item['number'] else f"{idx+1}"
            use_stock = st.checkbox(
                label=f"納入 股票 **{stock_code}** — NT$ {item['amount']:,.0f}", 
                value=True, 
                key=f"chk_stock_num_v13_{idx}"
            )
            if use_stock:
                sold_total += item["amount"]
        st.write("---")

    with st.expander("➕ 手動輸入或修正賣出股票代號與金額", expanded=not bool(st.session_state["scanned_items"])):
        col_left, col_right = st.columns(2)
        manual_total = 0.0
        for i in range(1, 11):
            target_col = col_left if i <= 5 else col_right
            with target_col:
                s1, s2 = st.columns([1, 2])
                with s1:
                    st.text_input(f"股票代號/名稱 #{i}", placeholder="例如：2376", key=f"m_num_v13_{i}")
                with s2:
                    amt = st.number_input(f"股票 #{i} 成交價金 (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"m_amt_num_v13_{i}")
                    manual_total += amt
        sold_total += manual_total

    st.metric(label="已勾選之賣出總金額（可用資金池）", value=f"NT$ {sold_total:,.0f}")
    st.write("---")

    # 3. 再投資預算比例設定
    st.header("第三步：設定再投資預算比例")
    portfolio_pct = st.slider("預計投入再投資之金額比例 (%)", min_value=1, max_value=100, value=100, key="slider_t1_v13")
    total_reinvest_budget = sold_total * (portfolio_pct / 100.0)
    st.info(f"實際可用再投資總預算（{portfolio_pct}% 的 NT$ {sold_total:,.0f}）：**NT$ {total_reinvest_budget:,.0f}**")
    st.write("---")

    # 4. 目標買入股票分配設定
    st.header("第四步：設定欲買入目標股票（最多 6 檔）")
    st.caption("請輸入目標股票代號、預計買入掛單單價與資金分配百分比。")

    buy_rows = []
    total_weight = 0.0

    for i in range(1, 7):
        b1, b2, b3 = st.columns([2, 2, 3])
        with b1:
            b_name = st.text_input(f"買入目標 #{i} 代號/名稱", placeholder="例如：2330", key=f"buy_num_v13_{i}")
        with b2:
            b_price = st.number_input(f"買入目標 #{i} 掛單單價 (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"buy_price_num_v13_{i}")
        with b3:
            b_pct = st.number_input(f"買入目標 #{i} 預算分配比例 (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0, key=f"buy_pct_num_v13_{i}")
        
        if b_price > 0 and b_pct > 0:
            buy_rows.append({
                "slot": i,
                "name": b_name if b_name else f"目標股票 #{i}",
                "price": b_price,
                "pct": b_pct
            })
            total_weight += b_pct

    if total_weight > 100.0:
        st.error(f"⚠️ 買入分配比例總和為 {total_weight:.1f}%，已超過 100%！請調整比例。")
    elif total_weight < 100.0 and len(buy_rows) > 0:
        st.warning(f"ℹ️ 買入分配比例總和為 {total_weight:.1f}%。剩餘未分配比例：{100.0 - total_weight:.1f}%")

    st.write("---")

    if st.button("計算委託買入股數", type="primary", key="btn_calc_t1_v13"):
        if total_reinvest_budget <= 0:
            st.error("再投資總預算必須大於 0，請確認賣出金額。")
        elif len(buy_rows) == 0:
            st.error("請至少輸入一檔買入單價 > 0 且分配比例 > 0 的目標股票。")
        elif total_weight > 100.0:
            st.error("分配比例總和超過 100%，無法計算。")
        else:
            st.subheader("📊 委託下單計畫明細")
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
                    st.markdown(f"### 🎯 股票 {item['name']}")
                    st.write(f"**分配預算 ({item['pct']}%):** NT$ {allocated_funds:,.0f}")
                    st.write(f"**預計買入單價:** NT$ {item['price']:,.2f}")
                    st.metric(label="可買入零股股數", value=f"{shares:,} 股")
                    st.write(f"**預估花費成交價金:** NT$ {cost:,.0f}")
                    st.write(f"**剩餘未用現金:** NT$ {leftover:,.0f}")
                    st.divider()
                    
            total_leftover_cash = total_reinvest_budget - grand_total_spent
            st.success("✅ 下單股數試算完成！")
            summary_c1, summary_c2, summary_c3 = st.columns(3)
            with summary_c1:
                st.metric("再投資總預算", f"NT$ {total_reinvest_budget:,.0f}")
            with summary_c2:
                st.metric("預估總支出金額", f"NT$ {grand_total_spent:,.0f}")
            with summary_c3:
                st.metric("全案剩餘未用現金", f"NT$ {total_leftover_cash:,.0f}")


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
        ratio_nainai = st.number_input("奶奶 倍率", min_value=0.0, max_value=5.0, value=0.266, step=0.001, format="%.4f", key="t2_r_nainai_v13")
    with col_r3:
        ratio_yipo = st.number_input("姨婆 倍率", min_value=0.0, max_value=5.0, value=0.150, step=0.001, format="%.4f", key="t2_r_yipo_v13")
    with col_r4:
        ratio_baba = st.number_input("爸爸 倍率", min_value=0.0, max_value=5.0, value=0.200, step=0.001, format="%.4f", key="t2_r_baba_v13")
    with col_r5:
        ratio_lina = st.number_input("Lina 倍率", min_value=0.0, max_value=5.0, value=0.100, step=0.001, format="%.4f", key="t2_r_lina_v13")

    st.write("---")

    # 2. 多股票獨立輸入區 (最多 10 檔)
    st.header("第二步：輸入買進股票代號、掛單單價與「舅舅」個案預算（最多 10 檔）")
    st.caption("請填寫今日預計下單之各股票詳細參數。")

    stocks_to_buy = []

    for i in range(1, 11):
        c1, c2, c3 = st.columns([2, 2, 3])
        with c1:
            stk_code = st.text_input(f"股票 #{i} 代號/名稱", placeholder="例如：2330", key=f"t2_code_v13_{i}")
        with c2:
            stk_price = st.number_input(f"股票 #{i} 掛單單價 (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"t2_price_v13_{i}")
        with c3:
            stk_budget = st.number_input(f"股票 #{i} 舅舅預算 (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"t2_budget_v13_{i}")

        if stk_price > 0 and stk_budget > 0:
            stocks_to_buy.append({
                "row": i,
                "code": stk_code if stk_code else f"股票 #{i}",
                "price": stk_price,
                "jiujiu_budget": stk_budget
            })

    st.write("---")

    # 3. 執行試算與多帳戶結果顯示
    if st.button("計算全帳戶委託股數", type="primary", key="btn_calc_t2_v13"):
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

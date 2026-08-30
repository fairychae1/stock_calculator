import streamlit as st

# Page configuration
st.set_page_config(page_title="Portfolio Budget Allocator", layout="wide", page_icon="📈")
st.title("📈 Multi-Stock Rebalancing Calculator")

# 1. Screenshot Reference Section
st.header("Step 1: Sales Screenshot Reference (Optional)")
uploaded_file = st.file_uploader("Upload screenshot from 愛利得 for quick reference", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Sales Screenshot Reference", width=600)

st.write("---")

# 2. Sold Stocks Input Section (Up to 10 Stocks)
st.header("Step 2: Sold Stocks Earnings (Up to 10 Stocks)")
st.caption("Enter the ticker/name and 成交價金 for up to 10 stocks you sold.")

sold_total = 0.0

# Create 2 columns of 5 input slots each for a clean grid layout
col_left, col_right = st.columns(2)

for i in range(1, 11):
    target_col = col_left if i <= 5 else col_right
    with target_col:
        s_col1, s_col2 = st.columns([1, 2])
        with s_col1:
            st.text_input(f"Sold #{i} Name", value=f"Stock {i}" if i <= 2 else "", key=f"sold_name_{i}")
        with s_col2:
            amount = st.number_input(f"Sold #{i} Amount (NTD)", min_value=0.0, value=0.0, step=1000.0, key=f"sold_amt_{i}")
            sold_total += amount

st.metric(label="Total Earnings from Sales (Sum of Sold Stocks)", value=f"NT$ {sold_total:,.0f}")

st.write("---")

# 3. Overall Reinvestment Budget Allocation
st.header("Step 3: Reinvestment Budget Allocation")

portfolio_pct = st.slider("Percentage of total sales earnings to reinvest (%)", min_value=1, max_value=100, value=100)
total_reinvest_budget = sold_total * (portfolio_pct / 100.0)

st.info(f"Available Reinvestment Budget ({portfolio_pct}% of NT$ {sold_total:,.0f}): **NT$ {total_reinvest_budget:,.0f}**")

st.write("---")

# 4. Target Buy Allocation Section (Up to 6 Stocks)
st.header("Step 4: Target Buy Allocation (Up to 6 Stocks)")
st.caption("Enter up to 6 target stocks, their set buy price, and the share of your reinvestment budget to allocate to each.")

buy_rows = []
total_weight = 0.0

# Layout as 6 rows
for i in range(1, 7):
    b1, b2, b3 = st.columns([2, 2, 3])
    with b1:
        b_name = st.text_input(f"Buy #{i} Code/Name", value=f"Target {i}" if i <= 2 else "", key=f"buy_name_{i}")
    with b2:
        b_price = st.number_input(f"Buy #{i} Set Price (NTD)", min_value=0.0, value=0.0, step=0.5, key=f"buy_price_{i}")
    with b3:
        b_pct = st.number_input(f"Buy #{i} Budget Allocation (%)", min_value=0.0, max_value=100.0, value=50.0 if i <= 2 else 0.0, step=5.0, key=f"buy_pct_{i}")
    
    if b_price > 0 and b_pct > 0:
        buy_rows.append({
            "slot": i,
            "name": b_name if b_name else f"Stock #{i}",
            "price": b_price,
            "pct": b_pct
        })
        total_weight += b_pct

# Allocation Percentage Warnings
if total_weight > 100.0:
    st.error(f"⚠️ Total target allocation adds up to {total_weight:.1f}%, which exceeds 100%! Please reduce allocations.")
elif total_weight < 100.0 and len(buy_rows) > 0:
    st.warning(f"ℹ️ Total target allocation adds up to {total_weight:.1f}%. Unallocated budget: {100.0 - total_weight:.1f}%")

st.write("---")

# 5. Calculation Results
if st.button("Calculate Share Allocations", type="primary"):
    if total_reinvest_budget <= 0:
        st.error("Total reinvestment budget must be greater than zero. Please enter sold stock amounts.")
    elif len(buy_rows) == 0:
        st.error("Please enter at least one target stock with a price > 0 and allocation % > 0.")
    elif total_weight > 100.0:
        st.error("Cannot calculate while allocation total exceeds 100%.")
    else:
        st.subheader("📊 Purchase Plan Summary")
        
        grand_total_spent = 0.0
        
        # Display results in structured grid columns
        res_cols = st.columns(min(len(buy_rows), 3))
        
        for index, item in enumerate(buy_rows):
            col_target = res_cols[index % len(res_cols)]
            
            allocated_funds = total_reinvest_budget * (item["pct"] / 100.0)
            shares = int(allocated_funds // item["price"])
            cost = shares * item["price"]
            leftover = allocated_funds - cost
            grand_total_spent += cost
            
            with col_target:
                st.markdown(f"### 🎯 {item['name']}")
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

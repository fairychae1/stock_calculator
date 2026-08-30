import streamlit as st

# Page configuration
st.set_page_config(page_title="Proceeds Stock Allocator", layout="centered", page_icon="📈")
st.title("📈 Morning Stock Sales Allocator")

# 1. Image Upload (Visual Reference Only)
st.header("Step 1: Screenshot Reference (Optional)")
uploaded_file = st.file_uploader("Upload screenshot from 愛利得 for reference", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Sales Screenshot Reference", use_container_width=True)

# 2. Input Sales Earnings
st.write("---")
st.header("Step 2: Enter Sales Proceeds")

proceeds = st.number_input(
    "Total money gained from sales (成交價金) in NTD:", 
    min_value=0.0, 
    value=50000.0, 
    step=1000.0
)

# 3. Allocation & Target Stock
st.write("---")
st.header("Step 3: Set Allocation & Stock Details")

col1, col2 = st.columns(2)
with col1:
    portion = st.slider("Percentage of proceeds to use (%)", min_value=1, max_value=100, value=25)
with col2:
    target_stock = st.text_input("Target Stock Code/Name", value="2330")

calculated_budget = proceeds * (portion / 100.0)
st.info(f"Target Buying Budget ({portion}% of NT$ {proceeds:,.0f}): **NT$ {calculated_budget:,.0f}**")

# 4. Manual Price Input & Share Calculation
st.write("---")
st.header("Step 4: Calculate Shares to Buy")

manual_price = st.number_input(f"Enter target price for {target_stock} (NTD):", min_value=0.1, value=950.0, step=0.5)

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

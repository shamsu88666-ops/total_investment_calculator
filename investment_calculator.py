import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Total Investment Return Calculator", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1116 !important; color: #E5E7EB !important; }
    .input-card { background-color: #1A2233 !important; padding: 25px; border-radius: 10px; border: 1px solid #374151; color: #E5E7EB !important; margin-bottom: 20px; }
    .result-card { background-color: #1F2937 !important; padding: 20px; border-radius: 10px; border: 1px solid #374151; color: #E5E7EB !important; }
    .stButton>button { background-color: #22C55E !important; color: white !important; width: 100%; border: none; font-weight: bold; height: 3.5em; border-radius: 8px; font-size: 16px; }
    .metric-box { background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #22C55E; margin: 10px 0; }
    .metric-label { color: #9CA3AF; font-size: 14px; margin-bottom: 5px; }
    .metric-value { color: #22C55E; font-size: 28px; font-weight: bold; font-family: 'Courier New', monospace; }
    label, p, span, h1, h2, h3, h4, div { color: #E5E7EB !important; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE FUNCTIONS ---
def calculate_sip_future_value(sip_amount, annual_return, years):
    if sip_amount <= 0: return 0
    annual_rate = annual_return / 100
    monthly_rate = (1 + annual_rate) ** (1/12) - 1
    months = years * 12
    if monthly_rate > 0:
        future_value = sip_amount * ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
    else:
        future_value = sip_amount * months
    return future_value

def calculate_lumpsum_future_value(lumpsum_amount, annual_return, years):
    if lumpsum_amount <= 0: return 0
    annual_rate = annual_return / 100
    future_value = lumpsum_amount * (1 + annual_rate) ** years
    return future_value

def format_currency(amount):
    return f"₹ {amount:,.0f}"

# --- EXCEL REPORT FUNCTION (ഇത് മുകളിലേക്ക് മാറ്റി) ---
def create_excel_report(results):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        title_fmt = workbook.add_format({'bold': True, 'font_size': 16})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1})
        currency_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1})
        normal_fmt = workbook.add_format({'border': 1})
        
        worksheet = workbook.add_worksheet('Summary')
        worksheet.write('A1', 'Investment Summary Report', title_fmt)
        worksheet.write('A2', f'Generated on: {date.today()}')
        
        worksheet.write('A4', 'Input Parameters', header_fmt)
        worksheet.write('A5', 'Monthly SIP Amount', normal_fmt)
        worksheet.write('B5', results['sip_amount'], currency_fmt)
        worksheet.write('A6', 'Lumpsum Amount', normal_fmt)
        worksheet.write('B6', results['lumpsum_amount'], currency_fmt)
        
        worksheet.write('A10', 'Results Summary', header_fmt)
        worksheet.write('A11', 'Total Investment', normal_fmt)
        worksheet.write('B11', results['total_investment'], currency_fmt)
        worksheet.write('A13', 'Total Wealth Created', normal_fmt)
        worksheet.write('B13', results['total_future'], currency_fmt)

        # Year-wise growth Table
        worksheet.write('A15', 'Year-wise Growth', header_fmt)
        years_list = list(range(1, results['investment_years'] + 1))
        for idx, year in enumerate(years_list):
            row = 16 + idx
            s_val = calculate_sip_future_value(results['sip_amount'], results['expected_return'], year)
            l_val = calculate_lumpsum_future_value(results['lumpsum_amount'], results['expected_return'], year)
            worksheet.write(row, 0, year, normal_fmt)
            worksheet.write(row, 1, s_val, currency_fmt)
            worksheet.write(row, 2, l_val, currency_fmt)
            worksheet.write(row, 3, s_val + l_val, currency_fmt)

    return buffer.getvalue()

# --- UI SECTION ---
st.markdown("<h1 style='text-align: center;'>Total Investment Return Calculator</h1>", unsafe_allow_html=True)
st.markdown('<div class="input-card">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    sip_amount = st.number_input("Monthly SIP Amount (₹)", value=5000, step=500)
with col2:
    lumpsum_amount = st.number_input("One-time Lumpsum Amount (₹)", value=50000, step=1000)

col3, col4 = st.columns(2)
with col3:
    investment_years = st.number_input("Investment Period (Years)", min_value=1, value=10)
with col4:
    expected_return = st.number_input("Expected Annual Return (%)", value=12.0)

calculate_btn = st.button("Calculate Returns")
st.markdown('</div>', unsafe_allow_html=True)

if calculate_btn:
    sip_future = calculate_sip_future_value(sip_amount, expected_return, investment_years)
    lumpsum_future = calculate_lumpsum_future_value(lumpsum_amount, expected_return, investment_years)
    total_future = sip_future + lumpsum_future
    total_investment = (sip_amount * 12 * investment_years) + lumpsum_amount
    total_return = total_future - total_investment
    
    st.session_state.results = {
        'sip_amount': sip_amount, 'lumpsum_amount': lumpsum_amount,
        'investment_years': investment_years, 'expected_return': expected_return,
        'sip_future': sip_future, 'lumpsum_future': lumpsum_future,
        'total_future': total_future, 'total_investment': total_investment,
        'total_return': total_return
    }

    # Display Results Metrics...
    st.success(f"Total Wealth Created: {format_currency(total_future)}")
    
    # Chart
    years = list(range(1, investment_years + 1))
    chart_data = pd.DataFrame({
        'Year': years,
        'SIP Value': [calculate_sip_future_value(sip_amount, expected_return, y) for y in years],
        'Lumpsum Value': [calculate_lumpsum_future_value(lumpsum_amount, expected_return, y) for y in years]
    }).set_index('Year')
    st.line_chart(chart_data)

    # Download Button
    st.download_button(
        label="Download Excel Report",
        data=create_excel_report(st.session_state.results),
        file_name=f"Investment_Report_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

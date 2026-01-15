import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io
import xlsxwriter  # വീണ്ടും ഇംപോർട്ട് ചേർത്തു

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Total Investment Return Calculator", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CORE CALCULATION FUNCTIONS (EFFECTIVE RETURN) ---
def calculate_sip_future_value(sip_amount, annual_return, years):
    """Calculate future value of SIP using EFFECTIVE MONTHLY RETURN"""
    if sip_amount <= 0:
        return 0
    
    annual_rate = annual_return / 100
    monthly_rate = (1 + annual_rate) ** (1/12) - 1
    months = years * 12
    
    if monthly_rate > 0:
        future_value = sip_amount * ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
    else:
        future_value = sip_amount * months
    
    return future_value

def calculate_lumpsum_future_value(lumpsum_amount, annual_return, years):
    """Calculate future value of one-time lumpsum using EFFECTIVE RETURN"""
    if lumpsum_amount <= 0:
        return 0
    
    annual_rate = annual_return / 100
    future_value = lumpsum_amount * (1 + annual_rate) ** years
    return future_value

def format_currency(amount):
    """Format amount as Indian Rupees"""
    return f"₹ {amount:,.0f}"

# --- EXCEL REPORT FUNCTION (മുൻപ് പ്രഖ്യാപിച്ചു) ---
def create_excel_report(results):
    """Create Excel report with detailed breakdown"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#E5E7EB', 'bg_color': '#1A2233'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1})
        currency_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1, 'font_color': '#E5E7EB', 'bg_color': '#1F2937'})
        normal_fmt = workbook.add_format({'border': 1, 'font_color': '#E5E7EB', 'bg_color': '#1F2937'})
        
        # Summary Sheet
        worksheet = workbook.add_worksheet('Summary')
        worksheet.write('A1', 'Investment Summary Report', title_fmt)
        worksheet.write('A2', f'Generated on: {date.today()}')  # തീയതി ഫോർമാറ്റ് ശരിയാക്കി
        
        worksheet.write('A4', 'Input Parameters', header_fmt)
        worksheet.write('A5', 'Monthly SIP Amount', normal_fmt)
        worksheet.write('B5', results['sip_amount'], currency_fmt)
        worksheet.write('A6', 'Lumpsum Amount', normal_fmt)
        worksheet.write('B6', results['lumpsum_amount'], currency_fmt)
        worksheet.write('A7', 'Investment Period (Years)', normal_fmt)
        worksheet.write('B7', results['investment_years'], normal_fmt)
        worksheet.write('A8', 'Expected Annual Return (%)', normal_fmt)
        worksheet.write('B8', results['expected_return'], normal_fmt)
        
        worksheet.write('A10', 'Results Summary', header_fmt)
        worksheet.write('A11', 'Total Investment', normal_fmt)
        worksheet.write('B11', results['total_investment'], currency_fmt)
        worksheet.write('A12', 'Total Returns', normal_fmt)
        worksheet.write('B12', results['total_return'], currency_fmt)
        worksheet.write('A13', 'Total Wealth Created', normal_fmt)
        worksheet.write('B13', results['total_future'], currency_fmt)
        
        # Year-wise breakdown
        worksheet.write('A15', 'Year-wise Growth', header_fmt)
        
        years = list(range(1, results['investment_years'] + 1))
        worksheet.write('A16', 'Year', header_fmt)
        worksheet.write('B16', 'SIP Value', header_fmt)
        worksheet.write('C16', 'Lumpsum Value', header_fmt)
        worksheet.write('D16', 'Total Value', header_fmt)
        
        for idx, year in enumerate(years):
            row = 17 + idx
            sip_val = calculate_sip_future_value(results['sip_amount'], results['expected_return'], year)
            lump_val = calculate_lumpsum_future_value(results['lumpsum_amount'], results['expected_return'], year)
            total_val = sip_val + lump_val
            
            worksheet.write(f'A{row}', year, normal_fmt)
            worksheet.write(f'B{row}', sip_val, currency_fmt)
            worksheet.write(f'C{row}', lump_val, currency_fmt)
            worksheet.write(f'D{row}', total_val, currency_fmt)
        
        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:D', 20)
        
        # Add chart
        chart = workbook.add_chart({'type': 'line'})
        chart.add_series({
            'name': 'SIP Value',
            'categories': f'=Summary!$A$17:$A${16+len(years)}',
            'values': f'=Summary!$B$17:$B${16+len(years)}',
            'line': {'color': '#22C55E'}
        })
        chart.add_series({
            'name': 'Lumpsum Value',
            'categories': f'=Summary!$A$17:$A${16+len(years)}',
            'values': f'=Summary!$C$17:$C${16+len(years)}',
            'line': {'color': '#3B82F6'}
        })
        chart.add_series({
            'name': 'Total Value',
            'categories': f'=Summary!$A$17:$A${16+len(years)}',
            'values': f'=Summary!$D$17:$D${16+len(years)}',
            'line': {'color': '#F59E0B'}
        })
        
        chart.set_title({'name': 'Investment Growth Over Time'})
        chart.set_x_axis({'name': 'Years'})
        chart.set_y_axis({'name': 'Value (₹)'})
        chart.set_size({'width': 720, 'height': 480})
        
        worksheet.insert_chart('F4', chart)
    
    return buffer.getvalue()

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1116 !important; color: #E5E7EB !important; }
    .main { background-color: #0E1116 !important; }
    .block-container { padding-top: 2rem !important; }
    .input-card { background-color: #1A2233 !important; padding: 25px; border-radius: 10px; border: 1px solid #374151; color: #E5E7EB !important; margin-bottom: 20px; }
    .result-card { background-color: #1F2937 !important; padding: 20px; border-radius: 10px; border: 1px solid #374151; color: #E5E7EB !important; }
    .stButton>button { background-color: #22C55E !important; color: white !important; width: 100%; border: none; font-weight: bold; height: 3.5em; border-radius: 8px; font-size: 16px; }
    .stButton>button:hover { background-color: #16a34a !important; }
    .metric-box { background-color: #1F2937; padding: 15px; border-radius: 8px; border-left: 5px solid #22C55E; margin: 10px 0; }
    .metric-label { color: #9CA3AF; font-size: 14px; margin-bottom: 5px; }
    .metric-value { color: #22C55E; font-size: 28px; font-weight: bold; font-family: 'Courier New', monospace; }
    label, p, span, h1, h2, h3, h4, div { color: #E5E7EB !important; }
    .stNumberInput label { color: #E5E7EB !important; font-weight: 500; }
    .stSlider label { color: #E5E7EB !important; font-weight: 500; }
    footer { visibility: hidden; }
    .header-text { text-align: center; color: #E5E7EB; }
    </style>
    """, unsafe_allow_html=True)

# --- MAIN APP HEADER ---
st.markdown("<h1 style='text-align: center; color: #E5E7EB;'>Total Investment Return Calculator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF; font-size: 16px;'>Calculate combined returns from SIP and Lumpsum investments</p>", unsafe_allow_html=True)

# --- INPUT SECTION ---
with st.container():
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 SIP Investment")
        sip_amount = st.number_input("Monthly SIP Amount (₹)", min_value=0, value=5000, step=500, help="Enter monthly SIP investment amount")
    
    with col2:
        st.markdown("### 💰 Lumpsum Investment")
        lumpsum_amount = st.number_input("One-time Lumpsum Amount (₹)", min_value=0, value=50000, step=1000, help="Enter one-time lumpsum investment amount")
    
    st.markdown("### ⏱️ Investment Details")
    col3, col4 = st.columns(2)
    
    with col3:
        investment_years = st.number_input("Investment Period (Years)", min_value=1, max_value=50, value=10, step=1, help="Number of years you plan to stay invested")
    
    with col4:
        expected_return = st.number_input("Expected Annual Return (%)", min_value=0.1, max_value=50.0, value=12.0, step=0.5, help="Expected annual rate of return (effective rate)")
    
    calculate_btn = st.button("Calculate Returns")
    st.markdown('</div>', unsafe_allow_html=True)

# --- CALCULATE AND DISPLAY RESULTS ---
if calculate_btn:
    # Calculate individual components
    sip_future = calculate_sip_future_value(sip_amount, expected_return, investment_years)
    lumpsum_future = calculate_lumpsum_future_value(lumpsum_amount, expected_return, investment_years)
    
    # Combined values
    total_future = sip_future + lumpsum_future
    total_investment = (sip_amount * 12 * investment_years) + lumpsum_amount
    total_return = total_future - total_investment
    
    # Store in session state
    st.session_state.results = {
        'sip_amount': sip_amount,
        'lumpsum_amount': lumpsum_amount,
        'investment_years': investment_years,
        'expected_return': expected_return,
        'sip_future': sip_future,
        'lumpsum_future': lumpsum_future,
        'total_future': total_future,
        'total_investment': total_investment,
        'total_return': total_return
    }
    
    # Display results
    st.markdown("### 📊 Investment Results")
    
    # Individual Results
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        if sip_amount > 0:
            st.markdown(f"""
                <div class='result-card'>
                    <h4 style='color: #22C55E; margin-bottom: 15px;'>💸 SIP Results</h4>
                    <div class='metric-box'>
                        <div class='metric-label'>Total Invested (SIP)</div>
                        <div class='metric-value'>{format_currency(sip_amount * 12 * investment_years)}</div>
                    </div>
                    <div class='metric-box'>
                        <div class='metric-label'>SIP Future Value</div>
                        <div class='metric-value'>{format_currency(sip_future)}</div>
                    </div>
                    <div class='metric-box'>
                        <div class='metric-label'>SIP Returns</div>
                        <div class='metric-value'>{format_currency(sip_future - (sip_amount * 12 * investment_years))}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No SIP investment entered")
    
    with col_res2:
        if lumpsum_amount > 0:
            st.markdown(f"""
                <div class='result-card'>
                    <h4 style='color: #22C55E; margin-bottom: 15px;'>💰 Lumpsum Results</h4>
                    <div class='metric-box'>
                        <div class='metric-label'>Total Invested (Lumpsum)</div>
                        <div class='metric-value'>{format_currency(lumpsum_amount)}</div>
                    </div>
                    <div class='metric-box'>
                        <div class='metric-label'>Lumpsum Future Value</div>
                        <div class='metric-value'>{format_currency(lumpsum_future)}</div>
                    </div>
                    <div class='metric-box'>
                        <div class='metric-label'>Lumpsum Returns</div>
                        <div class='metric-value'>{format_currency(lumpsum_future - lumpsum_amount)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No Lumpsum investment entered")
    
    # Combined Results
    st.markdown("### 💎 Combined Portfolio Value")
    
    if sip_amount > 0 or lumpsum_amount > 0:
        col_total1, col_total2, col_total3 = st.columns(3)
        
        with col_total1:
            st.markdown(f"""
                <div class='metric-box' style='background-color: #1A2233; border-left: 5px solid #F59E0B;'>
                    <div class='metric-label'>Total Investment</div>
                    <div class='metric-value' style='color: #F59E0B;'>{format_currency(total_investment)}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_total2:
            st.markdown(f"""
                <div class='metric-box' style='background-color: #1A2233; border-left: 5px solid #3B82F6;'>
                    <div class='metric-label'>Total Returns</div>
                    <div class='metric-value' style='color: #3B82F6;'>{format_currency(total_return)}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_total3:
            st.markdown(f"""
                <div class='metric-box' style='background-color: #1A2233; border-left: 5px solid #22C55E;'>
                    <div class='metric-label'>Total Wealth Created</div>
                    <div class='metric-value' style='color: #22C55E; font-size: 32px;'>{format_currency(total_future)}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Year-wise breakdown chart
    st.markdown("### 📈 Investment Growth Chart")
    
    # Create year-wise data
    years = list(range(1, investment_years + 1))
    sip_corpus = [calculate_sip_future_value(sip_amount, expected_return, year) for year in years]
    lumpsum_corpus = [calculate_lumpsum_future_value(lumpsum_amount, expected_return, year) for year in years]
    total_corpus = [s + l for s, l in zip(sip_corpus, lumpsum_corpus)]
    
    # Create DataFrame for chart
    chart_data = pd.DataFrame({
        'Year': years,
        'SIP Value': sip_corpus,
        'Lumpsum Value': lumpsum_corpus,
        'Total Value': total_corpus
    })
    
    chart_data = chart_data.set_index('Year')
    
    # Display line chart
    st.line_chart(chart_data, color=['#22C55E', '#3B82F6', '#F59E0B'], height=400)
    
    # Download button
    st.markdown("### 📥 Download Report")
    download_btn = st.download_button(
        label="Download Excel Report",
        data=create_excel_report(st.session_state.results),
        file_name=f"Investment_Report_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- SIDEBAR INFO ---
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("This calculator helps you plan your investments by showing: - Individual returns from SIP and Lumpsum - Combined portfolio value - Year-wise growth visualization - Downloadable detailed report")
    
    st.markdown("### 🎨 Features")
    st.markdown("Dark theme optimized for all devices Works in both light and dark modes Clear visibility of all text Mobile responsive design")
    
    st.markdown("### 📊 Assumptions")
    st.markdown("SIP investments made at beginning of month Returns compounded monthly using **effective rate** Inflation not considered")

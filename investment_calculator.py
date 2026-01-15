import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io
import xlsxwriter

# --- CORE CALCULATION FUNCTIONS ---
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
    """Create Excel report with proper alignment and visible text"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats - വെള്ള ബാക്ക്ഗ്രൗണ്ട് + കറുത്ത ടെക്സ്റ്റ്
        title_fmt = workbook.add_format({
            'bold': True, 
            'font_size': 16, 
            'font_color': '#000000',
            'bg_color': '#E2EFDA',
            'align': 'center',
            'valign': 'vcenter'
        })
        
        header_fmt = workbook.add_format({
            'bold': True, 
            'bg_color': '#22C55E', 
            'font_color': 'white', 
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        currency_fmt = workbook.add_format({
            'num_format': '₹ #,##0.00',
            'border': 1, 
            'font_color': '#000000',
            'bg_color': '#FFFFFF',
            'align': 'right',
            'valign': 'vcenter'
        })
        
        normal_fmt = workbook.add_format({
            'border': 1, 
            'font_color': '#000000',
            'bg_color': '#FFFFFF',
            'align': 'left',
            'valign': 'vcenter'
        })
        
        number_fmt = workbook.add_format({
            'border': 1, 
            'font_color': '#000000',
            'bg_color': '#FFFFFF',
            'align': 'right',
            'valign': 'vcenter'
        })
        
        percent_fmt = workbook.add_format({
            'num_format': '0.00%',
            'border': 1,
            'font_color': '#000000',
            'bg_color': '#FFFFFF',
            'align': 'right',
            'valign': 'vcenter'
        })
        
        # Summary Sheet
        worksheet = workbook.add_worksheet('Summary')
        
        # വീതിയുള്ള കോലങ്ങൾ
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:D', 20)
        
        # ടൈറ്റിൽ
        worksheet.merge_range('A1:D1', 'Investment Summary Report', title_fmt)
        worksheet.merge_range('A2:D2', f'Generated on: {date.today().strftime("%d-%B-%Y")}', normal_fmt)
        
        # ഇൻപുട്ട് പാരാമീറ്ററുകൾ
        worksheet.merge_range('A4:B4', 'Input Parameters', header_fmt)
        
        input_data = [
            ['Monthly SIP Amount', results['sip_amount']],
            ['Lumpsum Amount', results['lumpsum_amount']],
            ['Investment Period (Years)', results['investment_years']],
            ['Expected Annual Return (%)', results['expected_return'] / 100]
        ]
        
        for idx, (label, value) in enumerate(input_data):
            row = 5 + idx
            worksheet.write(f'A{row}', label, normal_fmt)
            if 'Amount' in label:
                worksheet.write(f'B{row}', value, currency_fmt)
            elif 'Return' in label:
                worksheet.write(f'B{row}', value, percent_fmt)
            else:
                worksheet.write(f'B{row}', value, number_fmt)
        
        # റിസൾട്ടുകൾ
        result_start_row = 10
        worksheet.merge_range(f'A{result_start_row}:B{result_start_row}', 'Results Summary', header_fmt)
        
        result_data = [
            ['Total Investment', results['total_investment']],
            ['Total Returns', results['total_return']],
            ['Total Wealth Created', results['total_future']]
        ]
        
        for idx, (label, value) in enumerate(result_data):
            row = result_start_row + 1 + idx
            worksheet.write(f'A{row}', label, normal_fmt)
            worksheet.write(f'B{row}', value, currency_fmt)
        
        # വർഷ-wise ബ്രേക്ക്ഡൗൺ
        breakdown_start_row = 15
        worksheet.merge_range(f'A{breakdown_start_row}:D{breakdown_start_row}', 'Year-wise Growth', header_fmt)
        
        breakdown_header_row = breakdown_start_row + 1
        headers = ['Year', 'SIP Value', 'Lumpsum Value', 'Total Value']
        for col, header in enumerate(headers):
            worksheet.write(breakdown_header_row, col, header, header_fmt)
        
        years = list(range(1, results['investment_years'] + 1))
        for idx, year in enumerate(years):
            row = breakdown_header_row + 1 + idx
            sip_val = calculate_sip_future_value(results['sip_amount'], results['expected_return'], year)
            lump_val = calculate_lumpsum_future_value(results['lumpsum_amount'], results['expected_return'], year)
            total_val = sip_val + lump_val
            
            worksheet.write(row, 0, year, number_fmt)
            worksheet.write(row, 1, sip_val, currency_fmt)
            worksheet.write(row, 2, lump_val, currency_fmt)
            worksheet.write(row, 3, total_val, currency_fmt)
        
        # ചാർട്ട്
        chart_row = breakdown_header_row
        chart_col = 5
        
        chart = workbook.add_chart({'type': 'line'})
        
        chart.add_series({
            'name': 'SIP Value',
            'categories': ['Summary', breakdown_header_row + 1, 0, breakdown_header_row + len(years), 0],
            'values': ['Summary', breakdown_header_row + 1, 1, breakdown_header_row + len(years), 1],
            'line': {'color': '#22C55E', 'width': 2.5}
        })
        
        chart.add_series({
            'name': 'Lumpsum Value',
            'categories': ['Summary', breakdown_header_row + 1, 0, breakdown_header_row + len(years), 0],
            'values': ['Summary', breakdown_header_row + 1, 2, breakdown_header_row + len(years), 2],
            'line': {'color': '#3B82F6', 'width': 2.5}
        })
        
        chart.add_series({
            'name': 'Total Value',
            'categories': ['Summary', breakdown_header_row + 1, 0, breakdown_header_row + len(years), 0],
            'values': ['Summary', breakdown_header_row + 1, 3, breakdown_header_row + len(years), 3],
            'line': {'color': '#F59E0B', 'width': 3}
        })
        
        chart.set_title({
            'name': 'Investment Growth Over Time',
            'name_font': {'size': 14, 'bold': True}
        })
        chart.set_x_axis({'name': 'Years', 'name_font': {'size': 12}})
        chart.set_y_axis({
            'name': 'Value (₹)',
            'num_format': '₹ #,##0',
            'name_font': {'size': 12}
        })
        chart.set_size({'width': 720, 'height': 480})
        chart.set_legend({'position': 'bottom'})
        
        worksheet.insert_chart(chart_row, chart_col, chart)
        worksheet.autofilter(breakdown_header_row, 0, breakdown_header_row + len(years), 3)
    
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

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Total Investment Return Calculator", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    
    years = list(range(1, investment_years + 1))
    sip_corpus = [calculate_sip_future_value(sip_amount, expected_return, year) for year in years]
    lumpsum_corpus = [calculate_lumpsum_future_value(lumpsum_amount, expected_return, year) for year in years]
    total_corpus = [s + l for s, l in zip(sip_corpus, lumpsum_corpus)]
    
    chart_data = pd.DataFrame({
        'Year': years,
        'SIP Value': sip_corpus,
        'Lumpsum Value': lumpsum_corpus,
        'Total Value': total_corpus
    }).set_index('Year')
    
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

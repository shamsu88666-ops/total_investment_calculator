def create_excel_report(results):
    """Create Excel report with proper alignment and visible text"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats - ലൈറ്റ് ബാക്ക്‌ഗ്രൗണ്ടിനായി ഡാർക്ക് ടെക്സ്റ്റ്
        title_fmt = workbook.add_format({
            'bold': True, 
            'font_size': 16, 
            'font_color': '#000000',  # കറുത്ത നിറം വെള്ള ബാക്ക്ഗ്രൗണ്ടിനായി
            'bg_color': '#E2EFDA',  # ലൈറ്റ് ഗ്രീൻ ബാക്ക്ഗ്രൗണ്ട്
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
            'num_format': '₹ #,##0.00',  # രണ്ട് ദശമാംശ സ്ഥാനങ്ങൾ
            'border': 1, 
            'font_color': '#000000',  # കറുത്ത ടെക്സ്റ്റ്
            'bg_color': '#FFFFFF',    # വെള്ള ബാക്ക്ഗ്രൗണ്ട്
            'align': 'right',
            'valign': 'vcenter'
        })
        
        normal_fmt = workbook.add_format({
            'border': 1, 
            'font_color': '#000000',  # കറുത്ത ടെക്സ്റ്റ്
            'bg_color': '#FFFFFF',    # വെള്ള ബാക്ക്ഗ്രൗണ്ട്
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
        worksheet.set_column('A:A', 30)  # ലേബലുകൾ
        worksheet.set_column('B:B', 25)  # മൂല്യങ്ങൾ
        worksheet.set_column('D:D', 20)  # ചാർട്ടിനായി ഇടം
        
        # ടൈറ്റിൽ
        worksheet.merge_range('A1:D1', 'Investment Summary Report', title_fmt)
        worksheet.merge_range('A2:D2', f'Generated on: {date.today().strftime("%d-%B-%Y")}', normal_fmt)
        
        worksheet.write('A4', 'Input Parameters', header_fmt)
        worksheet.merge_range('A4:B4', 'Input Parameters', header_fmt)
        
        # ഇൻപുട്ട് പാരാമീറ്ററുകൾ
        data_start_row = 5
        input_data = [
            ['Monthly SIP Amount', results['sip_amount']],
            ['Lumpsum Amount', results['lumpsum_amount']],
            ['Investment Period (Years)', results['investment_years']],
            ['Expected Annual Return (%)', results['expected_return'] / 100]
        ]
        
        for idx, (label, value) in enumerate(input_data):
            row = data_start_row + idx
            worksheet.write(f'A{row}', label, normal_fmt)
            if 'Amount' in label:
                worksheet.write(f'B{row}', value, currency_fmt)
            elif 'Return' in label:
                worksheet.write(f'B{row}', value, percent_fmt)
            else:
                worksheet.write(f'B{row}', value, number_fmt)
        
        # റിസൾട്ടുകൾ
        result_start_row = data_start_row + len(input_data) + 2
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
        breakdown_start_row = result_start_row + len(result_data) + 3
        worksheet.merge_range(f'A{breakdown_start_row}:D{breakdown_start_row}', 'Year-wise Growth', header_fmt)
        
        # ഹെഡർ
        breakdown_header_row = breakdown_start_row + 1
        headers = ['Year', 'SIP Value', 'Lumpsum Value', 'Total Value']
        for col, header in enumerate(headers):
            worksheet.write(breakdown_header_row, col, header, header_fmt)
        
        # ഡാറ്റ
        years = list(range(1, results['investment_years'] + 1))
        for idx, year in enumerate(years):
            row = breakdown_header_row + 1 + idx
            sip_val = calculate_sip_future_value(results['sip_amount'], results['expected_return'], year)
            lump_val = calculate_lumpsum_future_value(results['lumpsum_amount'], results['expected_return'], year)
            total_val = sip_val + lump_val
            
            worksheet.write(row, 0, year, number_fmt)  # Year
            worksheet.write(row, 1, sip_val, currency_fmt)  # SIP Value
            worksheet.write(row, 2, lump_val, currency_fmt)  # Lumpsum Value
            worksheet.write(row, 3, total_val, currency_fmt)  # Total Value
        
        # ചാർട്ട് - ഉയരം കൂടുതൽ ഇടം ഉറപ്പാക്കാൻ
        chart_row = breakdown_header_row
        chart_col = 5
        
        chart = workbook.add_chart({'type': 'line'})
        
        # SIP Value series
        chart.add_series({
            'name': 'SIP Value',
            'categories': ['Summary', breakdown_header_row + 1, 0, breakdown_header_row + len(years), 0],
            'values': ['Summary', breakdown_header_row + 1, 1, breakdown_header_row + len(years), 1],
            'line': {'color': '#22C55E', 'width': 2.5}
        })
        
        # Lumpsum Value series
        chart.add_series({
            'name': 'Lumpsum Value',
            'categories': ['Summary', breakdown_header_row + 1, 0, breakdown_header_row + len(years), 0],
            'values': ['Summary', breakdown_header_row + 1, 2, breakdown_header_row + len(years), 2],
            'line': {'color': '#3B82F6', 'width': 2.5}
        })
        
        # Total Value series
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
        
        # ഓട്ടോ ഫിൽറ്റർ ഹെഡർകൾക്ക്
        worksheet.autofilter(breakdown_header_row, 0, breakdown_header_row + len(years), 3)
        
        # വർക്ക്‌ഷീറ്റ് പ്രൊട്ടക്ഷൻ - ഉപയോക്താവിന് തിരുത്താൻ കഴിയില്ലെന്ന് ഉറപ്പാക്കാൻ
        worksheet.protect()
    
    return buffer.getvalue()

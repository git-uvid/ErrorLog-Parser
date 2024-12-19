import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(
    page_title="ErrorLog Classifier",
    layout="wide"
)

def parse_log_file(file):
    date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'
    warn_pattern = r'(?:WARN :)'
    pattern_1 = r"Coordinate (\S+) not found in dimension (\S+) \(load (\S+)\)"
    pattern_2 = r"Could not write cube cell: Element (\S+) in dimension (\S+) is consolidated and Splashing is disabled. \(load (\S+)\)"
    
    data = []
    other_warnings = []

    file_content = file.read().decode("utf-8")
    
    for line in file_content.splitlines():
        processed_date = re.sub(date_pattern, '', line)
        processedWarn_date = re.sub(warn_pattern, '', processed_date)
        
        # Check if the line matches pattern_1
        match_1 = re.search(pattern_1, processedWarn_date)
        if match_1:
            coordinate = match_1.group(1)
            dimension = match_1.group(2)
            load = match_1.group(3)
            data.append([coordinate, dimension, load])
        
        # Check if the line matches pattern_2
        else:
            match_2 = re.search(pattern_2, processedWarn_date)
            if match_2:
                element = match_2.group(1)
                dimension = match_2.group(2)
                load = match_2.group(3)
                data.append([element, dimension, load])
            else:
                line_without_date_warn = re.sub(r"^\S+ \S+, \S+  WARN :", "", processedWarn_date)
                other_warnings.append([line_without_date_warn])

    return data, other_warnings


st.title("ErrorLog Parser")
st.write("This tool simplifies troubleshooting, enhances debugging efficiency, and allows users to quickly generate downloadable Excel reports, making it easier to track, manage, and resolve integration process-related problems.")

uploaded_file = st.file_uploader("Choose a log file", type="txt")
if uploaded_file is not None:
    extracted_data, other_warnings = parse_log_file(uploaded_file)
    if extracted_data:
        df_data = pd.DataFrame(extracted_data, columns=["coordinate", "dimension", "load"])
        df_other_warnings = pd.DataFrame(other_warnings, columns=["other warning"])

        excel_file = io.BytesIO()
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            df_data.to_excel(writer, index=False, sheet_name="Parsed Data")
            df_other_warnings.to_excel(writer, index=False, sheet_name="Other Warnings")
        
        excel_file.seek(0)

        st.download_button(
            label="Download Excel file",
            data=excel_file,
            file_name="parsed_log_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        col1,col2 = st.columns(2)

        with col1:
            st.write("Warning Data :")
            st.table(df_data)
        with col2:
            if other_warnings:
                st.write("Other Warnings:")
                st.table(df_other_warnings)
                
    else:
        st.write("No matching data found in the log file.")

import streamlit as st
import pandas as pd
import re,io

st.set_page_config(
    page_title="ErrorLog Classifier",
    layout="wide"
)

st.markdown("""
    <style>
        /* Add your custom CSS here */
        .st-emotion-cache-pgf13w h1 {
            scroll-margin-top: 3.75rem;
            font-size: 3em;
            color: #273746;
            margin-bottom: 20px;
            font-weight: 900;
            text-align: center;
            font-family: "Source Sans Pro", sans-serif;
            font-weight: 700;
            font-size: 2.75rem;
            padding: 1.25rem 0px 1rem;
            margin: 0px;
            line-height: 1.2;
        }
        .st-emotion-cache-nrabgc p{
            word-break: break-word;
            margin: 0px 0px 1rem;
            padding: 0px;
            font-size: 17px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

def parse_log_file(file):
    date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'
    warn_pattern = r'(?:WARN :)'
    pattern_1 = r"Coordinate ([\S\s]+) not found in dimension ([\S\s]+) \(load ([\S\s]+)\)"
    pattern_2 = r"Could not write cube cell: Element ([\S\s]+) in dimension ([\S\s]+) is consolidated and Splashing is disabled. \(load ([\S\s]+)\)"
    pattern_3 = r"Failed to transform NULL value of column null in function ([\S\s]+) at line : Element ([\S\s]+) does not exist in dimension ([\S\s]+) \(function ([\S\s]+) in transform ([\S\s]+)\)"
    pattern_4 = r"Element with name ([\S\s]+) exists multiple times in normalized form \(transform ([\S\s]+)\)"
    pattern_5 = r"Column ([\S\s]+) does not exist in source. Dimension mapping is ignored. \(load ([\S\s]+)\)"
    pattern_6 = r"Failed to transform value ([\S\s]+) of column ([\S\s]+) in function ([\S\s]+): Unparseable ([\S\s]+) \(function ([\S\s]+) in transform ([\S\s]+)\)"
    pattern_7 = r"Removing column ([\S\s]+) of source ([\S\s]+) from joint result, because ([\S\s]+) \(transform ([\S\s]+)\)"
    pattern_8 = r"Empty coordinate in dimension ([\S\s]+) \(load ([\S\s]+)\)"
    pattern_9 = r"Failed to transform NULL value of column null in function ([\S\s]+) at line : Unable to execute groovy function: Cannot invoke method substring\(\) on null object \(function ([\S\s]+) in transform ([\S\s]+)\)"

    data = []
    other_warnings = []
    file_content = file.read().decode("utf-8")
    for line in file_content.splitlines():
        processed_date = re.sub(date_pattern, '', line)
        processedWarn_date = re.sub(warn_pattern, '', processed_date)
        match_1 = re.search(pattern_1, processedWarn_date)
        if match_1:
            coordinate = match_1.group(1)
            dimension = match_1.group(2)
            load = match_1.group(3)
            message = "element not found in dimension"
            data.append([coordinate, dimension, load, message])
        else:
            match_2 = re.search(pattern_2, processedWarn_date)
            if match_2:
                element = match_2.group(1)
                dimension = match_2.group(2)
                load = match_2.group(3)
                message = "Splashing disabled in consolidation"
                data.append([element, dimension, load, message])
            else:
                match_3 = re.search(pattern_3, processedWarn_date)
                if match_3:
                    function = match_3.group(1)
                    element = match_3.group(2)
                    dimension = match_3.group(3)
                    transform = match_3.group(5)
                    function_transform = "[function] "+function+" in [transform] "+transform
                    message = "NULL value transformation failed"
                    data.append([element, dimension, function_transform, message])
                else:
                    match_4 = re.search(pattern_4, processedWarn_date)
                    if match_4:
                        element = match_4.group(1).replace('"', "")
                        transform = match_4.group(2)
                        message = "Element exists multiple times in normalized form"
                        data.append([element, "N/A", transform, message])
                    else:
                        match_5 = re.search(pattern_5, processedWarn_date)
                        if match_5:
                            dim = match_5.group(1)
                            load = match_5.group(2)
                            message = "Dimension mapping is ignored"
                            data.append(["N/A", dim , load, message])
                        else:
                            match_6 = re.search(pattern_6, processedWarn_date)
                            if match_6:
                                value = match_6.group(1).replace('"', "")
                                column = match_6.group(2)
                                function = match_6.group(3)
                                unparseable = match_6.group(4)
                                transform = match_6.group(6)
                                function_transform = "[function] "+function+" in [transform] "+transform
                                message = "Value transformation failed due to unparseable "+ unparseable
                                data.append([value, "N/A", function_transform, message])
                            else:
                                match_7 = re.search(pattern_7, processedWarn_date)
                                if match_7:
                                    coord = match_7.group(1)
                                    source = match_7.group(2)
                                    reason = match_7.group(3)
                                    transform = match_7.group(4)
                                    data.append([coord, "N/A", transform, reason])
                                else:
                                    match_8 = re.search(pattern_8, processedWarn_date)
                                    if match_8:
                                        coord = match_8.group(1)
                                        transform = match_8.group(2)
                                        data.append([coord, "N/A", transform, "Empty coordinate"])
                                    else:
                                        match_9 = re.search(pattern_9, processedWarn_date)
                                        if match_9:
                                            func = match_9.group(1)
                                            transform = match_9.group(3)
                                            data.append([func,"N/A",transform,"Unable to execute groovy function: Cannot invoke method substring() on null object"])
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
        df_data = pd.DataFrame(extracted_data, columns=["Element/Coordinate/function", "dimension", "component", "remarks"])
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

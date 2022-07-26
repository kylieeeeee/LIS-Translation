import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime


st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })

st.title('🗃️LIS File Translation Tool🧰⚙️')
st.header('📊Summary Report')
st.info('Please standardize the timestamps before using this tool.')

with st.expander('Click here to view the instructions'):
    st.markdown("""
    #### Instructions
1. Select the raw data which timestamps are standardized by this application. **ONLY EXCEL files are accpeted**
2. Select the sheet name which contains the formatted timestamp data.
3. Select the column name for *Test Name*, *Test Arrival Date*, *Test Arrival Time* respectively.
4. Click **Generate Aggregated Report** button to view the result.
    """)

# function
def format_date(date: datetime, time: str):
    weekday = date.strftime('%A')
    date = date.strftime('%Y-%m-%d')
    hour = datetime.strptime(time, '%H:%M:%S').hour
    return (date, weekday, hour)




## Upload the excel file
st.header('Upload Time Formatted Data')
uploaded_file = st.file_uploader("Select the file which needs translation:", type=['xlsx'])
st.info('Please only upload excel file.')


if uploaded_file is not None:
    # get the file name of raw data
    st.session_state.file_name = uploaded_file.name
    LIS_file = pd.ExcelFile(uploaded_file)
    all_sheets = ['(Not Selected Yet)'] + LIS_file.sheet_names
    
    ## User select the sheet name that needs translation
    selected_sheet = st.selectbox('Select the sheet with timestamps standardized data:', all_sheets)

    ## to read just one sheet to dataframe and display the sheet:
    if selected_sheet != '(Not Selected Yet)':
        # Read the data in as string
        raw_data = pd.read_excel(LIS_file, sheet_name = selected_sheet, dtype = str)

        with st.expander("Click here to check the file you upoaded"):
            st.write("Number of observations: " + str(len(raw_data)))
            st.write("Here are the first 10 rows of raw data")
            st.write(raw_data.head(10))
            st.caption("<NA> means there is no value in the cell")

        all_columns = ['(Not Selected Yet)'] + list(raw_data.columns)
        # ID_column = st.selectbox("Select the column for patient ID", all_columns) 
        test_name_col = st.selectbox('Select the column for tests name', all_columns)
        arrival_date_col = st.selectbox('Select the column for tests arrival date', all_columns)
        arrival_time_col = st.selectbox('Select the column for tests arrival time', all_columns)
        # verified_date_col = st.selectbox('Select the date column when tests are completed/verified', all_columns)
        # verified_time_col = st.selectbox('Select the time column when tests are completed/verified', all_columns)

        st.session_state.raw_data = raw_data
        st.session_state.test_name_col = test_name_col
        st.session_state.arrival_dat_col = arrival_date_col
        st.session_state.arrival_time_col = arrival_time_col
        # st.session_state.verified_date_col = verified_date_col
        # st.session_state.verified_time_col = verified_time_col

        if st.button("Generate Aggregated Report"):
            if '(Not Selected Yet)' in (test_name_col, arrival_date_col, arrival_time_col):
                st.warning('WARNING: You missed selecting one of the columns above')
            else:
                df = raw_data.copy()
                df['Arrival_Date'], df['Arrival_Weekday'], df['Arrival_Hour'] = zip(*df.apply(lambda t: format_date(t[arrival_date_col], t[arrival_time_col]), axis=1))

                aggregated_date_hour = df.groupby(['Arrival_Date', 'Arrival_Hour']).count()[test_name_col].reset_index()
                aggregated_date = df.groupby(['Arrival_Date']).count()[test_name_col].reset_index()
                aggregated_week = df.groupby(['Arrival_Weekday']).count()[test_name_col].reset_index()

                chart1 = alt.Chart(aggregated_date_hour, title='Number of tests conducted in each hour').mark_rect().encode(
                    alt.X('Arrival_Hour:O', title='hour of day'),
                    alt.Y('Arrival_Date:O', title='date'),
                    alt.Color(test_name_col, title='number of tests'),
                    tooltip = [test_name_col]
                ).interactive()

                chart2 = alt.Chart(aggregated_date, title='Number of tests conducted in each date').mark_bar().encode(
                        alt.X(test_name_col, title='number of tests'),
                        alt.Y("Arrival_Date:O", title='Date'),
                        tooltip = [test_name_col]
                ).interactive()

                chart3 = alt.Chart(aggregated_week, title='Number of tests conducted on each day').mark_bar().encode(
                        alt.Y('Arrival_Weekday:O', title='Weekday', sort=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']),
                        alt.X(test_name_col, title='number of tests'),
                        tooltip = [test_name_col]
                ).interactive()

                st.header("Aggregated results for tests arrival time")
                tab1, tab2, tab3 = st.tabs(['Aggregated by arrival date and hour', 'Aggregated by arrival date', 'Aggregated by arrival day of week'])

                with tab1:
                    col11, col12 = st.columns(2)
                    col11.dataframe(aggregated_date_hour, width=800)
                    col12.write(chart1)
                    col12.caption('White square means there was no tests conducted in that hour.')

                with tab2:
                    col21, col22 = st.columns(2)
                    col21.dataframe(aggregated_date, width=800)
                    col22.write(chart2)

                with tab3:
                    col31, col32 = st.columns(2)
                    col31.dataframe(aggregated_week, width=800)
                    col32.write(chart3)


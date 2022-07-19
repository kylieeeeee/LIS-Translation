import streamlit as st
import pandas as pd
import numpy as np
import functions as f
from datetime import datetime

st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })


st.title('🗃️LIS File Translation Tool🧰⚙️')
st.header('Timestamps Formatting')
st.subheader('Fill in the missing timestamps and format the date and time')
with st.expander('Click here to view the instructions'):
    st.markdown("""
    #### Instructions
1. Select the file you want to translate. **ONLY EXCEL files are accpeted**
2. Select the sheet that contains the raw data.
3. Select the columns for *patient ID*
4. Select the timestamp columns which you want to format.
5. Select the delimiter that the raw file is using to separate data and time in the columns
6. Preview the formatted data below. If the result is correct, click **Download Current Result** to download the formatted file.
    """)

## Section: Upload the excel file
st.header('Upload Raw Data')
uploaded_file = st.file_uploader("Select the file which needs translation:", type=['xlsx'])
st.info('Please only upload excel file.')



if uploaded_file is not None:
    # get the file name of raw data
    st.session_state.file_name = uploaded_file.name
    LIS_file = pd.ExcelFile(uploaded_file)
    all_sheets = ['(Not Selected Yet)'] + LIS_file.sheet_names
    
    ## User select the sheet name that needs translation
    selected_sheet = st.selectbox('Select the sheet with raw data:', all_sheets)

    ## to read just one sheet to dataframe and display the sheet:
    if selected_sheet != '(Not Selected Yet)':
        raw_data = pd.read_excel(LIS_file, sheet_name = selected_sheet, dtype=str)
        
        all_columns = ['(Not Selected Yet)'] + list(raw_data.columns)
        ID_column = st.selectbox("Select the column for patient ID", all_columns)
        if ID_column != '(Not Selected Yet)':
            st.session_state.ID_column = ID_column
            if raw_data[ID_column].isna().sum() > 0:
                st.warning('WARNING: There are missing patient ID in this data.  Rows without patient ID will be dropped durning translation.')
            raw_data[ID_column] = raw_data[ID_column].astype(str)
            st.session_state.raw_data = raw_data

        with st.expander("Click here to check the file you upoaded"):
            st.write("Number of observations: " + str(len(raw_data)))
            st.write("Here are the first 10 rows of raw data")
            st.write(raw_data.head(10))
            st.caption("<NA> means there is no value in the cell")


        st.markdown('---')
        # select the timestamp columns
        time_columns = st.multiselect("Select the columns of timestamps that need formatting. ", raw_data.columns)
        st.info('Please only select the timestamp columns which include **BOTH** date and time.\
            **Multiple selections are allowed**.')

        # input/choose delimiter
        delimiter = st.radio('Select the delimiter that separate date and time in a timestamp column',
                        ('Space', '@', '_'))
        if delimiter == 'Space':
            delimiter = ' '

        # fill in missing dates
        filled_data = raw_data.copy()
        filled_data[time_columns] = filled_data.groupby(ID_column)[time_columns].ffill().bfill()
        st.session_state.filled_data = filled_data

        # separate the date and time
        for col in time_columns:
            try:
                # see if the time column includes both date and time
                if len(filled_data[col][0]) < 11:
                    st.warning('The column you selected does not include BOTH date and time')
                # check if the delimiter is correct
                elif filled_data[col][0].find(delimiter) == -1:
                    st.warning('The selected delimiter is not found in the timestamps.')
                else:
                    # create the new column name                       
                    date_col = col + '__Date'
                    time_col = col + '__Time'
                    filled_data[[date_col, time_col]] = filled_data[col].str.split(delimiter, expand = True)

                    # # check the data type of the timestamp column
                    # if filled_data[col].dtypes == 'object':
                    #     filled_data[[date_col, time_col]] = filled_data[col].str.split(delimiter, expand = True)
                    #     st.session_state.filled_data = filled_data
                    # elif filled_data[col].dtypes == 'datetime64[ns]':
                    #     filled_data[date_col] = filled_data[col].apply(lambda x: x.strftime("%Y/%m/%d"))
                    #     filled_data[time_col] = filled_data[col].apply(lambda x: x.strftime("%H:%M:%S"))
                    # else:
                    #     st.write(filled_data[col].dtypes)
                    #     st.warning('Unknown data type')

            except ValueError:
                st.error('At least one of the columns you selected does not include **BOTH** date and time')


        st.markdown('---')
        st.write('Preview the new data')
        st.info('Please scroll to the right to see the newly created columns')
        st.write(filled_data)
        st.caption("<NA> means there is no value in the cell")


        # Formatting the new file name
        today = datetime.today().strftime("%Y%m%d_%H%M")+'_'
        new_file_name = 'Time Formatted_' + today + st.session_state.file_name 
        # output the excel file and let the user download
        sheet_list = ['Time Formatted Data', 'Raw Data']
        df_xlsx = f.dfs_to_excel([filled_data, raw_data], sheet_list)
        st.download_button(label='📥 Download Current Result 📥',
                                        data=df_xlsx,
                                        file_name= new_file_name)

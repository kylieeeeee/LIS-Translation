from http.cookies import BaseCookie
from operator import index
import pandas as pd
import streamlit as st
import json
from io import BytesIO
from LIS_data import LIS_Data
import functions as f
import difflib


st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })

     
st.title('🗃️LIS File Translation Tool🧰⚙️')
st.header('Using the similarity scores to compare tests')


## Section 1: Upload the excel file that need translation
st.header("1️⃣Select the file which needs translation:")

uploaded_file = st.file_uploader("Please only upload Excel file.")

# list to save all LIS_Data objects
list_of_LIS = []
if 'list_of_LIS' not in st.session_state:
    st.session_state.list_of_LIS = list_of_LIS

if uploaded_file is not None:
    try:
        LIS_file = pd.ExcelFile(uploaded_file)
        all_sheets = ['(Not Selected Yet)'] + LIS_file.sheet_names
        
        ## User select the sheet name that needs translation
        selected_sheet = st.selectbox('Select the sheet name:', all_sheets, key='raw_data_selection')

        ## to read just one sheet to dataframe and display the sheet:
        if selected_sheet != '(Not Selected Yet)':
            LIS_sheet = pd.read_excel(LIS_file, sheet_name = selected_sheet)
            st.session_state.raw_data = LIS_sheet
            with st.expander("Click here to check the file you upoaded"):
                st.write("Number of observations: " + str(len(LIS_sheet)))
                st.write("Here are the first 10 rows of data")
                st.write(LIS_sheet.head(10))
            ID_column = st.selectbox("Select the column for patient ID", LIS_sheet.columns)
            st.session_state.ID_column = ID_column
            test_name_column = st.selectbox('Select the columns for LIS test names', LIS_sheet.columns)
            st.session_state.test_name_column = test_name_column

            if st.button('📤 Upload Raw Data'):
                # create LIS objects for each row
                try:
                    for i in range(len(LIS_sheet)):
                        patient_id = LIS_sheet[ID_column][i]
                        test_name = str(LIS_sheet[test_name_column][i])
                        tmp = LIS_Data(patient_id, test_name)
                        list_of_LIS.append(tmp)
                        st.session_state.list_of_LIS = list_of_LIS
                    st.success('File uploaded successfully')

                except AttributeError:
                    st.warning("🚨 There are invalid test names")

    except ValueError:
        st.error("🚨The file you upload is not an Excel file (.xlsx)")
    
#=======================================================================================================#

panelDict = f.load_json('data/LIS DB.json')
st.session_state.panelDict = panelDict
threshold = st.slider('Select the threshold of confidence score', 0, 100, 80)
st.session_state.threshold = threshold

if st.button('Click here to start matching'):
    list_of_LIS = st.session_state.list_of_LIS
    panelDict = st.session_state.panelDict
    threshold = st.session_state.threshold

    # Take all unique test names in the raw file and find the most similar test name in the
    # panel dictionary and then translate it into corresponding roche assay names.
    
    # @input
    # panelDef: a dictionary for panel definition(contains historical LIS tranlation data)
    # tests: a list of unique LIS test names which need translation
    # cutoff: a float number which determines the word similarity cutoff for the get_close_match function. 
    
    # @return
    # match_result: a dictionary of suggested translations for the new test data

    # Get unique test names from all LIS objects
    tests = list(set(x.getTestName() for x in list_of_LIS))
    st.session_state.tests = tests

    match_result = {}
    for test in tests:
        matches = difflib.get_close_matches(test, panelDict.keys(), n=1, cutoff = threshold/100)
        if len(matches) > 0:
            best_match = matches[0]
            score = difflib.SequenceMatcher(None, test, best_match).ratio()
            match_result[test] = {'Include':1, 
                                    'Material':panelDict[best_match]['Material'],
                                    'SimilarTest': best_match,
                                    'AssayName': panelDict[best_match]['AssayName'],
                                    'ConfidenceScore': score}
        else:
            match_result[test] = {'Include':1, 
                                    'Material': '',
                                    'SimilarTest': 'No similar test found',
                                    'AssayName': '',
                                    'ConfidenceScore': 0}
        st.session_state.match_result = match_result




    # Turn the match_result from get_close_match into a dataframe
    # @input
    # match_result: a dictionary
    # @output
    # panel_df: a dataframe
    panel_df = pd.DataFrame()
    for key, value in match_result.items():
        tmp = pd.DataFrame([[key, value['Include'], value['Material'], 
                            value['SimilarTest'], value['AssayName'], 
                            value['ConfidenceScore']]])
        panel_df = pd.concat([panel_df, tmp])
        st.session_state.panel_df = panel_df

    panel_df.columns = ['Test Name', 'Include', 'Material', 'Similar Test',
                        'Assay Name', 'Confidence Score']
    panel_df.sort_values('Confidence Score', ascending = False, inplace = True)
    st.session_state.panel_df = panel_df
    st.text('The panel dictionary for the file you uploaded')
    st.write(panel_df)



    # Append the data in match_result as new columns to the raw file
    # New columns are Similat Test, Assay Name, Confidence Score

    # @input
    # raw: A DataFrame selected by user which contains the LIS test names. 
    #      The column of LIS test names cannot have missing values
    # LIS_column_name: A string which is the column name of the LIS test name in the raw file
    # match_result:  A dictionary contains the test names and similar test and roche assay name
    # @return
    # result_df: A DataFrame contains the raw file and three new columns
    raw_data = st.session_state.raw_data
    LIS_column = st.session_state.test_name_column
    result_df = raw_data.copy()
    result_df.dropna(subset = LIS_column, inplace = True)
    st.session_state.result_df = result_df

    for index, row in result_df.iterrows():
        result_df.loc[index,'Similar Test'] = match_result[row[LIS_column]]['SimilarTest']
        result_df.loc[index, 'Assay Name'] = match_result[row[LIS_column]]['AssayName']
        result_df.loc[index, 'Confidence Score'] = round(match_result[row[LIS_column]]['ConfidenceScore'],3)
        st.session_state.result_df = result_df

    st.text('The result file with translation')
    st.write(result_df)


    # output the excel file and let the user download
    sheet_list = ['Panel Definitions', 'raw data with matching results', 'raw data']
    df_xlsx = f.dfs_to_excel([panel_df, result_df, raw_data],  sheet_list)
    st.download_button(label='📥 Download Current Result 📥',
                                    data=df_xlsx,
                                    file_name= 'df_test.xlsx')


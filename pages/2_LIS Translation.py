from http.cookies import BaseCookie
from operator import index
import pandas as pd
from pyparsing import col
import streamlit as st
import json
from io import BytesIO
from LIS_data import LIS_Data
import functions as f
import difflib
from datetime import datetime


st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })


st.title('🗃️LIS File Translation Tool🧰⚙️')
st.subheader('Using the similarity scores to compare LIS test names and match with Roche Assay names')


## Section 1: Upload the excel file that need translation
st.header('Upload Raw Data')
uploaded_file = st.file_uploader("Select the file which needs translation:")
st.info('Please only upload excel file.')

# list to save all LIS_Data objects
list_of_LIS = []
if 'list_of_LIS' not in st.session_state:
    st.session_state.list_of_LIS = list_of_LIS

if uploaded_file is not None:
    try:
        # get the file name of raw data
        st.session_state.file_name = uploaded_file.name
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
                st.write("Here are the first 10 rows of raw data")
                st.write(LIS_sheet.head(10))
                st.caption("<NA> means there is no value in the cell")

            ID_column = st.selectbox("Select the column for patient ID", LIS_sheet.columns)
            st.session_state.ID_column = ID_column
            if LIS_sheet[ID_column].isna().sum() > 0:
                st.warning('WARNING: There are missing patient ID in this data.  Rows without patient ID will be dropped durning translation.')
            LIS_sheet[ID_column] = LIS_sheet[ID_column].astype(str)
            st.session_state.raw_data = LIS_sheet

            test_name_column = st.selectbox('Select the columns for LIS test names', LIS_sheet.columns)
            st.session_state.test_name_column = test_name_column
            if LIS_sheet[test_name_column].isna().sum() > 0:
                st.warning('WARNING: There are missing LIS test names in this data.  Rows without LIS test name will be dropped durning translation.')

            # Let user select the columns for 5 columns worksheet
            # Patient_ID	Priority	TimeStamp	TestName	Material
            column_options = st.multiselect(
            'Select the columns for the 5 column worksheet', LIS_sheet.columns)
            st.info('Suggestion: Patient_ID, Priority, TimeStamp')
            st.session_state.columns_for_5 = column_options

            if st.button('📤 Upload Raw Data'):
                # create LIS objects for each row
                try:
                    for i in range(len(LIS_sheet)):
                        patient_id = LIS_sheet[ID_column][i]
                        test_name = LIS_sheet[test_name_column][i]
                        # only save rows with test names
                        if (type(test_name) == str):
                            tmp = LIS_Data(patient_id, test_name)
                            list_of_LIS.append(tmp)
                            st.session_state.list_of_LIS = list_of_LIS
                    st.success('File uploaded successfully')

                except AttributeError:
                    st.warning("🚨 There are invalid test names")

    except ValueError:
        st.error("🚨The file you upload is not an Excel file (.xlsx)")
    
#=======================================================================================================#
# User select the threshold
st.markdown('---')
st.header('Select the threshold for confidence level')
threshold = st.slider('Only the tests with similarity higher than threshold will be translated', 0, 100, 80)
st.session_state.threshold = threshold

# Load the base dictionary
panelDict = f.load_json('data/LIS DB.json')
st.session_state.panelDict = panelDict

# merge the base dictionary with newDict if the user uploaded a new dictionary
st.markdown('---')
upload = st.checkbox('Check the box if you uploaded a new dictionary')
st.info('If this is the first time translating this file, you should not check the box.')
if upload:
    newDict = st.session_state.newDict
    panelDict.update(newDict)
    st.session_state.panelDict = panelDict


# Start matching
if st.button('Click here to start matching'):
    list_of_LIS = st.session_state.list_of_LIS
    if list_of_LIS == []:
        st.warning("You haven't uploaded raw file yet")
    else:
        # Get unique test names from all LIS objects
        list_of_LIS = st.session_state.list_of_LIS
        tests = list(set(x.getTestName() for x in list_of_LIS))
        st.session_state.tests = tests

        # Take all unique test names in the raw file and find the most similar test name in the
        # panel dictionary and then translate it into corresponding roche assay names.
        
        # @input
        # panelDef: a dictionary for panel definition(contains historical LIS tranlation data)
        # tests: a list of unique LIS test names which need translation
        # cutoff: a float number which determines the word similarity cutoff for the get_close_match function. 
        
        # @return
        # match_result: a dictionary of suggested translations for the new test data
        match_result = {}
        panelDict = st.session_state.panelDict
        threshold = st.session_state.threshold
        for test in tests:
            matches = difflib.get_close_matches(str(test), panelDict.keys(), n=1, cutoff = threshold/100)
            if len(matches) > 0: # if a match is found
                best_match = matches[0]
                score = difflib.SequenceMatcher(None, test, best_match).ratio()
                match_result[test] = {'Include':panelDict[best_match]['Include'], 
                                        'Material':panelDict[best_match]['Material'],
                                        'SimilarTest': best_match,
                                        'AssayName': panelDict[best_match]['AssayName'],
                                        'ConfidenceScore': round(score*100,2)}
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
        panel_df.reset_index(drop = True, inplace = True)
        st.session_state.panel_df = panel_df


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
        result_df.dropna(subset = [LIS_column], inplace = True) #Drop the row if test name is missing
        st.session_state.result_df = result_df

        #### Do not add rows if Include == 0
        for index, row in result_df.iterrows():
            if match_result[row[LIS_column]]['Include'] == 1:
                result_df.loc[index,'Similar Test'] = match_result[row[LIS_column]]['SimilarTest']
                result_df.loc[index,'Material'] = match_result[row[LIS_column]]['Material']
                result_df.loc[index, 'Assay Name'] = match_result[row[LIS_column]]['AssayName']
                result_df.loc[index, 'Confidence Score'] = round(match_result[row[LIS_column]]['ConfidenceScore'],3)
            else:
                result_df.drop(index, axis=0, inplace = True)
            st.session_state.result_df = result_df



        # Graph data worksheet
        # Patient ID/Assay Name/LIS Test Name/Location-Ward/Priority/
        # Received Time/Verified Time/Lab/Data Origin
        graph_data = result_df.copy()
        graph_data = graph_data.assign(Assay_Name = graph_data['Assay Name'].str.split(','))
        graph_data = graph_data.explode(['Assay_Name']).drop(['Assay Name'], axis=1)


        # 5 columns worksheet
        columns = st.session_state.columns_for_5 + ['Material', 'Assay Name']
        five_column_df = result_df.copy().loc[:, columns]
        five_column_df = five_column_df.assign(Assay_Name = five_column_df['Assay Name'].str.split(','))
        five_column_df = five_column_df.explode(['Assay_Name']).drop(['Assay Name'], axis=1)


        # Preview results
        with st.expander("Click here to preview results"):
            st.write('Panel definition for the uploaded raw data')
            st.dataframe(panel_df)
            st.caption("<NA> means there is no value in the cell")
            st.markdown('---')
            st.write('The result data with translation and confidence score')
            st.dataframe(result_df)
            st.caption("<NA> means there is no value in the cell")


        # Formatting the new file name
        today = datetime.today().strftime("%Y-%m-%d_%H%M")+'_'
        new_file_name = 'Translated_' + today + st.session_state.file_name 
        # output the excel file and let the user download
        sheet_list = ['Panel Definitions', 'Graph Data Worksheet', '5 Column Worksheet',
                    'Raw data with matching results', 'Raw Data']
        df_xlsx = f.dfs_to_excel([panel_df, graph_data, five_column_df,
                                    result_df, raw_data], sheet_list)
        st.download_button(label='📥 Download Current Result 📥',
                                        data=df_xlsx,
                                        file_name= new_file_name)


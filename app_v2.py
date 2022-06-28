from http.cookies import BaseCookie
from operator import index
import pandas as pd
import streamlit as st
from LIS_data import LIS_Data
from io import BytesIO

## Create authentications https://towardsdatascience.com/how-to-add-a-user-authentication-service-in-streamlit-a8b93bf02031
## Privacy setting https://docs.streamlit.io/knowledge-base/deploy/share-apps-with-viewers-outside-organization
## Sharing setting https://docs.streamlit.io/streamlit-cloud/get-started/share-your-app

st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })

st.title('🗃️LIS File Translation Tool🧰⚙️')

## Functions

# Function for saving the user-defined dictionary
@st.cache
def create_panelDef(panel_file):
    """
        Translate the input file to a dictionary.
        input panel_file: the panel definition excel file user upload or the base dicitonary
        return panelDict: a dictionary
    """
    panelDict = {}
    for i in range(len(panel_file)):
        row = panel_file.iloc[i]
        test_name = row['Test Name']
        include = row['Include']
        material = row['Material']
        tempList = row[3:]
        roche_names = []
        for name in tempList:
            if pd.notna(name):
                roche_names.append(name)
        panelDict[test_name] = {'Include': include, 'Material': material, 'Result_Test': roche_names}
    return panelDict


# Function to save all dataframes to one single excel
def dfs_to_excel(df_list, sheet_list): 
    output = BytesIO()
    writer = pd.ExcelWriter(output,engine='xlsxwriter')   
    for dataframe, sheet in zip(df_list, sheet_list):
        dataframe.to_excel(writer, sheet_name=sheet, startrow=0 , startcol=0, index=False)   
        for column in dataframe:
            column_length = max(dataframe[column].astype(str).map(len).max(), len(column))
            col_idx = dataframe.columns.get_loc(column)
            writer.sheets[sheet].set_column(col_idx, col_idx, column_length)

    writer.save()
    processed_data = output.getvalue()
    return processed_data


## paths for data if running online
path_medicare = 'data/Medicare Panels.csv'
path_roche_tests = 'data/tests performed by instruments.csv'

#=======================================================================================================#
# """
#     All the variables starting with 'st.session_state' are used for saving
#     the corresponding variables to avoid renew.
#     Can view the session_state as a dictionary.
#     Key is the name to assess the variable data, value is the actual data/value store in that variable
#     For example:
#         count = 10, we dont want the program to reset this number, so we use session_state to store the value
#         st.session_state.count = count
#         First 'count' is the key value in the session_state dictionary.
#         Second 'count' is the value we want to store in the dictionary.
#         We can also update the session_state by st.session_state.count = 20
# """


## Section 1: Upload the excel file that need translation
st.header("1️⃣Select the file which needs translation:")

uploaded_file = st.file_uploader("Please only upload Excel file.")

# list to save all LIS_Data objects
list_of_LIS = []
if 'list_of_LIS' not in st.session_state:
    st.session_state.list_of_LIS = list_of_LIS

if uploaded_file is not None:
      #try:
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

              except AttributeError:
                  st.warning("🚨 There are invalid test names")

#     except ValueError:
#         st.error("🚨The file you upload is not an Excel file (.xlsx)")
    

#=======================================================================================================#

## Section 2: upload dictionary
st.header('2️⃣Upload dictionary')
dict_source = st.selectbox('Do you want to use your own dictionary or the base dictionary?',
['  ', 'Upload my own dictionary', 'Use the base dictionary'])
st.session_state.dict_source = dict_source

# create an empty dictionary for saving the user-defined dictionary
panelDict = {}
if 'panelDict' not in st.session_state:
    st.session_state.panelDict = panelDict

# User upload their own dictionary
if dict_source == 'Upload my own dictionary':
    st.info("The column names of the first 4 columns should be exactly the same as **Test Name**, **Include**, **Material**, and **Result_Test**.")
    uploaded_dict = st.file_uploader("Select the excel file. Please make sure the file follows the format.")
    if uploaded_dict is not None:
        try:
            own_dict = pd.ExcelFile(uploaded_dict)
            all_dict_sheets = ['(Not Selected Yet)'] + own_dict.sheet_names

            ## User select the sheet name that needs translation
            selected_dict_sheet = st.selectbox('Select the sheet name:', all_dict_sheets, key='dictionary_selection')

            ## to read just one sheet to dataframe and display the sheet:
            if selected_dict_sheet != '(Not Selected Yet)':
                try:
                    own_dict_sheet = pd.read_excel(own_dict, sheet_name = selected_dict_sheet)
                    own_dict_sheet['Result_Test'].fillna('NA', inplace=True)
                    st.session_state.own_dict_sheet = own_dict_sheet
                    with st.expander("Click here to check the dictionary you uploaded"):
                        st.write("Number of observations: " + str(len(own_dict_sheet)))
                        st.write("Here are the first 10 rows of data")
                        st.write(own_dict_sheet.head(10))

                    # If the button is clicked, app will save the dictionary
                    if st.button('📤 Upload Dictionary'):
                        panelDict = create_panelDef(own_dict_sheet)
                        st.session_state.panelDict = panelDict

                except KeyError:
                    st.warning('🚨 Your dictionary does not follow the naming conventions')

        except ValueError:
            st.error("🚨The file you upload is not an Excel file (.xlsx)")



# User select to use the base dictionary
# base dictionary is the medicare panels
if dict_source == 'Use the base dictionary':
    medicare_panel = pd.read_csv(path_medicare, index_col = 0)

    medicare_panel['Result_Test'].fillna('NA', inplace=True)
    st.session_state.medicare_panel = medicare_panel
    with st.expander("Click here to check the base dicitonary"):
        st.write(medicare_panel)

    panelDict = create_panelDef(medicare_panel)
    st.session_state.panelDict = panelDict


# Read in all roche test names by different instruments and save in rocheDef
roche_test_by_platform = pd.read_csv(path_roche_tests, index_col=0)

# create an empty dictionary for saving all roche test names
rocheDict = {}
if 'rocheDict' not in st.session_state:
    st.session_state.rocheDict = rocheDict

for i in range(len(roche_test_by_platform)):
    test_name = roche_test_by_platform['Test Name'][i]
    rocheDict[test_name] = {'Include': 1, 'Material': '', 'Result_Test': test_name}
    st.session_state.rocheDict = rocheDict

# Dictionary for each platform
c50x_dict = roche_test_by_platform['Test Name'][roche_test_by_platform['c50x']==1]
c503_dict = roche_test_by_platform['Test Name'][roche_test_by_platform['c503']==1]
c70x_dict = roche_test_by_platform['Test Name'][roche_test_by_platform['c70x']==1]
e60x_dict = roche_test_by_platform['Test Name'][roche_test_by_platform['e60x']==1]
e80x_dict = roche_test_by_platform['Test Name'][roche_test_by_platform['e80x']==1]


# Select platforms
st.header('3️⃣Select the platform:')
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    c50x = st.checkbox('c50x')
with col2:
    c503 = st.checkbox('c503')
with col3:
    c70x = st.checkbox('c70x')
with col4:
    e60x = st.checkbox('e60x')
with col5:
    e80x = st.checkbox('e80x')


# Matching Process
if st.button('🖱️ Click here to start matching ⏳'):
    if st.session_state.list_of_LIS == []:
        st.warning("🚨 You haven't uploaded your raw file that need translation 🚨")
    if st.session_state.panelDict == {}:
        st.warning("🚨 You haven't uploaded or chose your panel definition 🚨")

    else:
        # new_panelDict save the original panelDict + unknow tests in raw data
        panelDict = st.session_state.panelDict
        new_panelDict = {}
        if 'new_panelDict' not in st.session_state.keys():
            st.session_state.new_panelDict = {}

        matched_LIS = st.session_state.list_of_LIS

        for data in matched_LIS:
            # If the test is in the panel definition selected
            if data.getTestName() in panelDict.keys():
                data.setRocheTest(panelDict[data.getTestName()]['Result_Test'])
                data.setMatchFound()
                data.setNumberOfRocheTest(len(data.getRocheTest()))
                data.setSourceDict('Panel Definitions')

            # If the test name is the same as roche names
            elif data.getTestName() in rocheDict.keys():
                data.setRocheTest(rocheDict[data.getTestName()]['Result_Test'])
                data.setMatchFound()
                data.setNumberOfRocheTest(len(data.getRocheTest()))
                data.setSourceDict('Roche Test List')

            else:
                # test is unknown, append the test into the new dictionary
                new_panelDict[data.getTestName()] = {'Include': 1, 'Material':'', 'Result_Test': ''}
                data.setRocheTest('')
                data.setNumberOfRocheTest(0)

            # save the matched_LIS into the session state to memorize the data
            st.session_state.list_of_LIS = matched_LIS
            st.session_state.new_panelDict = new_panelDict

        st.success("🎉Matching finished! Generating result file...")


# Process the output
        # Raw Data
        raw_data = st.session_state.raw_data

        # Matched result save as a dataframe
        matched_LIS = st.session_state.list_of_LIS
        tmp = []
        for i in range(len(matched_LIS)):
            tmp.append([matched_LIS[i].getId(), matched_LIS[i].getTestName(), 
                    matched_LIS[i].getRocheTest(), matched_LIS[i].getSourceDict()])

        matched_df = pd.DataFrame(tmp)
        matched_df.columns = ['Patient ID', 'LIS Test Name', 'Assay Name', 'Source']


        # Joining the raw data with matched results
        merged_raw = pd.merge(raw_data, matched_df, 
                            left_on = [st.session_state['ID_column'], st.session_state['test_name_column']], 
                            right_on = ['Patient ID', 'LIS Test Name'])


        merged_raw = merged_raw.explode('Assay Name')
        matched_df = matched_df.explode('Assay Name')
        matched_df = matched_df.astype(str)
        st.session_state.matched_df = matched_df

        # Process the panelDef dictionary into Dataframe
        if st.session_state.dict_source == 'Use the base dictionary':
            old_dict = st.session_state.medicare_panel
        if st.session_state.dict_source == 'Upload my own dictionary':
            old_dict = st.session_state.own_dict_sheet
        
        new_panelDict = st.session_state.new_panelDict
        new_dict = pd.DataFrame.from_dict(new_panelDict, orient='index').reset_index()
        new_dict.columns = ['Test Name', 'Include', 'Material', 'Result_Test']
        #new_dict.columns = [v if 'Unnamed' not in col else col for col, v in new_dict.iloc[0].items()]
        new_dict = pd.concat([old_dict, new_dict], axis=0).reset_index().drop('index', axis = 1)


        # output the excel file and let the user download
        sheet_list = ['Panel Definitions', 'Graph Data Worksheet', 'raw data with matching results', 'raw data']
        df_xlsx = dfs_to_excel([new_dict, matched_df, merged_raw, raw_data],  sheet_list)
        st.download_button(label='📥 Download Current Result 📥',
                                        data=df_xlsx ,
                                        file_name= 'df_test.xlsx')






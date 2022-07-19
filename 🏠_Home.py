import streamlit as st

st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })


st.sidebar.info('Select features above')

st.markdown("""
# 🏠Guide for LIS Translation Tool
An online tool for strategic workflow consultants to translate the raw LIS file from customers


## Suggested Steps
1. Fill in the missing timestamps and standardize the timestamps by the **Timestamps Formatting** page and download the formatted file.
2. Translate the formatted file with **LIS Translation** page and get the preliminary translation and panel definitions.
3. Download the traslated file and inspect the panel definition sheet. Fill in the corresponding Roche Assay name for the unknown LIS tests and check if the program-recommended assay names are correct. If not, please mannually correct it.
4. If there are tests that you don't want to include in the result file, please change the *Include* column to 0.
5. Visit the **Update Dictionary** page to upload your revised dictionary.
6. Go to **LIS Tranlation** page and redo the translation.


## Detailed guide for each page
### LIS Translation
Translate the LIS test names in raw data based on calculating the string similarity of LIS names to the test names in our base dictionary
#### Instructions
1. Select the file you want to translate. **ONLY EXCEL files are accpeted**
2. Select the sheet that contains the raw data.
3. Select the columns for *patient ID* and *LIS test names*.
4. Select the columns that you wish to include in the **5 columns worksheet**.
5. Click the **Upload Raw Data** button to upload.
6. Select the desired threshold for similarity score with the slide bar. The default score is 80.
7. (Optional) If you have uploaded your own dictionary at **Update Dictionary** page, please check the box.
8. After the result file is generated, the **Download Cuttent Result** button will show up. Click the button to download the result.


---


### Update Dictionary
The page for SWC to upload their own dictionary or the new panel definiton that revised by SWC.

**Please make sure the dictionary follows the format below, or the upload will not succeed.**
| Test Name | Include | Material | Assay Name |
| ----------- | ----------- | ----------- | ----------- |
| BMP | 1 | SERUM | CO27,GLU7,CA7,CREP7,BUN7|
| Insulin | 1 | SERUM | INSUL |

> - The 4 columns above are mandatory and the names need to be exactly the same as the example. However, it's fine that your dictionary contains other columns like *Similar Test*, *Confidence Score*. 
> - If a test name corresponds to multiple assays, please type all the assay names in **ONE cell** and separate the assays with commas(,)

#### Instructions
1. Select your dictionary file. **ONLY EXCEL files are accepted**
2. Select the sheet that contains your dictionary.
3. Click the **Upload Dictionary** button to upload.


---


### Timestamps Formatting
The page for SWC to fill in the missing timestamps in the raw data and format the timestamps into separate columns for data and time respectively.

#### Instructions
1. Select the file you want to translate. **ONLY EXCEL files are accpeted**
2. Select the sheet that contains the raw data.
3. Select the columns for *patient ID*
4. Select the timestamp columns which you want to format.
5. Select the delimiter that the raw file is using to separate data and time in the columns
6. Preview the formatted data below. If the result is correct, click **Download Current Result** to download the formatted file.

""")

import streamlit as st
import pandas as pd
import functions as f

st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })


st.title('🗃️LIS File Translation Tool🧰⚙️')
st.header('View and Download Base Dictionary')


base_dict = f.load_json('data/LIS DB.json')
base_dict = pd.DataFrame.from_dict(base_dict, orient='index').reset_index(drop = False)
base_dict.rename(columns={'index': 'LIS Test Name', 'AssayName': 'Assay Name'}, inplace = True)

st.dataframe(base_dict, width=1400)

df_xlsx = f.dfs_to_excel([base_dict], ['Base Dictionary'])
st.download_button(label='📥 Download Base Dictionary 📥',
                                data=df_xlsx,
                                file_name='Base Dictionary.xlsx')

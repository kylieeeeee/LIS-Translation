import streamlit as st

st.set_page_config(page_title="LIS Translation Tool", page_icon='🗃️', 
                layout="wide",
                initial_sidebar_state="expanded",
     menu_items={
         'About': "# This is the LIS file translation tool."
     })


st.title('🏠Homepage for LIS translation tool')
st.write('Here will be some instructions and README.md')
st.sidebar.info('Select features above')

import streamlit as st


st.header("Commit History of each Author")

with st.expander("Polo"):
    st.code("Polo Commits ------- Code")


with st.expander("CodingMaster"):
    st.write("Polo Commits")


with st.container():
    st.write("prueba")

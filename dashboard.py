import streamlit as st
import subprocess
import os
import sys


menu = ["Levelpack-UI", "Syntib-UI"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Levelpack-UI":
    st.title("Welcome to levelpack-UI")
    process = subprocess.Popen(["streamlit", "run", os.path.join(
        'levelpack-UI', 'usage.py')])


elif choice == "Syntib-UI":
    st.title("Welcome to Syntib-UI")


import streamlit as st
import subprocess
import os


menu = ["Levelpack-UI", "Syntib-UI"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Levelpack-UI":
    st.title("Welcome to levelpack-UI")
    process = subprocess.run(["streamlit", "run", os.path.join(
        '/home', 'lungsang', 'Desktop', 'levelpack-UI', 'usage.py')])


elif choice == "Syntib-UI":
    st.title("Welcome to Syntib-UI")
    process = subprocess.call(["streamlit", "run", os.path.join(
        '/home', 'lungsang', 'Desktop', 'syntib', 'usage.py')])
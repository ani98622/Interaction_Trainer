import streamlit as st
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

st.markdown("""
## Client Interaction Trainer!

This platform helps you improve your client interactions and leadership skills. Key features include:

- **Pitch Enhancement:** Get feedback and refine your pitch with real-time analysis.
- **Leadership Evaluation:** Assess and improve your leadership qualities through targeted practice.
- **Secure Login:** Access personalized projects after logging in.
- **Audio Responses:** Upload or record responses for AI-driven transcription and feedback.
- **Progress Dashboard:** Track your performance with an interactive score dashboard.

Log in via the sidebar, select a project, and start practicing with either recorded or new audio responses. Let’s boost your interview and leadership skills!
""")
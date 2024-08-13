import pandas as pd
import streamlit as st
import pandas as pd
import plotly.express as px
from database_sql import extract_from_data
from database_sql import get_project_ids

def plot_dashboard(data):
    dates = []
    f_scores = []
    t_scores = []
    c_scores = []

    for date, scores in data.items():
        if all(score is not None for score in scores):  # Ensure all scores are present
            dates.append(date)
            f_scores.append(scores[0])
            t_scores.append(scores[1])
            c_scores.append(scores[2])

    df = pd.DataFrame({
        'date': dates,
        'Fluency score': f_scores,
        'Truthfulness score': t_scores,
        'Communication score': c_scores
    })

    melted_data = df.melt(id_vars=['date'], value_vars=['Fluency score', 'Truthfulness score', 'Communication score'],
                          var_name='Score Types', value_name='score')

    fig = px.bar(melted_data, x='date', y='score', color='Score Types', 
                 title='Scores over Dates', labels={'score': 'Score', 'date': 'Date'})

    fig.update_xaxes(type='category')
    return fig

st.title('Dashboard')
if st.session_state.user_id:
    projs = get_project_ids(st.session_state.user_id)
    project_selected = st.sidebar.selectbox("Projects",['select a project'] + projs)
    if project_selected:
        if project_selected != 'select a project':
            val = extract_from_data(st.session_state.user_id,project_selected)
            if val:
                st.plotly_chart(plot_dashboard(val))
            else:
                st.write('No data available for this user and project.')
        else:
            st.markdown("""
        
    ## Welcome to the Dashboard!

- **Visualize Scores Over Time:** Track how different metrics have evolved across various projects.
- **Interactive Bar Plot:** View performance trends and progress using a dynamic bar chart.
- **Project Selection:** Choose a project from the sidebar to display its data.
- **Scores:** For every project we have:
  - **Truthfulness Score (t_score)**
  - **Fluency Score (f_score)**
  - **Communication Score (c_score)**
""")
else:
    st.markdown("""
        
    ## Welcome to the Dashboard!

- **Visualize Scores Over Time:** Track how different metrics have evolved across various projects.
- **Interactive Bar Plot:** View performance trends and progress using a dynamic bar chart.
- **Project Selection:** Choose a project from the sidebar to display its data.
- **Scores:** For every project we have:
  - **Truthfulness Score (t_score)**
  - **Fluency Score (f_score)**
  - **Communication Score (c_score)**
"""  )
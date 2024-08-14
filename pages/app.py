import streamlit as st,os,shutil
from database_sql import rag_answer, relevent_answer, insert_into_data_table, check_user_credentials, get_project_ids, get_question_texts
from audio_recorder_streamlit import audio_recorder
from audio_text import return_text,reduce_noise_in_audio
from main import output
# from dotenv import load_dotenv
# load_dotenv()

# os.environ['AUTOGEN_USE_DOCKER'] = "False"
# os.environ['TOKENIZERS_PARALLELISM']= "True"

if 'project' not in st.session_state:
    st.session_state.project = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'i' not in st.session_state:
    st.session_state.i = 0
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'model' not in st.session_state:
    st.session_state.model = "llama3-70b-8192"
if 'uploaded_audio' not in st.session_state:
    st.session_state.uploaded_audio = False
if 'recorded_audio' not in st.session_state:
    st.session_state.recorded_audio = False
if 'ques_selected' not in st.session_state:
    st.session_state.ques_selected = None

def login():
    if not st.session_state.logged_in:
        st.sidebar.write('User Login')
        user_id = st.sidebar.text_input('User ID (for login)')
        user_password = st.sidebar.text_input('Password (for login)', type='password')

        if st.sidebar.button('Login'):
            if check_user_credentials(user_id, user_password):
                st.success('Login successful')
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error('Invalid credentials')
                st.session_state.logged_in = False
    else:
        st.sidebar.write(f'Logged in as {st.session_state.user_id}')
        if st.sidebar.button('Logout'):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.uploaded_audio = False
            st.session_state.recorded_audio = False
            st.rerun()
    return st.session_state.user_id if st.session_state.logged_in else None

def clear_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

def get_id_que(user_id):
    if user_id:
        project_ids = get_project_ids(user_id)
        if project_ids:
            proj_selected = st.sidebar.selectbox("Choose Proj", ['select a project'] + project_ids, label_visibility='hidden')
            if proj_selected != 'select a project':
                if proj_selected:
                    questions = get_question_texts(proj_selected)
                    question_selected = st.sidebar.selectbox("Choose Que", ['Describe the Project'] + questions, label_visibility='hidden')
                    if question_selected:
                        return question_selected, proj_selected
                    else:
                        st.write('Request IT Team for ques.')
                        return None, None 
                else:
                    st.write("No Proj found.Request IT team")
                    return None, None
            else:
                #st.write('select project')
                return None, None

def save_uploaded_file(uploaded_file, filename=None):
    save_directory = './audiossss'
    os.makedirs(save_directory, exist_ok=True)
    if filename is None:
        with open(os.path.join(save_directory, uploaded_file.name), 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return uploaded_file.name
    else:
        with open(os.path.join(save_directory, filename), 'wb') as f:
            f.write(uploaded_file)

def audio_input(key):
    audio_file = st.file_uploader("Choose Audio", type=["wav", "mp3", "m4a"], help="Upload an audio file in .wav, .mp3, or .m4a format", label_visibility="hidden",key=key)
    if audio_file:
        path = save_uploaded_file(audio_file)
        st.audio(audio_file)
        return path

var1 = None
var2 = None
res = None
user_id = login()
ques_selected = None
if user_id:
    ques_selected, proj_id = get_id_que(user_id)
    st.session_state.project = proj_id
    
    if ques_selected == 'select a question':
        ques_selected = '!@#$%^&'

if ques_selected:
    if ques_selected != st.session_state.ques_selected:
        # st.empty()
        clear_directory('./audiossss')
        st.session_state.uploaded_audio = False
        st.session_state.recorded_audio = False
        st.session_state.ques_selected = ques_selected
        st.session_state.i += 1
        st.rerun()

    res = None
    st.header("Upload or Record Audio to start Training.")

    tab1, tab2 = st.tabs(["Upload Audio", "Record Audio"])
    with tab1:
        
        filename = audio_input(st.session_state.i)
        if filename:
            st.session_state.uploaded_audio = True
            if st.button("Submit",key="upload"):
                transcribed_text = return_text(f"./audiossss/{filename}")
                if transcribed_text:
                    st.write(transcribed_text)
                    st.info("transcription done")
                    with st.spinner("Analysing audio"):
                        PROBLEM = "Ques: " + ques_selected + " " + "Ans: " + transcribed_text
                        res = output(PROBLEM, rag_answer(project_id=proj_id, question_text=ques_selected, audio_answer=transcribed_text), relevent_answer(project_id = proj_id , question_text=ques_selected))
                else:
                    st.error("Could not transcribe audio")
        
    with tab2:
        audio_bytes = audio_recorder(text='Click to record',pause_threshold=10)
        if audio_bytes:
            st.session_state.recorded_audio = True
            st.session_state.i += 1
            filename = f"audio{st.session_state.i}.wav"
            save_uploaded_file(reduce_noise_in_audio(audio_bytes), filename=filename)
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Submit",key="record"):
                try:
                    transcribed_text = return_text(f"./audiossss/{filename}")
                    if transcribed_text:
                        st.info("transcription done")
                        with st.spinner("Analysing audio"):
                            PROBLEM = "Ques: " + ques_selected + " " + "Ans: " + transcribed_text
                            res = output(PROBLEM, rag_answer(project_id=proj_id, question_text=ques_selected, audio_answer=transcribed_text), relevent_answer(project_id = proj_id , question_text=ques_selected))
                except:
                    st.error("Could not transcribe audio.Please Re-record.")            
                
    if res:
        var1, var2 = res[0], res[1]
        st.write(var1)
        
        if var2:
            if var2['Truthfulness'] and var2['Fluency'] and var2['Communication']:
                insert_into_data_table(id=user_id, project_id=proj_id, question_text=ques_selected, date=var2['Date'], timestamp=var2['Serial'], t_score=var2['Truthfulness'], f_score=var2['Fluency'], c_score=var2['Communication'])
            else:
                insert_into_data_table(id=user_id, project_id=proj_id, question_text=ques_selected, date=var2['Date'], timestamp=var2['Serial'], t_score=0, f_score=0, c_score=0)
            

else:
    st.markdown("""
# Welcome to the Client Interaction Trainer!

This application is designed to help you prepare for client interactions by providing a platform to practice and receive feedback on your responses. Here are some of the key features:

- **Login and Project Selection**: Securely log in to access your personalized projects and questions.
- **Audio Input**: Upload or record audio responses to the provided questions. Our advanced AI system will transcribe and analyze your responses.
- **Feedback and Scoring**: Receive detailed feedback on your responses, including scores for truthfulness, fluency, and communication skills.
- **Dashboard**: Track your progress over time with an interactive dashboard displaying your scores.

### How to Get Started:
1. **Log In**: Use the sidebar on the left to log in securely.
2. **Select a Project**: Choose a project and a question to begin your training.
3. **Record or Upload Audio**: Either upload a pre-recorded audio file or record a new response directly within the app.
4. **Receive Feedback**: Get detailed feedback on your response, including areas of improvement.
5. **Track Progress**: Use the dashboard to monitor your scores over time and see your improvement.

Let's work together to enhance your client interaction skills!
""")
            
 
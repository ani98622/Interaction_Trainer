import sqlite3
from PyPDF2 import PdfReader
from summarizer import Summarizer
from retrieve import compressed_retriever1, compressed_retriever2

conn = sqlite3.connect('project.db')
cursor = conn.cursor()
model=Summarizer()

retriever_dict={"proj1":compressed_retriever1,'proj3':compressed_retriever2}

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id TEXT PRIMARY KEY,
    password TEXT NOT NULL
);
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS UserProjects (
    id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    PRIMARY KEY (id, project_id),
    FOREIGN KEY (id) REFERENCES Users(id)
    
);
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS ProjectsQuestions (
    project_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    PRIMARY KEY(project_id,question_text)
);
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS data(
    id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    question_text TEXT,
    date TEXT,
    timestamp INTEGER,
    t_score FLOAT,
    f_score FLOAT,
    c_score FLOAT                    
);
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS PrjctSumm(
    project_id TEXT PRIMARY KEY,
    Summ TEXT              
);
''')

conn.commit()
conn.close()

def get_summary_(pdf_docs,min_len=5,max_len=100,model=model):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    result = model(body=text, min_length=min_len, max_length=max_len)
    full = ''.join(result)
    return full

def rag_answer(project_id,question_text,audio_answer):
    retriever=retriever_dict[project_id]
    compressed_docs = retriever.invoke(f"question:{question_text},answer:{audio_answer}")
    combined_text = '\n\n'.join([doc.page_content for doc in compressed_docs])
    return combined_text

def relevent_answer(project_id,question_text):
    if question_text == "!@#$%^&":
        conn = sqlite3.connect('project.db')
        cursor = conn.cursor()
        query = '''
        SELECT Summ 
        FROM  PrjctSumm
        WHERE project_id = ?
        '''
        cursor.execute(query, (project_id,))
        summary = cursor.fetchall()
        conn.close()
        return summary
    retriever=retriever_dict[project_id]
    compressed_docs = retriever.invoke(f"question:{question_text}")
    combined_text = '\n\n'.join([doc.page_content for doc in compressed_docs])
    return combined_text

def insert_into_data_table(id,project_id,question_text,date,timestamp,t_score,f_score,c_score):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    INSERT INTO data (id,project_id,question_text,date,timestamp,t_score,f_score,c_score)
    VALUES (?,?,?,?,?,?,?,?)
    '''

    cursor.execute(query,(id,project_id,question_text,date,timestamp,t_score,f_score,c_score))
    conn.commit()
    conn.close()
    
def user_exists(user_id):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    SELECT 1 FROM Users WHERE id = ? 
    '''
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:       
        return True 
    else:           
        return False

def insert_into_users_table(id, password):
    if user_exists(id):
        return False  # User already exists
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    INSERT INTO Users (id, password)
    VALUES (?, ?)
    '''
    cursor.execute(query, (id, password))
    conn.commit()
    conn.close()
    return True

def insert_into_userprojects_table(id, project_id):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    INSERT INTO UserProjects (id, project_id)
    VALUES (?, ?)
    '''

    cursor.execute(query, (id, project_id))
    conn.commit()
    conn.close()

def insert_into_projectsquestions_table(project_id, question_text):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    INSERT INTO ProjectsQuestions (project_id, question_text)
    VALUES (?, ?)
    '''
    cursor.execute(query, (project_id, question_text))
    conn.commit()
    conn.close()

def check_user_credentials(user_id, password):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    SELECT 1 FROM Users WHERE id = ? AND password = ?
    '''
    cursor.execute(query, (user_id, password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_project_ids(user_id):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    SELECT project_id 
    FROM UserProjects 
    WHERE id = ?
    '''
    cursor.execute(query, (user_id,))
    results = cursor.fetchall()
    conn.close()
    project_ids = [result[0] for result in results] if results else []
    return project_ids

def get_question_texts(project_id):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
    SELECT question_text
    FROM ProjectsQuestions 
    WHERE project_id = ?
    '''
    cursor.execute(query, (project_id,))
    results = cursor.fetchall()
    conn.close()
    question_texts = [result[0] for result in results]
    return question_texts

def get_dates_for_id_and_project_id(id, project_id):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    query = """
    SELECT date 
    FROM data 
    WHERE id = ? AND project_id = ?
    """
    
    cursor.execute(query, (id, project_id))
    dates = cursor.fetchall()
    conn.close()
    date_list = [date[0] for date in dates]
    return date_list

def get_scores_for_highest_timestamp(id, project_id, date, question_text):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    query = """
    SELECT t_score, f_score, c_score
    FROM data
    WHERE id = ? AND project_id = ? AND date = ? AND question_text = ?
    ORDER BY timestamp DESC
    LIMIT 1
    """
    
    cursor.execute(query, (id, project_id, date, question_text))
    
    scores = cursor.fetchone()
    
    conn.close()
    
    if scores:
        return {
            "t_score": scores[0],
            "f_score": scores[1],
            "c_score": scores[2]
        }
    else:
        return None

def extract_from_data(id,project_id):
    date_list=get_dates_for_id_and_project_id(id, project_id)
    question_texts=get_question_texts(project_id)
    no_question=len(question_texts)
    di={}
    for i in range(len(date_list)):
        date=date_list[i]
        t_score=0.0
        f_score=0.0
        c_score=0.0
        for question_text in question_texts:
            d=get_scores_for_highest_timestamp(id, project_id, date, question_text)
            if d!=None:
                t_score+=d["t_score"]
                f_score+=d["f_score"]
                c_score+=d["c_score"]
            else:
                for j in range(i-1,-1,-1):
                    new_date=date_list[j]
                    d=get_scores_for_highest_timestamp(id, project_id, new_date, question_text)
                    if d:
                        t_score+=d["t_score"]
                        f_score+=d["f_score"]
                        c_score+=d["c_score"]
                        break
        di[date]=[t_score/no_question,f_score/no_question,c_score/no_question]
    return di

def add_summ(project_id,summary):
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    query = '''
        INSERT INTO PrjctSumm (project_id,Summ)
    VALUES (?, ?)
        '''
    cursor.execute(query, (project_id,summary))
    conn.commit()
    conn.close()
    return "Project sucessfully added"


# text = """The paper "Attention Is All You Need" by Vaswani et al. presents the Transformer model, a novel architecture designed for sequence transduction tasks, such as machine translation and language modeling. The model is notable for relying solely on self-attention mechanisms, dispensing with recurrent or convolutional layers found in traditional architectures. This design choice enables the Transformer to process input sequences in parallel, greatly improving computational efficiency and reducing training times.

# The Transformer is composed of an encoder-decoder structure. The encoder's role is to convert the input sequence into a sequence of continuous representations, while the decoder generates the corresponding output sequence using this representation. Both the encoder and decoder consist of a stack of identical layers. Each encoder layer has two main components: a multi-head self-attention mechanism and a position-wise fully connected feed-forward network. The multi-head attention mechanism allows the model to focus on different parts of the input sequence by computing attention scores from multiple perspectives simultaneously. The position-wise feed-forward network applies transformations to each position in the sequence independently.

# One of the key innovations of the Transformer is the use of positional encodings, which are added to the input embeddings to maintain the positional information of tokens in the sequence. This is crucial because the model does not have inherent knowledge of the order of the sequence elements, unlike recurrent networks.

# The decoder mirrors the encoder structure but includes an additional multi-head attention mechanism that attends to the encoder's output, facilitating the generation of the output sequence. This design allows the model to condition each generated output token on the entire input sequence and the previously generated tokens.

# The authors demonstrate the effectiveness of the Transformer by achieving state-of-the-art results on the WMT 2014 English-to-German and English-to-French translation tasks. The model outperforms previous architectures, such as recurrent neural networks and convolutional neural networks, in terms of both accuracy and training efficiency. The introduction of the Transformer marks a significant shift in the field of natural language processing, showcasing the power of self-attention mechanisms in capturing complex dependencies in sequential data. The paper suggests that this architecture can be extended to various other tasks beyond translation, paving the way for future research and applications."""
# add_summ("proj3",text)

# text1 = """
# The "FAQ_SWAYAM 1" document provides an extensive overview of the SWAYAM platform, an initiative by the Government of India for delivering Massive Open Online Courses (MOOCs). SWAYAM stands for "Study Webs of Active-learning for Young Aspiring Minds" and aims to facilitate lifelong learning opportunities. It offers courses for students from 9th grade to postgraduate levels, covering a wide range of disciplines including arts, science, commerce, engineering, and more. The courses are created by top educators from across India and are accessible to anyone globally.

# Courses on SWAYAM are free, though there may be a nominal fee for certification. The platform uses a four-quadrant approach for course delivery, which includes video lectures, downloadable reading material, self-assessment tests, and an online discussion forum. SWAYAM also allows for credit transfer under the UGC (Credit Framework for online learning courses) Regulation 2016, enabling students to transfer credits earned through these courses to their academic records in their respective institutions. The initiative is part of the broader Digital India program and aims to improve the quality of education, address the shortage of quality teachers, and increase the Gross Enrollment Ratio in higher education. The document also details registration procedures, course search and selection, and other operational aspects of the SWAYAM platform.
# """
# add_summ("proj1",text1)

# insert_into_users_table("user1",password="password123")
# insert_into_users_table("user2",password="password124")
# insert_into_users_table("user3",password="password125")
# insert_into_userprojects_table("user1",project_id="proj1")
# insert_into_userprojects_table("user2",project_id="proj2")

# insert_into_userprojects_table('user1',project_id='proj3')
# insert_into_projectsquestions_table("proj3","What is the Transformer architecture?")
# insert_into_projectsquestions_table("proj3","How does self-attention work?")
# insert_into_projectsquestions_table("proj3","What is multi-head attention?")
# insert_into_projectsquestions_table("proj3","What are positional encodings?")
# insert_into_projectsquestions_table("proj3","Why is the Transformer model efficient?")


 
# add_summ("proj3",pdf_paths_proj2)


# insert_into_projectsquestions_table("proj1","What are the outcomes of the SWAYAM.")
# insert_into_projectsquestions_table("proj1","How can I select a course on Swayam?")
# insert_into_projectsquestions_table("proj1","Will a Learner earn Credits & certificate after going through the MOOCs on SWAYAM?")
# insert_into_projectsquestions_table("proj1","Has Government embarked upon an ICT Programme in the Past?")

# insert_into_projectsquestions_table("proj1","What different activities can a learner do within a discussion forum?")

# insert_into_projectsquestions_table("proj2","What is the Transformer architecture?")
# insert_into_projectsquestions_table("proj2","How does self-attention work?")
# insert_into_projectsquestions_table("proj2","What is multi-head attention?")
# insert_into_projectsquestions_table("proj2","What are positional encodings?")
# insert_into_projectsquestions_table("proj2","Why is the Transformer model efficient?")

# insert_into_data_table("user1","proj1","Will a Learner earn Credits & certificate after going through the MOOCs on SWAYAM?","2024-07-23",20240723,66.7,78.07,66)
# print(get_scores_for_highest_timestamp("user1","proj1","2024-07-23", "Will a Learner earn Credits & certificate after going through the MOOCs on SWAYAM?"))
# print(extract_from_data("user1","proj1"))

# insert_into_data_table("user1","proj1","Will a Learner earn Credits & certificate after going through the MOOCs on SWAYAM?","23-07-2024",20240723,67,98,76)
# insert_into_data_table("user1","proj1","How can I select a course on Swayam?","23-07-2024",20240723,89,90,99)
# insert_into_data_table("user1","proj1","Has Government embarked upon an ICT Programme in the Past?","24-07-2024",20240723,56,78,87)
# insert_into_data_table("user1","proj1","Has Government embarked upon an ICT Programme in the Past?","24-07-2024",20240723,56,66,67)
# insert_into_data_table("user1","proj1","What are the outcomes of the SWAYAM.","25-07-2024",20240723,90,34,56)
# insert_into_data_table("user1","proj1","What different activities can a learner do within a discussion forum?","26-07-2024",20240723,89,90,90)


# insert_into_data_table("user1","proj3","How does self-attention work?","23-07-2024",20240723,60,70,80)
# insert_into_data_table("user1","proj3","What is the Transformer architecture?","23-07-2024",20240723,88,90,45)
# insert_into_data_table("user1","proj3","What is the Transformer architecture?","24-07-2024",20240724,80,56,78)
# insert_into_data_table("user1","proj3","What is multi-head attention?","25-07-2024",20240725,34,54,78)
# insert_into_data_table("user1","proj3","What are positional encodings?","26-07-2024",20240726,98,45,66)
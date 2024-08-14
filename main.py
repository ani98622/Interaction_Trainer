from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import os,re
from autogen.agentchat import GroupChat, AssistantAgent, GroupChatManager, Agent
from datetime import datetime

a=0
def output(PROBLEM,doc,Relv):
    config_list = [
        {"api_type": "groq", "model": "llama3-70b-8192", "api_key": "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"}
    ]

    # config_list = [
    #     {"api_type": "groq", "model": "llama3-70b-8192", "api_key": os.getenv("GROQ_API_KEY")}
    # ]
    
    def extract_club_up_content(response):
        for item in response:
            if item.get('name') == 'Club_up':
                return item.get('content')
        return None
    
    def termination_msg(x):
        return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()
    
    def extract_scores(input_string):
        current_datetime = datetime.now()
        if input_string == "Your answer is completely irrelevant to the question you have selected. Recheck your question or answer and try again.":
            scores = {
            'Overall': 0,
            'Truthfulness': 0,
            'Fluency': 0,
            'Communication': 0,
            'Date': datetime.now().strftime('%d-%m-%Y'),
            'Serial': f"{current_datetime.year}{current_datetime.month:02d}{current_datetime.day:02d}{current_datetime.hour:02d}{current_datetime.minute:02d}{current_datetime.second:02d}"


            }
            return scores

        
        scores = {
            'Overall': None,
            'Truthfulness': None,
            'Fluency': None,
            'Communication': None
        }

        # Updated regex pattern to match all score formats
        score_pattern = r'(?:{})\s*(?:score|Score)(?:\s*:)?\s*(\d+(?:\.\d+)?)'

        for category in scores.keys():
            match = re.search(score_pattern.format(category), input_string, re.IGNORECASE)
            if match:
                try:
                    scores[category] = float(match.group(1))
                except ValueError:
                    # In case of any unexpected format, keep it as None
                    pass

        # Add current date and serial
        current_datetime = datetime.now()
        scores['Date'] = current_datetime.strftime('%d-%m-%Y')
        
        # Create serial number with two-digit month, date, hour, minutes, and seconds
        scores['Serial'] = f"{current_datetime.year}{current_datetime.month:02d}{current_datetime.day:02d}{current_datetime.hour:02d}{current_datetime.minute:02d}{current_datetime.second:02d}"

        return scores
            

    llm_config = {"config_list": config_list, "timeout": 60, "temperature": 0.8, "seed": 1234}
    
    
    Boss = RetrieveUserProxyAgent(
        name="Boss",
        is_termination_msg=termination_msg,
        system_message= "You retrieve information whenever TruthChecker agent wants it.",
        human_input_mode="NEVER",
        default_auto_reply="Reply `TERMINATE` if the task is done.",
        max_consecutive_auto_reply=3,
        retrieve_config={
            "task": "qa",
            "docs_path": doc,
            "chunk_token_size": 1000,
            "model": config_list[0]["model"],
            "collection_name": "groupchat",
            "get_or_create": True,
        },
        code_execution_config=False,
        description="""Can retrieve extra content for solving difficult problems.
        Provide retrieved information only to `TruthChecker`.""")
    
    RelevanceVerifier = RetrieveUserProxyAgent(
        name="RelevanceVerifier",
        is_termination_msg=termination_msg,
        system_message=""" You retrieve information whenever RelevanceAgent wants it.""",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        retrieve_config={
            "task": "qa",
            "docs_path": Relv,
            "chunk_token_size": 1000,
            "model": config_list[0]["model"],
            "collection_name": "groupchat",
            "get_or_create": True,
        },
        code_execution_config=False,
        description= """Can retrieve extra content for solving difficult problems.
        Acts immediately after Boss. Provide retrieved information only to `RelevanceAgent`"""
    )
    
    RelevanceAgent = AssistantAgent(
        name="RelevanceAgent",
        is_termination_msg=termination_msg,
        system_message="""RelevanceAgent:  
        if the Question is "!@#$%^&":
            Verify the ANSWER (converted from audio) given in `Boss` is relevant to the data from RelevanceVerifier.
            Output format:
                If the relevance is less than 20%, output:
                    "IRRELEVANT"
                If the relevance is greater than 20%, output:
                    "RELEVANT"
        if the Question is not "!@#$%^&":
            Verify the ANSWER (converted from audio) given in `Boss` is relevant to the Question using data from RelevanceVerifier.
            Output format:
                If the relevance is less than 20%, output:
                    "IRRELEVANT"
                If the relevance is more than 20%, output:
                    * <If any irrelevant content exists, list it and suggest its removal.>
                    * <If any relevant content is missing, list it and suggest its addition.>
        Notes:
        - Ignore square brackets in the ANSWER and content within them.
        - Do not comment on filler words, grammar mistakes, unclear phrases or pauses. Assume they contribute to relevance.
        - Focus only on content relevance, ignoring language accuracy.""",
        llm_config=llm_config,
        description="""Take information from RelevanceVerifier only.""",
    )
    
    TruthChecker = AssistantAgent(
        name="TruthChecker",
        is_termination_msg=termination_msg,
        system_message="""Truthfulness Checker: Boss has a DOCUMENT and a PROBLEM. 
        The PROBLEM contains an Answer (converted from audio). 
        The DOCUMENT contains texts relevant to the question from a reliable source. 
        Retrieve information from it.

        In both cycles, Verify the truthfulness of the answer against the document. 
        Provide a score out of 100 based on accuracy and truthfulness.

        Output Format:
        "Truthfulness score: <1.00-99.99>/100
        *<If there are any factually incorrect statements:
            List each incorrect statement and the contradictory statement from the document.
            If none, do not provide this point.>
        *<If any statements cannot be verified:
            Assume they are true and mention the assumption.
            If all statements can be verified, do not provide this point.>
        *<If there are contradictory statements within the answer:
            Point out the contradictory statements from the answer.
            If none, do not provide this point.>"
        
        Notes:
        - Ignore square brackets in the answer and content within them.
        - Do not summarize or comment on other agents' feedback. Stick strictly to the instructions.
        - You must only play the role of TruthChecker.""",
        llm_config=llm_config,
        description="""Take information from Boss only. """,
    )  
    
    FluencyReviewer = AssistantAgent(
        name="FluencyReviewer",
        is_termination_msg=termination_msg,
        system_message="""Fluency Reviewer: Boss message contains a PROBLEM with a Question and 
        an Answer (converted from audio). Review the Answer for fluency and clarity.

        Instructions:
            In both cycles, Point out any filler words, repetitive words, pauses, or unclear phrases.
            Provide a fluency score out of 100.
        Output Format:
            "Fluency score: <0.00-100>/100

            * <List filler words and suggest alternatives if they exist. If none, omit this point.>
            * <List repetitive words and suggest alternatives if they exist. If none, omit this point.>
            * <For pauses in square brackets (indicating length), list pauses with their length and position 
                (mention phrase before and after it). If none, omit this point.>
            * <For unintelligible phrases in square brackets, list all unclear phrases. If none, omit this point.>
        Notes:
        - Do not summarize or comment on other agents' feedback. Stick strictly to the instructions.
        - Only play the role of FluencyReviewer.""",
        llm_config=llm_config,)
    
    CommunicationCoach = AssistantAgent(
        name="CommunicationCoach",
        is_termination_msg=termination_msg,
        system_message="""Communication Coach: Review the text converted from audio, 
        focusing on language appropriateness, grammar, engagement, and positivity.

        Instructions:
        Identify cuss words, inappropriate language, or informal words, and suggest the alternatives.
        Correct any grammar errors. Explain how to rectify it.
        Provide suggestions to enhance engagement and positivity if needed.
        
        Output Format:
        "Communication score: <0.00-100>/100
        * <List inappropriate words and suggest alternatives if they exist. If none, omit this point.>
        * <List informal phrases and suggest alternatives if they exist. If none, omit this point.>
        * <List grammatical errors and corrections if they exist. If none, omit this point.>
        * <If the answer is either boring or negative, suggest how to make it engaging and positive. If not, omit this point.>
        
        Notes:
        - Ignore square brackets and content within them.
        - Do not summarize or comment on other agents' feedback. Stick strictly to the instructions.
        - Only play the role of CommunicationCoach.
        """,
        llm_config=llm_config,
        )
    
    Club_up = AssistantAgent(
        name="Club_up",
        is_termination_msg=termination_msg,
        system_message="""Club_up Agent:
        If `CommunicationCoach` was the previous Agent:
            Tasks:
            Give an overall score.
            Compile all results from `RelevanceAgent`, `TruthChecker`, `FluencyReviewer`, and `CommunicationCoach` in well explained maner without making it concise.
            Output Format:
            "Overall score: <Average of Truthfulness score, Fluency score, Communication score> / 100
            Truthfulness score <Truthfulness score> / 100 | Fluency score : <Fluency score> / 100 | Communication Score : <Communication score> / 100
            * <List all reviews and suggestions from RelevanceAgent agent>
            * <List all reviews and suggestions from TruthChecker agent without mentioning the score.>
            * <List all reviews and suggestions from FluencyReviewer agent without mentioning the score.>
            * <List all reviews and suggestions from CommunicationCoach agent without mentioning the score.>
        If `RelevanceAgent` is the previous agent and its output was "IRRELEVANT":
           "Your answer is completely irrelevant to the question you have selected. Recheck your question or answer and try again."

    Notes:
    - Don't miss any point or its explanation.
    - Stick strictly to the output format.
    - Avoid any introductions or summaries.
    - Avoid repeated points and remove the points which says None or not found.
    - Only play the role of Club_up.
        """,
        llm_config=llm_config,
        )
    
    def custom_speaker_selection_func(last_speaker: Agent, groupchat: GroupChat):
        global a
        messages = groupchat.messages
        if last_speaker is Boss:
            return RelevanceVerifier
        if last_speaker is RelevanceVerifier:
            return RelevanceAgent
        if last_speaker is RelevanceAgent:
            if "IRRELEVANT" in messages[-1]["content"]:
                return Club_up
            else:
                return TruthChecker
        if last_speaker is TruthChecker:
            return FluencyReviewer
        if last_speaker is FluencyReviewer:
            return CommunicationCoach
        if last_speaker is CommunicationCoach:
            if a==0:
                a=a+1
                return TruthChecker
            else:
                return Club_up
            
 
    agents = [Boss,RelevanceVerifier,RelevanceAgent,TruthChecker,FluencyReviewer,CommunicationCoach,Club_up]
    
    group_chat = GroupChat(agents=agents, messages=[], max_round=10, speaker_selection_method=custom_speaker_selection_func, speaker_transitions_type="allowed")
    
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
    )

    
    chat_hist = Boss.initiate_chat(
        manager,
        message=PROBLEM,
        clear_history=True
    )
    
    response = extract_club_up_content(chat_hist.chat_history)

    return [response, extract_scores(response)]
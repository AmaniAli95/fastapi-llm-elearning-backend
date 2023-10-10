import os
import streamlit as st
import openai
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from streamlit_chat import message

# Set Streamlit page config
st.set_page_config(page_title="LearnGPT")
st.markdown("<h1 style='text-align: center;'>LearnGPT \U0001F916</h1>", unsafe_allow_html=True)

# Initialize session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "system", "content": "You are a helpful assistant."}]

# Sidebar - Allow the user to clear the conversation
st.sidebar.title("Sidebar")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# Reset the conversation
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [{"role": "system", "content": "You are a helpful assistant."}]

# Set up OpenAI API key
os.environ["OPENAI_API_KEY"] = 'sk-k0A75H1W1EgBVt'

# Initialize LangChain components
persist_directory = 'db'
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
retriever = vectordb.as_retriever(search_kwargs={"k": 1})

# Set up the turbo LLM
turbo_llm = ChatOpenAI(
    temperature=0,
    model_name='gpt-3.5-turbo'
)

# Create the chain to answer questions
qa_chain = RetrievalQA.from_chain_type(
    llm=turbo_llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# Define a function to process the LLM response
def process_llm_response(llm_response):
    result = llm_response['result']
    sources = [source.metadata['source'] for source in llm_response["source_documents"]]
    return result, sources

# Generate a response based on user input
def generate_response(query):
    llm_response = qa_chain(query)
    result, sources = process_llm_response(llm_response)
    return result, sources

# Container for chat history
response_container = st.container()

# Container for text box
container = st.container()

# User input form
with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output, sources = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)

# Display chat history
if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))

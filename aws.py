import streamlit as st
import boto3
import json
from dotenv import load_dotenv
import os

# Loading environment variables from .env file
load_dotenv()

# Set up the AWS profile and initialize the Bedrock clients
# boto3.setup_default_session(profile_name=os.getenv('profile_name'))
bedrock = boto3.client('bedrock-runtime', 'us-east-1')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime','us-east-1')

# Retrieve knowledge base ID from environment variable
knowledge_base_id = os.getenv('knowledge_base_id')

# Function to get contexts from knowledge base (same as in your provided code)
def get_contexts(query, kbId, numberOfResults=5):
    results = bedrock_agent_runtime.retrieve(
        retrievalQuery={'text': query},
        knowledgeBaseId=kbId,
        retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': numberOfResults}}
    )
    contexts = [result['content']['text'] for result in results['retrievalResults']]
    return contexts

# Function to answer the user query using both knowledge base context and Claude model
def answer_query(user_input):
    # Get the context for the user input from the knowledge base
    userContexts = get_contexts(user_input, knowledge_base_id)

    # Format the prompt for Claude
    prompt_data = """
    You are a Question and answering assistant and your responsibility is to answer user questions based on provided context
    
    Here is the context to reference:
    <context>
    {context_str}
    </context>

    Referencing the context, answer the user question
    <question>
    {query_str}
    </question>
    """

    # Format the prompt with the context and the user query
    formatted_prompt_data = prompt_data.format(context_str='\n'.join(userContexts), query_str=user_input)

    # Configure model parameters
    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.5,
        "messages": [{"role": "user", "content": [{"type": "text", "text": formatted_prompt_data}]}]
    }

    # Send the request to Claude
    json_prompt = json.dumps(prompt)
    response = bedrock.invoke_model(body=json_prompt, modelId="anthropic.claude-3-sonnet-20240229-v1:0", accept="application/json", contentType="application/json")
    
    # Parse the response and return the answer
    response_body = json.loads(response.get('body').read())
    answer = response_body['content'][0]['text']
    return answer

# Set up Streamlit chatbot interface
st.set_page_config(layout='wide', page_title='AI Chatbot')
def chatbot():
    st.title("Chatbot - AI Powered by AWS Bedrock")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display chat history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask me anything!"):
        # Add user message to session history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get the answer from knowledge base or Claude
        response_text = answer_query(prompt)

        # Display assistant's response
        with st.chat_message("assistant"):
            st.markdown(response_text)

        # Add assistant's response to session history
        st.session_state.messages.append({"role": "assistant", "content": response_text})

# Run the chatbot function
if __name__ == "__main__":
    chatbot()

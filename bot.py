import streamlit as st
import boto3
import json

# Initialize the Bedrock clients
bedrock = boto3.client(service_name='bedrock-runtime', region_name='us-west-2')
bedrock_agent = boto3.client(service_name='bedrock-agent-runtime', region_name='us-west-2')

def retrieve_relevant_context(query, knowledge_base_id):
    """
    Retrieve relevant context from the knowledge base
    :param query: User's query
    :param knowledge_base_id: ID of the knowledge base
    :return: Retrieved context as a string
    """
    try:
        # Retrieve relevant passages from the knowledge base
        response = bedrock_agent.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': query
            }
        )
        
        # Extract and combine the retrieved passages
        if response.get('retrievalResults'):
            # Limit to first 3 results manually
            context = "\n\n".join([
                result.get('content', {}).get('text', '') 
                for result in response['retrievalResults'][:3]
            ])
            return context
        return ""
    
    except Exception as e:
        st.error(f"Error retrieving context: {e}")
        return ""

def chatbot():
    # Configure your knowledge base ID
    KNOWLEDGE_BASE_ID = "JO5A2U5W9L"  # Replace with your actual knowledge base ID

    st.title("EventBot - AI Powered by AWS Bedrock with Knowledge Base")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display chat messages from history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask me anything!"):
        # Add the user's message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Retrieve relevant context from knowledge base
        relevant_context = retrieve_relevant_context(prompt, KNOWLEDGE_BASE_ID)

        # Create the conversation context to pass to Bedrock
        prompt_memory = ""
        for message in st.session_state["messages"]:
            prompt_memory += message["role"] + ": " + message["content"] + "\n"

        # Construct enhanced prompt with retrieved context
        enhanced_prompt = f"""
        Context from knowledge base:
        {relevant_context}

        Conversation History:
        {prompt_memory}

        User Query:
        {prompt}

        Please provide a helpful and contextually relevant response based on the given context and conversation history. 
        If the context provides specific information relevant to the query, incorporate those details into your response.
        If no relevant context is found, respond based on your general knowledge.
        """

        # Create the request body for the Bedrock API call
        kwargs = {
            "modelId": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "top_k": 250,
                "temperature": 0.7,
                "top_p": 0.999,
                "messages": [
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ]
            })
        }

        # Invoke the model (Claude)
        try:
            response = bedrock.invoke_model(**kwargs)

            # Decode the response body
            body = json.loads(response['body'].read())

            # Extract the assistant's response text
            response_text = body['content'][0]['text']

            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(response_text)

            # Add assistant's response to session history
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            st.error(f"Error: {e}")

# Run the chatbot function
if __name__ == "__main__":
    chatbot()
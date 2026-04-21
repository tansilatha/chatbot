import streamlit as st
from langgraph_tool_backend import chatbot,retrieve_all_threads
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage 
import uuid
#************************* utility function *************8
def generate_thread_id():
    return str(uuid.uuid4())
def reset_chat():
    thread_id =generate_thread_id()
    st.session_state['thread_id']=thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history']=[]

def move_thread_to_top(thread_id):
    if thread_id in st.session_state['chat_threads']:
        st.session_state['chat_threads'].remove(thread_id)
    st.session_state['chat_threads'].insert(0, thread_id)

def add_thread(thread_id):
    move_thread_to_top(thread_id)
    if thread_id not in st.session_state['chat_labels']:
        n = len(st.session_state['chat_labels']) + 1
        st.session_state['chat_labels'][thread_id] = f"thread-{n}"

def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    if not state or not getattr(state, "values", None):
        return []
    return state.values.get('messages', [])

#*****************sesssion setup**********************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id']=generate_thread_id()
if "chat_threads" not in st.session_state:
    st.session_state['chat_threads']=retrieve_all_threads()
if "chat_labels" not in st.session_state:
    st.session_state['chat_labels'] = {}
    for i, tid in enumerate(st.session_state['chat_threads'], start=1):
        st.session_state['chat_labels'][tid] = f"thread-{i}"
add_thread(st.session_state['thread_id'])

#****SIDEBAR UI ********************************
st.sidebar.title("Langgraph Chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()
st.sidebar.header("My Conversation")
for thread_id in list(st.session_state['chat_threads']):
    base_label = st.session_state['chat_labels'].get(thread_id, 'thread')
    is_active = thread_id == st.session_state['thread_id']
    label = f"* {base_label}" if is_active else base_label
    if st.sidebar.button(label, key=f"chat_{thread_id}"):
        move_thread_to_top(thread_id)
        st.session_state['thread_id']=thread_id
        messages=load_conversation(thread_id)
        temp_messages=[]
        for message in messages:
            if isinstance(message,HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role':role,'content':message.content})
        st.session_state['message_history']=temp_messages
        st.rerun()

#************************main UI **************************
# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

#{'role': 'user', 'content': 'Hi'}
#{'role': 'assistant', 'content': 'Hi=ello'}

user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # Assistant streaming block
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    # Save assistant message
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )
# LangGraph Streamlit Chatbot

This repository contains a Streamlit frontend and a LangGraph backend for a tool-using chatbot.

## Main files

- [streamlit_frontend_tool.py](streamlit_frontend_tool.py)
- [langgraph_tool_backend.py](langgraph_tool_backend.py)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy [.env.example](.env.example) to `.env` and set your values.

## Run

Start the app with:

```bash
streamlit run streamlit_frontend_tool.py
```

## Notes

- Do not commit `.env` or `chatbot.db`.
- The backend expects `OPENROUTER_API_KEY` and optionally `MODEL_NAME`.

from .llm_client import make_chat_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain.agents import AgentExecutor


def build_my_agent() -> AgentExecutor:
    llm = make_chat_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            ("human", "{input}"),
        ]
    )
    return RunnableSequence(prompt | llm)

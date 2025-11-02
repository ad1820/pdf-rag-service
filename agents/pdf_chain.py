from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from models.embeddings_faiss import create_faiss_index, get_retriever
from config.settings import OPENAI_API_KEY

def create_pdf_chain(text: str):
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found.")

    vectorstore = create_faiss_index(text)
    retriever = get_retriever(vectorstore)

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.1,
        api_key=OPENAI_API_KEY,
        streaming=True
    )
    system_prompt = (
        "You are an intelligent PDF assistant. Your main goal is to help the user "
        "by answering questions using the provided PDF content as your primary source of truth.\n\n"
        "However, if the user's question is relevant to the topic of the PDF but not directly answered "
        "within the provided context, you may use your general knowledge to give a helpful and reasonable answer.\n\n"
        "If the question is completely unrelated to the PDF or outside its scope, reply with: "
        "'This seems unrelated to the PDF.'\n\n"
        "Be concise, factual, and conversational.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain
# Since Azure Open AI models are not giving the proper response. Developed a chatbot by using Chainlit framework, I'm utilizing other open source models.

from langchain_community.document_loaders import PyPDFLoader # For loading the Pdf
from langchain.prompts import PromptTemplate # Prompt template
from langchain_pinecone import PineconeVectorStore # Vector Database
from langchain.text_splitter import RecursiveCharacterTextSplitter # For Chunking
from langchain.chains import RetrievalQA # For Retrieval
from langchain_groq import ChatGroq # Inference Engine
from dotenv import load_dotenv # For detecting env variables
from langchain.embeddings import OllamaEmbeddings # To perform vector embeddings
import chainlit as cl # For user interface
from langchain_groq import ChatGroq # Inference Engine

load_dotenv() # Detecting env 

# Defining prompt 
prompt_template = """ 

    You are a financial analyst expert at summarizing the complex amazon financial report that has been given to you.
    
    Analyze the amazon financial report and provide
        1. A detailed performance summary
        2. Calculate the following financial ratios
        3. Summarize the key risk factors
        
           Output Format:
        - Performance Summary: [Comprehensive overview of financial performance]
        - Financial Ratios (Table):
            Current Ratio
            Debt-to-Equity Ratio
            Return on Equity (ROE)
            Return on Assets (ROA)
            Gross Profit Margin
            Net Profit Margin
            Earnings Per Share (EPS)
        - Risk Factors Summary: [Key risks identified in the report]

    Context: {context} Question: {question}

    Helpful answer:
    
"""

# Just created a function to interact with the prompt template
def set_custom_prompt():
    prompt = PromptTemplate(template=prompt_template, input_variables=['context', 'question'])  
    return prompt

# Defined this function to perform retrieval
def retrieval_qa_chain(llm, prompt, db):
    qa_chain = RetrievalQA.from_chain_type(
        llm, retriever=db.as_retriever(), chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain

# This function is for defining llm model
def load_llm():
    groqllm = ChatGroq(
        model ="llama3-8b-8192", temperature=0
    )
    return groqllm

# Here just loading the pdf and transforming it to chunks, and performing vector embeddings as well as storing the vector embeddings in Pinecone vector database.
def qa_bot():
    
    data = PyPDFLoader('C:\\Users\\USER\\OneDrive\\Desktop\\NeoStats Hackathon\\Amazon-com-Inc-2023-Annual-Report.pdf')
    loader = data.load()
    chunk = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=0)
    splitdocs = chunk.split_documents(loader)
    index_name = "langchain2"
    db = PineconeVectorStore.from_documents(splitdocs[:5], OllamaEmbeddings(model ="mxbai-embed-large"),index_name=index_name)
    llm = load_llm()
    qa_prompt = set_custom_prompt()
    qa = retrieval_qa_chain(llm, qa_prompt, db)
    return qa


# Chainlit decorator for starting the app
@cl.on_chat_start
async def start():
    chain = qa_bot()
    msg = cl.Message(content="Starting the bot...")
    await msg.send()
    msg.content = "Hi, Welcome to the Financial Analyzer Bot. Ask questions about amazon annual report"
    await msg.update()

    cl.user_session.set("chain", chain)

@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")
    if chain is None:
        return
    try:
        res = await chain.acall({'query': message.content})
        answer = res['result']
        await cl.Message(content=answer).send()
    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()
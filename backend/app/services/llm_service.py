import os
import logging
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class MeetingIntelligenceService:
    def __init__(self):
        """Initialize the LLM and Local Embedding models."""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            logger.warning("MISTRAL_API_KEY is missing from .env!")

        
        self.llm = ChatMistralAI(api_key=api_key, model="open-mistral-nemo")
        
        
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None

    def generate_insights(self, transcript: str) -> dict:
        """Extracts structured data from the raw transcript."""
        logger.info("Generating meeting insights via Mistral API...")
        
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert executive assistant. Analyze the following meeting transcript. "
                       "Return ONLY a structured response with the following headers: "
                       "TITLE, SUMMARY, ACTION_ITEMS, KEY_DECISIONS, OPEN_QUESTIONS. "
                       "Format the content under each header clearly using bullet points where appropriate."),
            ("user", "Transcript:\n\n{transcript}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"transcript": transcript})
        
        
        content = response.content
        
        
        return {
            "title": self._extract_section(content, "TITLE", "SUMMARY"),
            "summary": self._extract_section(content, "SUMMARY", "ACTION_ITEMS"),
            "action_items": self._extract_section(content, "ACTION_ITEMS", "KEY_DECISIONS"),
            "key_decisions": self._extract_section(content, "KEY_DECISIONS", "OPEN_QUESTIONS"),
            "open_questions": self._extract_section(content, "OPEN_QUESTIONS", "END")
        }

    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Helper function to slice the LLM response into our Pydantic fields."""
        try:
            start_idx = text.find(start_marker) + len(start_marker)
            end_idx = text.find(end_marker) if end_marker != "END" else len(text)
            if start_idx < len(start_marker): # Marker not found
                return "Information not explicitly stated in transcript."
            return text[start_idx:end_idx].strip().strip(":")
        except Exception:
            return "Could not parse this section."

    def initialize_rag_database(self, transcript: str):
        """Chunks the transcript and loads it into a local ChromaDB vector store."""
        logger.info("Initializing ChromaDB Vector Store for interactive Q&A...")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(transcript)
        
        
        self.vector_store = Chroma.from_texts(
            texts=chunks, 
            embedding=self.embeddings
        )
        logger.info(f"Successfully vectorized {len(chunks)} chunks.")

    def answer_question(self, question: str) -> str:
        """Retrieves context from ChromaDB and answers the user's question."""
        if not self.vector_store:
            return "Error: Document has not been analyzed yet. Please process a meeting first."
            
        logger.info(f"Querying RAG database for: {question}")
        docs = self.vector_store.similarity_search(question, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent AI Meeting Assistant. Your job is to answer questions based ONLY on the provided meeting transcript context.
            
            Context:
            {context}
            
            Instructions:
            - Answer the user's question accurately using the context above.
            - You are allowed to understand synonyms and rephrase the information to be helpful.
            - If the context does not contain relevant information to answer the question, respond exactly with: "I'm sorry, but that information was not discussed in this meeting."
            - Do not pull in outside knowledge to answer general questions."""),
            ("user", "{question}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": question})
        return response.content
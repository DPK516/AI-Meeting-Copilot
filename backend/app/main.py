import shutil
import uuid
from fastapi import File, UploadFile
import os
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware


from app.core.schemas import (
    MeetingAnalysisRequest,
    MeetingAnalysisResponse,
    ChatRequest,
    ChatResponse
)
from app.services.audio_service import AudioProcessingService
from app.services.llm_service import MeetingIntelligenceService


logger = logging.getLogger("backend_app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


app = FastAPI(
    title="AI Meeting Intelligence API",
    description="Production-ready asynchronous processing backend for meeting transcription and RAG analytics.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


audio_service = AudioProcessingService()
llm_service = MeetingIntelligenceService()

@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    """Simple service availability probe."""
    return {"status": "healthy", "engine": "local_whisper"}

@app.post(
    "/api/analyze", 
    response_model=MeetingAnalysisResponse, 
    status_code=status.HTTP_200_OK,
    tags=["Core Engine"]
)
async def analyze_meeting(payload: MeetingAnalysisRequest):
    """
    Accepts a media path or YouTube link, executes full local transcription, 
    extracts executive analytical assets, and populates the RAG database instance.
    """
    try:
        logger.info(f"Received analysis request for resource path: {payload.source}")
        
        
        transcript = audio_service.transcribe(payload.source)
        if not transcript.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The audio file could not produce any transcribable content."
            )
            
        
        insights = llm_service.generate_insights(transcript)
        
        
        llm_service.initialize_rag_database(transcript)
        
        logger.info("Successfully fully processed meeting asset pipelines.")
        return MeetingAnalysisResponse(**insights)

    except Exception as e:
        logger.error(f"Critical failure inside execution lifecycle: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline Processing Exception: {str(e)}"
        )

@app.post(
    "/api/analyze-upload", 
    response_model=MeetingAnalysisResponse, 
    status_code=status.HTTP_200_OK,
    tags=["Core Engine"]
)
async def analyze_uploaded_file(file: UploadFile = File(...)):
    """
    Accepts a direct multipart file upload from the browser, saves it temporarily 
    to the container's disk, processes it, and cleans up after itself.
    """
    try:
        logger.info(f"Receiving file upload: {file.filename}")
        
        
        file_extension = file.filename.split(".")[-1]
        temp_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        
        temp_file_path = os.path.join("downloads", temp_filename)
        
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"File saved to {temp_file_path}. Starting analysis pipeline...")

        
        transcript = audio_service.transcribe(temp_file_path)
        if not transcript.strip():
            raise HTTPException(status_code=422, detail="The audio file produced no text.")
            
        insights = llm_service.generate_insights(transcript)
        llm_service.initialize_rag_database(transcript)
        
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info("Temporary file deleted successfully.")
            
        return MeetingAnalysisResponse(**insights)

    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload Engine Error: {str(e)}"
        )

@app.post(
    "/api/chat", 
    response_model=ChatResponse, 
    status_code=status.HTTP_200_OK,
    tags=["Core Engine"]
)
async def chat_with_meeting(payload: ChatRequest):
    """
    Queries the current instantiated RAG memory store to return factual semantic context answers.
    """
    try:
        answer = llm_service.answer_question(payload.question)
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"RAG Retrieval cycle exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval Engine Error: {str(e)}"
        )
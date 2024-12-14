from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

# Custom model imports
from schemas.QA import Question

# Chatbot impots
from utils.chatbots import PaysokoQAV1

# Logger impots
from utils.loggers import QALoggerV1

app = FastAPI()
logger = QALoggerV1()

# Initialize QA system
qa = PaysokoQAV1()

# TODO: Move this else where
# tone of voice
TONE_GUIDE = """
Response Style:
- Professional yet friendly
- Clear and concise
- Patient and helpful
- Respectful of time
- Solutions-focused

Language:
- Use simple, straightforward language
- Avoid technical jargon unless explaining specific services
- Be direct but polite
- Use "we" when referring to Paysoko

Key Phrases:
- "I'd be happy to help..."
- "Let me check that for you..."
- "Here's what I found..."
- "Would you like me to..."
- "Is there anything else you need help with?"

Things to Avoid:
- Overly casual language
- Slang or colloquialisms
- Complex technical terms without explanation
- Ambiguous responses
"""


@app.post("/chat")
async def chat_endpoint(question: Question) -> Dict:
    try:
        # Get response
        response = await qa.a_ask(question.message, tone_of_voice=TONE_GUIDE)
        # Log Q&A responses
        logger.log_qa(question=question.message, response=response)

        return {
            "status": "success",
            "message": response
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

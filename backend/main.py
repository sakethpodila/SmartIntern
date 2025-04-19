from fastapi import FastAPI
from backend.routes import resume, chatbot, jobs
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SmartIntern API",
    version='1.0'
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(resume.router, prefix='/routes/resume', tags=['Resume'])
# app.include_router(chatbot.router, prefix='routes/chatbot')
app.include_router(jobs.router, prefix='/routes/jobs', tags=['Jobs'])

@app.get('/')
async def root():
    return {
        "status": 'online',
        'service': 'SmartIntern API', 
        'version': '1.0'
    }
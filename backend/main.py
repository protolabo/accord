from fastapi import FastAPI
from app.routes import auth, emails
from app.db.connection import init_db

app = FastAPI()

# Initialisation of database
@app.on_event("startup")
async def startup_db():
    await init_db()

# Register router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
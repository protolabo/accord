from fastapi import FastAPI
from app.routes import auth, emails
from app.db.connection import init_db
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from backend.app.email_providers.google.auth import router as auth_router
import sys
from backend.app.killer_process import kill_processes_on_port
import secrets
app = FastAPI()

SECRET_KEY = secrets.token_hex(16)

# Initialisation of database
@app.on_event("startup")
async def startup_db():
    await init_db()

# Register router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])
app.include_router(auth_router)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="accord_session",
    max_age=1800  # 30 minutes
)

if __name__ == "__main__":
    if kill_processes_on_port(8000):
        print("Port 8000 is now available...")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("Failed to free port 8000")
        sys.exit(1)
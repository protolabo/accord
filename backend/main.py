import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from backend.app.email_providers.google.auth import  router as auth_router
import sys
from backend.app.utils.killer_process import  kill_processes_on_port
import secrets

app = FastAPI()

SECRET_KEY = secrets.token_hex(16)

# Configuration du middleware de session
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="accord_session",
    max_age=1800
)

app.include_router(auth_router)

if __name__ == "__main__":
    if kill_processes_on_port(8000):
        print("Port 8000 is now available...")
        uvicorn.run(app, host="0.0.0.0", port=8000)

        ### README PROCESS ###

        ## etape 1 : generation du mockdata , en production cette phase sera supprime
            #mockdataGenerator.main()

        ## etape 2: authentification & export mails
        """
                Args: email, max_email=None,output_dir,batchsize
        """

            # pour tester : auth_export_gmail("johndoe@gmail.com",10,"./data",5000)
            # pour relier au bouton se connecter :  "/export/gmail" {...}
            # les messages sont sauvegardé dans app/data

    else:
        print("Failed to free port 8000")
        sys.exit(1)
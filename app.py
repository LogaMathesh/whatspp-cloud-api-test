from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

import json
import os

from config import VERIFY_TOKEN
from whatsapp import send_message

app = FastAPI()

templates = Jinja2Templates(directory="templates")


DATA_FILE = "received_messages.json"


if not os.path.exists(DATA_FILE):

    with open(DATA_FILE, "w") as f:
        json.dump([], f)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    with open(DATA_FILE) as f:
        messages = json.load(f)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "messages": messages[::-1],
        },
    )

#######################################################
# WEBHOOK VERIFICATION
#######################################################

@app.get("/webhook")
async def verify(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")

    token = params.get("hub.verify_token")

    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


#######################################################
# RECEIVE MESSAGES
#######################################################
@app.get("/webhook")
async def verify(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("VERIFY_TOKEN from env:", VERIFY_TOKEN)
    print("Received token:", token)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)
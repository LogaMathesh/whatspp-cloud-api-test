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

@app.post("/webhook")
async def webhook(request: Request):

    body = await request.json()

    print(body)

    try:

        message = body["entry"][0]["changes"][0]["value"]["messages"][0]

        phone = message["from"]

        text = message["text"]["body"]

        with open(DATA_FILE) as f:
            data = json.load(f)

        data.append(
            {
                "phone": phone,
                "message": text
            }
        )

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        send_message(
            phone,
            f"I received your message:\n\n{text}"
        )

    except Exception as e:

        print(e)

    return {"status": "ok"}
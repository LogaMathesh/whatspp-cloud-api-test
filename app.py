from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

import json
import os

from config import VERIFY_TOKEN
from whatsapp import send_message

app = FastAPI()

templates = Jinja2Templates(directory="templates")

DATA_FILE = "received_messages.json"

# Create file if it doesn't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


#######################################################
# HOME PAGE
#######################################################

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    with open(DATA_FILE, "r") as f:
        messages = json.load(f)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "messages": messages[::-1]
        }
    )


#######################################################
# WEBHOOK VERIFICATION (GET)
#######################################################

@app.get("/webhook")
async def verify(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("Verification Request Received")
    print("Mode:", mode)
    print("Token:", token)
    print("Expected:", VERIFY_TOKEN)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook Verified Successfully")
        return PlainTextResponse(challenge)

    print("Verification Failed")
    return PlainTextResponse("Verification failed", status_code=403)


#######################################################
# RECEIVE WHATSAPP MESSAGES (POST)
#######################################################

@app.post("/webhook")
async def receive_message(request: Request):

    body = await request.json()

    print("\n" + "=" * 60)
    print("WEBHOOK RECEIVED")
    print(json.dumps(body, indent=4))
    print("=" * 60)

    try:

        value = body["entry"][0]["changes"][0]["value"]

        # Ignore status updates
        if "messages" not in value:
            print("Status update received.")
            return {"status": "ignored"}

        message = value["messages"][0]

        sender = message["from"]

        if message["type"] == "text":
            text = message["text"]["body"]
        else:
            text = "[Non-text Message]"

        print(f"Sender : {sender}")
        print(f"Message: {text}")

        ###########################################
        # Save message
        ###########################################

        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        data.append({
            "from": sender,
            "message": text
        })

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        ###########################################
        # Send Reply
        ###########################################

        reply = f"You said: {text}"

        print("Sending reply...")

        send_message(
            phone_number=sender,
            message=reply
        )

        print("Reply sent successfully.")

    except Exception as e:

        print("\nERROR OCCURRED")
        print(e)

    return {"status": "ok"}
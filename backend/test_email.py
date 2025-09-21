import os
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),

    MAIL_SERVER=os.getenv("MAIL_SERVER"),
MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),  # convert to integer here
MAIL_TLS=os.getenv("MAIL_STARTTLS", "True") == "True",
MAIL_SSL=os.getenv("MAIL_SSL_TLS", "False") == "True",

    USE_CREDENTIALS=True,
)

async def test_mail():
    fm = FastMail(conf)
    message = MessageSchema(
        subject="Test Email",
        recipients=[os.getenv("MAIL_USERNAME")],  # send to your own email
        body="Hello! This is a test email from Foresight AI backend.",
        subtype="plain"
    )
    await fm.send_message(message)
    print("Email sent successfully!")

if __name__ == "__main__":
    asyncio.run(test_mail())

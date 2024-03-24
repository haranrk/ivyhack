from fastapi import FastAPI
import random
import time
from main import *
from fastapi.middleware.cors import CORSMiddleware
from typing import Union
import re

app = FastAPI()
# Add a list of allowed origins (i.e., the front-end URLs that you want to allow to make requests to your backend)
origins = [
    "http://localhost:3000",  # Add more origins as needed
]

# Add CORSMiddleware to the application instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/newsletters")
def get_newsletters():
    emails = get_emails()
    newsletters = set()
    for mail in emails:
        newsletters.add(mail["name"])
    return list(newsletters)


@app.get("/emails")
def get_all_emails():
    email_details = get_emails()
    return email_details

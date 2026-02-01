import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

load_dotenv()  

firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    cred_dict = json.loads(firebase_credentials)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'mltqa-9864c.firebasestorage.app' 
    })

bucket = storage.bucket()

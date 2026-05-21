import time
import boto3
from botocore.client import Config
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cliente S3
s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_BUCKET_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    config=Config(signature_version="s3v4"),
)

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return f.read()


# POST /api/s3 — equivalente a route.ts
@app.post("/api/s3")
async def upload_image(image: UploadFile = File(...)):
    try:
        timestamp = int(time.time() * 1000)
        key = f"{timestamp}-{image.filename}"
        content = await image.read()

        # Sube el archivo
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=image.content_type,
        )

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600,
        )

        return JSONResponse({
            "success": True,
            "message": "La imagen se subió correctamente!",
            "data": {"url": url},
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e), "data": None},
        )
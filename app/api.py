from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import mysql.connector
import sys
import subprocess
import os

app = FastAPI()

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sanjay@123",
    "database": "traffic_db"
}

@app.get("/detections")
def get_detections():
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT id, ts_utc, file_path, violation_type, fine FROM violations ORDER BY ts_utc DESC")
    detections = cur.fetchall()
    cur.close()
    con.close()
    return detections

@app.get("/image/{detection_id}")
def get_image(detection_id: int):
    con = mysql.connector.connect(**MYSQL_CONFIG)
    cur = con.cursor()
    cur.execute("SELECT file_path FROM violations WHERE id = %s", (detection_id,))
    result = cur.fetchone()
    cur.close()
    con.close()
    if result:
        return FileResponse(result[0])
    return {"error": "Image not found"}

@app.get("/predict")
def run_prediction():
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        result = subprocess.run(
            [sys.executable, os.path.join("app", "realtime.py")],
            cwd=os.getcwd(),
            env=env,
            capture_output=True, text=True, check=True
        )
        return JSONResponse(content={
            "message": "Prediction completed.",
            "stdout": result.stdout,
            "stderr": result.stderr
        })
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={
            "message": "Prediction failed.",
            "stdout": e.stdout,
            "stderr": e.stderr
        }, status_code=500)
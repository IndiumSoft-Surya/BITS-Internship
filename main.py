from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import os
import csv
from io import StringIO, BytesIO
import pandas as pd
from io import StringIO

from charts import chart_plot
from eda import eda
from llama3 import llama

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

eds = eda()
model = llama()
charts = chart_plot()

@app.get("/")
def root():
    return {"message": "FastAPI AI-EDA Plot Server is running."}

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), schema_file: UploadFile = File(...)):
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8")
        dialect = csv.Sniffer().sniff(decoded[:2048])
        delimiter = dialect.delimiter
        df = pd.read_csv(StringIO(decoded), delimiter=delimiter)
    except Exception as e:
        return JSONResponse(content={"error": f"CSV Error: {str(e)}"}, status_code=400)

    try:
        schema_contents = await schema_file.read()
        schema_decoded = schema_contents.decode("utf-8")
    except Exception as e:
        return JSONResponse(content={"error": f"Schema Error: {str(e)}"}, status_code=400)

    # Generate summary
    summary_str = eds.generate_summary(df).getvalue()

    # Try llama response
    try:
        response = model.gen_insights(summary_str, schema_decoded)
    except Exception:
        response = model.fallback_response()

    charts.gen_charts(response,df)
    summary = response.get("insights", "No summary provided.")

    # Return list of public URLs for plots
    host_url = os.getenv("PUBLIC_HOST_URL", "https://data-bot.up.railway.app")
    plot_urls = [
        f"{host_url}/static/plots/{f}" for f in os.listdir("static/plots") if f.endswith(".png")
    ]

    return JSONResponse(content={
        "EDA report": summary_str,
        "schema" : schema_decoded,
        "summary": summary,
        "plot_urls": plot_urls
    })

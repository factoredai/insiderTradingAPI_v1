from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
import pandas as pd
import os

from api.resources import generate_plot
from api.api_utils import (read_all_form_4, create_ticker2name,
                           create_combined_data,
                           calculate_aggregates_per_insider)

app = FastAPI()

# Setup the Api resource routing here
# Route the URL to the resource
data_filings_path = os.path.join("data", "filings")
data_extracted_filename = os.path.join("data", "data.csv")
if not(os.path.exists(data_extracted_filename)):
    data = read_all_form_4(data_filings_path)
    data.to_csv(data_extracted_filename, index=False, header=True)
else:
    data = pd.read_csv(data_extracted_filename, header=0)
ticker2name = create_ticker2name(data)
dict_frames = create_combined_data(data)


@app.get("/generate_plot/{item_id}")
async def plot(item_id):
    generate_plot(dict_frames, ticker2name, item_id)
    return FileResponse(os.getcwd() + '/insider_plot.png')


@app.get("/generate_insiders_info/{item_id}")
async def insiders(item_id):
    insiders = calculate_aggregates_per_insider(data, item_id)
    return Response(content=insiders, media_type="text/html")


@app.get("/raw_data/{item_id}")
async def raw_data(item_id):
    dict_frames[item_id].to_csv("raw_data.csv")
    return FileResponse(os.getcwd() + '/raw_data.csv')

import sys

from fastapi import FastAPI , Response
from fastapi.responses import FileResponse
import finviz
import pandas as pd
import numpy as np
import quandl
import yfinance as yf
import matplotlib.pyplot as plt
import os

from api.resources import generate_plot
from api.api_utils import read_all_form_4, create_ticker2name, create_combined_data, calculate_aggregates_per_insider

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
quandl.ApiConfig.api_key = "txYdeX4SX2NxGzzJYsLT"

app = FastAPI()



# Setup the Api resource routing here
# Route the URL to the resource
data_filings_path = os.path.join("data", "filings")
data = read_all_form_4(data_filings_path)
ticker2name = create_ticker2name(data)
dict_frames = create_combined_data(data)

@app.get("/generate_plot/{item_id}")
async def plot(item_id):
    generate_plot(dict_frames, ticker2name, item_id)
    return FileResponse(os.getcwd() + '/insider_plot.png')

@app.get("/generate_insiders_info/{item_id}")
async def insiders(item_id):
        insiders = calculate_aggregates_per_insider(data, item_id)
        return Response(content=insiders.to_html(), media_type="text/html")

@app.get("/raw_data/{item_id}")
async def raw_data(item_id):
    return Response(content=dict_frames[item_id].to_html(), media_type="text/html")

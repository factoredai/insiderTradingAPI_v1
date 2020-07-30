from fastapi import FastAPI, Response, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import quandl
import os

from web.resources import generate_plot
from web.api_utils import (read_all_form_4, create_ticker2name,
                           create_combined_data, calculate_aggregates_per_insider)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
quandl.ApiConfig.api_key = "txYdeX4SX2NxGzzJYsLT"

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
dict_ticker = {"[FB]": "FB", 
               'BRK.A': "BRK-B", 
               "BRKA": "BRK-B"}
data['ticker'] = data['ticker'].map(dict_ticker).fillna(data['ticker'])
data = data.dropna(subset=["transactiondate"])
ticker2name = create_ticker2name(data)
dict_frames = create_combined_data(data)


@app.get("/generate_plot/{stock_id}")
async def plot(stock_id):
    generate_plot(dict_frames, ticker2name, stock_id)
    return FileResponse('insider_plot.png')


@app.get("/generate_insiders_info/{stock_id}")
async def insiders(stock_id):
    insiders = calculate_aggregates_per_insider(data, stock_id)
    return Response(content=insiders.to_html(table_id="execs_table"), media_type="text/html")


@app.get("/raw_data/{stock_id}")
async def raw_data(stock_id):
    dict_frames[stock_id].to_csv("raw_data.csv")
    return FileResponse('raw_data.csv')

# Web GUI setup and endpoint
templates = Jinja2Templates(directory="web/templates/")
# mount an independent app for static files at /gui/static
app.mount("/assets", StaticFiles(directory="web/assets"), name="assets")
app.mount("/demo", StaticFiles(directory="web/demo"), name="demo")
app.mount("/docs", StaticFiles(directory="web/docs"), name="docs")


@app.get("/")
def home(request: Request):  # id: str = Form(), requested_sum: str = Form()):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard")
def home(request: Request, stock_id: str):  # id: str = Form(), requested_sum: str = Form()):
    execs_table = calculate_aggregates_per_insider(data, stock_id)
    if len(execs_table) == 0:
        return templates.TemplateResponse("404.html", {"request": request})
    execs_table = execs_table.to_html(
        table_id="execs_table",
        index_names=False,
        index=False,
        na_rep="-",
        justify="center",
        border=0
    )
    return templates.TemplateResponse("dashboard.html",
                                      {
                                          "request": request,
                                          "stock_id": stock_id,
                                          "stock_name": ticker2name[stock_id],
                                          "execs_table": execs_table
                                      })

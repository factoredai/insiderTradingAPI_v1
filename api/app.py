import sys

from flask import Flask
from flask_restful import abort, Api
import finviz
import pandas as pd
import numpy as np
import quandl
import yfinance as yf
import matplotlib.pyplot as plt
import os

from resources import PlotGenerator
from api_utils import read_all_form_4, create_ticker2name, create_combined_data

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
quandl.ApiConfig.api_key = "txYdeX4SX2NxGzzJYsLT"

app = Flask(__name__)
api = Api(app)

# Setup the Api resource routing here
# Route the URL to the resource
data_filings_path = os.path.join(os.getcwd(), "data", "filings")
data = read_all_form_4(data_filings_path)
ticker2name = create_ticker2name(data)
dict_frames = create_combined_data(data)

api.add_resource(PlotGenerator, '/generate_plot', resource_class_kwargs={'dict_frames':dict_frames, 
                                                                    'ticker_name':ticker2name})


if __name__ == '__main__':
    app.run(debug=True)
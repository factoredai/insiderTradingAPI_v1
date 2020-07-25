from flask_restful import reqparse, Resource
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
from flask import send_file
import sys

#from evaluate import Eval
from api_utils import visualization_insider_stock

parser = reqparse.RequestParser()
parser.add_argument('query')

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

class PlotGenerator(Resource):
    def __init__(self, dict_frames={}, ticker_name=None):
        super(PlotGenerator, self).__init__()
        self.dict_frames = dict_frames
        self.ticker_name = ticker_name

    def get(self):
        # use parser and find the user's query
        parser = reqparse.RequestParser()
        parser.add_argument('ticker', type=str, required=True, help='Company ticker')
        args = parser.parse_args()
        ticker = args['ticker']
        val = self.dict_frames[ticker]
        visualization_insider_stock(ticker, val, self.ticker_name, save_path="insider_plot.png", from_api=True)     
        return send_file(os.getcwd() + '/insider_plot.png', as_attachment=True)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
import sys

#from evaluate import Eval
from web.api_utils import visualization_insider_stock

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

def generate_plot(dict_frames, ticker_name, ticker):
    # use parser and find the user's query
    val = dict_frames[ticker]
    visualization_insider_stock(ticker, val, ticker_name,
                                save_path="insider_plot.png", from_api=True)

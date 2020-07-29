from datetime import datetime
from secedgar.filings import Filing, FilingType
import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

from api_utils import (create_dir, make_patch_spines_invisible, create_ticker2name,
                       create_combined_data, download_filing_4,
                       InsiderAggregators, calculate_aggregates_per_insider,
                       read_all_form_4,
                       visualization_insider_stock)


if __name__ == "__main__":
    tot_companies = 30 # None = All sp100
    data_path = os.path.join(os.getcwd(), "data")
    data_filings_path = os.path.join(data_path, "filings")
    sp_100_file = os.path.join(data_path, "top40_sp500.csv")

    create_dir(data_filings_path)

    sp100_companies = pd.read_csv(sp_100_file)[:-1]
    sp100_symbols = sp100_companies["Symbol"].unique()

    for symbol in sp100_symbols[:tot_companies]:
        print("symbol: ",symbol)
        download_filing_4(symbol, data_filings_path,
                        start_date=datetime(2019, 7, 21),
                        end_date=datetime(2020, 7, 20))
    print("Downloaded")



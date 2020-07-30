from datetime import datetime
import os
import pandas as pd

from api_utils import (create_dir, download_filing_4)


if __name__ == "__main__":
    tot_companies = 30  # None = All sp100
    data_path = os.path.join(os.getcwd(), "data")
    data_filings_path = os.path.join(data_path, "filings")
    sp_100_file = os.path.join(data_path, "top40_sp500.csv")

    create_dir(data_filings_path)

    sp100_companies = pd.read_csv(sp_100_file)[:-1]
    sp100_symbols = sp100_companies["Symbol"].unique()

    for symbol in sp100_symbols[:tot_companies]:
        print("symbol: ", symbol)
        download_filing_4(symbol, data_filings_path,
                          start_date=datetime(2019, 7, 21),
                          end_date=datetime(2020, 7, 20))
    print("Downloaded")

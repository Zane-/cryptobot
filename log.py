import csv
from collections import deque
from datetime import datetime


# Returns the portfolio percent change from the last transaction using the transactions csv.
def get_portfolio_change(data):
    last_portfolio = float(get_last_row('transactions.csv')[9])
    return round(get_portfolio(data) / last_portfolio, 4)


# Returns the last row of the filename
def get_last_row(filename):
    with open(filename) as f:
        return deque(csv.reader(f), 1)[0]


# TODO:
# * dropbox integration here w/ csv

# write data to CSV
# row = (
#     str(datetime.now()),
#     lowest,
#     data[lowest]['change'],
#     second_lowest,
#     data[second_lowest]['change'],
#     second_highest,
#     data[second_highest]['change'],
#     highest,
#     data[highest]['change'],
#     round(get_portfolio(data), 2),
#     get_portfolio_change(data)
# )

# with open('transactions.csv', 'a') as f:
#     writer = csv.writer(f, lineterminator='\n')
#     writer.writerow(row)
def main():
    low_high_pair_strat(2)




if __name__ == '__main__':
    main()
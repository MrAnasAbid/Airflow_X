import os
import requests
import pandasql as ps
import sqlite3
from pandas import DataFrame, read_sql_query, concat
from dotenv import load_dotenv
from constants import BASE_CURRENCY

# Load environment variables from a .env file
load_dotenv()
api_key = os.getenv('EXCHANGE_RATE_API_KEY')

# Request the latest exchange rates
url_currency_rates = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{BASE_CURRENCY}"
req_currency = requests.get(url_currency_rates)
data = req_currency.json()
conversion_rates = DataFrame(data['conversion_rates'].items(), columns=['currency_code', 'rate'])
highest_rates = conversion_rates.sort_values(by="rate", ascending=False).reset_index(drop=True)
highest_rates["date"] = data["time_last_update_utc"].split(" 00:")[0]

# Extract conversion rates and create DataFrame
url_currency_codes = f'https://v6.exchangerate-api.com/v6/{api_key}/codes'
req_codes = requests.get(url_currency_codes)
data_code = req_codes.json()
codes = DataFrame(data_code["supported_codes"], columns=["currency_code", "currency_name"])

# Merge the two DataFrames
query = """
SELECT currency_code, rate, currency_name, date
FROM highest_rates NATURAL JOIN codes
"""
result = ps.sqldf(query, locals())


# Replace the old data with the new data, this is highly inefficient
conn = sqlite3.connect('currency_rates.db')
c = conn.cursor()
result.to_sql('currency', conn, if_exists='replace', index=False)

query = """
SELECT *
FROM currency
"""
old_data = read_sql_query(query, conn)
new_data = concat([old_data, result], ignore_index=True)

new_data.to_sql('currency', conn, if_exists='replace', index=False)
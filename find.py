import requests
import json
import datetime
import time
import yaml
import numpy as np
from datetime import timedelta
import pandas as pd
from symbols import all_symbol

with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

def get_access_token():
    """토큰 발급"""
    
    
    '''headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    print(ACCESS_TOKEN)'''
    
    
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjA4M2VlNjM1LTg4ODYtNDk4YS04NzVlLWFjYjA3OWRkZTYyZiIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTcxNDA0MjIzOSwiaWF0IjoxNzEzOTU1ODM5LCJqdGkiOiJQU0htZE5FZTBKZ1k5bjNMNDlKVW40cTREUTVWSGg1MFFjOE0ifQ.qgHKNSH5bA5p_8bHr-i891sSIEALjvvqdy2TgRp6NCr8-Dcp2UORsEEBZnfCXI9SxviGJH1mHzMa-wVx699UWw"
    #return ACCESS_TOKEN
    
def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey

def minus_business_days(start_date, business_days_to_add, holidays=[]):
    current_date = start_date
    while business_days_to_add > 0:
        current_date -= datetime.timedelta(days=1)
        if current_date.weekday() < 5 and current_date not in holidays:  # 월요일=0, 일요일=6
            business_days_to_add -= 1
    return current_date

holidays = [datetime.date(2023, 12, 25), datetime.date(2024, 1, 1), datetime.date(2024, 2, 9), datetime.date(2024, 2, 12), datetime.date(2024, 3, 1)]

def get_holcv(code='005930', count='7'):
    """holcv 조회"""
    time_now = datetime.datetime.now()
    time_past = time_now - timedelta(days=count)
    str_today = time_now.strftime('%Y%m%d')
    str_past = time_past.strftime('%Y%m%d')
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST03010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "FID_INPUT_DATE_1":str_past,
    "FID_INPUT_DATE_2":str_today,
    "FID_PERIOD_DIV_CODE":"D",
    "FID_ORG_ADJ_PRC":"0"
    }
    res = requests.get(URL, headers=headers, params=params)
    if res.json()['rt_cd'] == '0':
        
        columns = ['open', 'high', 'low', 'close', 'volume']
        index = []
        rows = []
        if res.json()['output2'][0] == {} or res.json()['output2'][0]['stck_bsop_date'] <= str_past:
            return -1
        data_length = min(len(res.json()['output2']), count)
        for i in range(data_length):
            index.insert(0,res.json()['output2'][i]['stck_bsop_date'])
            rows.insert(0,[int(res.json()['output2'][i]['stck_oprc']),int(res.json()['output2'][i]['stck_hgpr']),int(res.json()['output2'][i]['stck_lwpr']),int(res.json()['output2'][i]['stck_clpr']),int(res.json()['output2'][i]['acml_vol'])])
        df = pd.DataFrame(rows, columns=columns, index=index) 
        return df
    else:
        return -1
    
def get_holcv_volume(code='005930', count='7'):
    """holcv 조회"""
    time_now = datetime.datetime.now()
    time_past = time_now - timedelta(days=count)
    str_today = time_now.strftime('%Y%m%d')
    str_past = time_past.strftime('%Y%m%d')
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST03010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "FID_INPUT_DATE_1":str_past,
    "FID_INPUT_DATE_2":str_today,
    "FID_PERIOD_DIV_CODE":"D",
    "FID_ORG_ADJ_PRC":"0"
    }
    res = requests.get(URL, headers=headers, params=params)
    columns = ['open', 'high', 'low', 'close', 'volume']
    index = []
    rows = []
    data_length = min(len(res.json()['output2']), count)
    for i in range(data_length):
        index.insert(0,res.json()['output2'][i]['stck_bsop_date'])
        rows.insert(0,[int(res.json()['output2'][i]['stck_oprc']),int(res.json()['output2'][i]['stck_hgpr']),int(res.json()['output2'][i]['stck_lwpr']),int(res.json()['output2'][i]['stck_clpr']),int(res.json()['output2'][i]['acml_vol'])])
    df = pd.DataFrame(rows, columns=columns, index=index) 
    return df

def get_ror(code = '035420', count = 7, k=0.5):
    df = get_holcv_volume(code, count)
    df['range'] = (df['high'] - df['low']) * k

    df['target'] = df['open'] + df['range'].shift(1)

    df['close'] = pd.to_numeric(df['close'])
    df['5dayline'] = df['close'].rolling(window=5).mean()
    df['10dayline'] = df['close'].rolling(window=10).mean()

    fee = 0.004971487
    df['ror'] = np.where((df['high'] > df['target']) & (df['high'] > df["5dayline"]) & (df['high'] > df["10dayline"]), df['close'] / df["target"] - fee, 1)

    ror = df['ror'].cumprod().iloc[-2]
    return ror

def get_name(code='005930'):
    """주식 이름 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"CTPF1604R",
        "custtype":'P'}
    params = {
    "PDNO":code,
    "PRDT_TYPE_CD":300
    }
    res = requests.get(URL, headers=headers, params=params)
    name = res.json()['output']['prdt_abrv_name']
    return name

columns = ['종목코드', '수익률']
found_name = []
found_list = []
found_volume = []
found_hpr_100 = []
found_hpr_30 = []

def find_volume(all_symbol):
    for sym in all_symbol:
        ror_100 = get_ror(sym, 100)
        ror_30 = get_ror(sym,30)
        df = get_holcv_volume(sym,1)
        name = get_name(sym)
        if df['volume'].iloc[0] > 100000 and ror_100 > 1.1 and ror_30 > 1.1:
            found_name.append(name)
            found_list.append(sym)
            found_hpr_100.append(ror_100)
            found_hpr_30.append(ror_30)
            found_volume.append(df['volume'].iloc[0])
    df = pd.DataFrame({
    '종목이름': found_name,
    '종목코드': found_list,
    '거래량': found_volume,
    '100일수익률': found_hpr_100,
    '30일수익률':found_hpr_30
    })
    df.to_excel(f"거래량이상종목.xlsx", index=False)

def read_symbol(file_path):
    df = pd.read_excel(file_path)
    column_values = df.iloc[:, 1].tolist()
    formatted_data = [str(num).zfill(6) for num in column_values]
    return formatted_data

def able_code(symbol):
    true_code = []
    for sym in symbol:
        
        df=get_holcv(sym, 5)
        if isinstance(df, int) and df == -1:
            print(f"{sym} 제외")
            continue
        true_code.append(sym)
    return true_code

try:
    ACCESS_TOKEN = get_access_token()
    print('1')
    able_symbol = able_code(all_symbol)
    print('2')
    find_volume(able_symbol)

except Exception as e:
    print(f"{e}")
    time.sleep(1)
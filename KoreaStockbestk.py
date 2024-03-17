import requests
import json
import datetime
import time
import yaml
from datetime import timedelta
import pandas as pd
import numpy as np

dont_sell = ["005930","035420"]

with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_access_token():
    """토큰 발급"""
    '''
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    print(ACCESS_TOKEN)
    '''
    return 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjVhYWU4Y2RhLWI3NGMtNDljYi05MmMzLTVkNTdiMDA2MDg1NyIsImlzcyI6InVub2d3IiwiZXhwIjoxNzEwNjc2ODQ5LCJpYXQiOjE3MTA1OTA0NDksImp0aSI6IlBTSG1kTkVlMEpnWTluM0w0OUpVbjRxNERRNVZIaDUwUWM4TSJ9.1LBB3XXkulR92DnqgLS220R3pIncHBYfVJDcf7LbUMSHwnsykHqP6AeEBfU6gYQ1DrfncnMnXBEjwskDzi7wMg'
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




def get_holcv(code='005930', count='7'):
    """holcv 조회"""
    time_now = datetime.datetime.now()
    time_past = minus_business_days(time_now, 30, holidays)
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
    

def get_target_price(code="005930"):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010400"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "fid_org_adj_prc":"1",
    "fid_period_div_code":"D"
    }

    res = requests.get(URL, headers=headers, params=params)

    stck_oprc = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    stck_hgpr = int(res.json()['output'][1]['stck_hgpr']) #전일 고가
    stck_lwpr = int(res.json()['output'][1]['stck_lwpr']) #전일 저가
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * 0.5
    return target_price

def get_ror(k=0.5, code = '035420', count = 7):
    df = get_holcv(code, count)
    df['range'] = (df['high'] - df['low']) * k

    df['target'] = df['open'] + df['range'].shift(1)

    df['close'] = pd.to_numeric(df['close'])
    df['5dayline'] = df['close'].rolling(window=5).mean()
    df['10dayline'] = df['close'].rolling(window=10).mean()

    fee = 0.004971487
    df['ror'] = np.where((df['high'] > df['target']) & (df['high'] > df["5dayline"]) & (df['high'] > df["10dayline"]), df['close'] / df["target"] - fee, 1)

    ror = df['ror'].cumprod().iloc[-2]
    return ror

holidays = [datetime.date(2023, 12, 25), datetime.date(2024, 1, 1), datetime.date(2024, 2, 9), datetime.date(2024, 2, 12), datetime.date(2024, 3, 1)]

def minus_business_days(start_date, business_days_to_add, holidays=[]):
    current_date = start_date
    while business_days_to_add > 0:
        current_date -= datetime.timedelta(days=1)
        if current_date.weekday() < 5 and current_date not in holidays:  # 월요일=0, 일요일=6
            business_days_to_add -= 1
    return current_date

ACCESS_TOKEN = get_access_token()
for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k, '035420', 30)
    print("%.1f %f" % (k, ror))
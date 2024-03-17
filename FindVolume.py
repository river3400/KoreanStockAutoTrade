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
    
    return 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjJlM2Y5OTE4LTZiOGQtNDg1NS04N2VjLWUyYzJiMWE5MDdiZiIsImlzcyI6InVub2d3IiwiZXhwIjoxNzEwNzY3NjIxLCJpYXQiOjE3MTA2ODEyMjEsImp0aSI6IlBTSG1kTkVlMEpnWTluM0w0OUpVbjRxNERRNVZIaDUwUWM4TSJ9.9w_vr9FiQFO5XYzZZ70F_HNj7kAtTDlvUQwRvFvTQ0QEu8tXJiirFXqNQQ7RKjrayuDSOreNgCfZTxzkJDXjxg'
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

holidays = [datetime.date(2023, 12, 25), datetime.date(2024, 1, 1), datetime.date(2024, 2, 9), datetime.date(2024, 2, 12), datetime.date(2024, 3, 1)]

def minus_business_days(start_date, business_days_to_add, holidays=[]):
    current_date = start_date
    while business_days_to_add > 0:
        current_date -= datetime.timedelta(days=1)
        if current_date.weekday() < 5 and current_date not in holidays:  # 월요일=0, 일요일=6
            business_days_to_add -= 1
    return current_date


def get_holcv(code='005930', count='7'):
    """holcv 조회"""
    time_now = datetime.datetime.now()
    time_past = minus_business_days(time_now - timedelta(days=count), 9, holidays)
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
    data_length = min(len(res.json()['output2']), count+9)
    for i in range(data_length):
        index.insert(0,res.json()['output2'][i]['stck_bsop_date'])
        rows.insert(0,[int(res.json()['output2'][i]['stck_oprc']),int(res.json()['output2'][i]['stck_hgpr']),int(res.json()['output2'][i]['stck_lwpr']),int(res.json()['output2'][i]['stck_clpr']),int(res.json()['output2'][i]['acml_vol'])])
    df = pd.DataFrame(rows, columns=columns, index=index) 
    return df


    
def get_ror(code = '035420', count = 7, k=0.5):
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


columns = ['종목코드', '수익률']
symbol_list = ['115390', '286750', '340360', '065650', '177350', '090150', '007820', '092870', '094970','270520', '246710', '043220', '270210', '136660', '212310', '003580', '001210', '003160', '067630', '104200', '059210', '222080', '101390', '321820', '064800', '073640', '192410', '208890', '121060', '014820', '013310', '270660', '214370', '092590', '116100', '083450', '114190', '035290', '317330', '019570', '235980', '053030', '027040', '033170', '298060', '109610', '036810', '348370', '198080', '083310', '309930', '018000', '033100', '307930', '044490', '041590', '114810', '236030', '311960', '208850', '254160', '308700', '042660', '009470', '212560', '025950', '083500', '240810', '138360', '223220', '238170', '224760', '093510', '341310', '145720', '000150', '452260', '396270', '160980', '196170', '014940', '131290', '062970', '161580', '322190', '185190', '224810', '066830', '077500', '025620', '151910', '255220', '330860', '060900', '900340', '234920', '080530', '199800', '256840', '178600', '388610', '402420', '202960', '006400', '005110', '121600', '261200', '383930', '200350', '058470', '006920', '072950', '068760', '056700', '302430', '033540', '032800', '241820', '042520', '390110', '169670']

found_name = []
found_list = []
found_volume = []
found_hpr_100 = []
found_hpr_30 = []
time_now = datetime.datetime.now()
# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()

    send_message("===종목 찾기 프로그램을 시작합니다===")
    for sym in symbol_list:
        ror_100 = get_ror(sym, 100)
        ror_30 = get_ror(sym,30)
        df = get_holcv(sym,1)
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


    
    df.to_excel(f"{time_now.strftime('%Y%m%d')}거래량이상종목.xlsx", index=False)

except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)
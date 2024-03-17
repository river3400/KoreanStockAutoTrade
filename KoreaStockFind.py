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
symbol_list = ['294870', '010060', '001740', '017900', '001140', '115390', '286940', '004990', '001470', '214420', '028300', '286750', '340360', '078140', '060240', '065650', '177350', '337930', '060230', '328380', '115530', '099190', '090150', '174900', '073570', '102120', '007820', '187660', '230980', '101360', '092870', '317870', '047560', '066980', '123570', '254120', '094970', '080220', '270520', '950160', '065130', '105550', '246710', '043220', '078350', '076340', '270210', '276240', '250030', '136660', '212310', '007700', '003580', '105560', '001210', '117580', '018500', '003160', '003960', '004360', '007810', '084870', '010100', '013720', '067630', '104200', '317240', '098460', '088130', '066670', '377030', '054180', '059210', '142760', '042940', '043100', '139050', '162300', '099320', '222080', '013990', '101390', '078860', '262840', '237690', '064090', '227950', '082210', '321820', '030530', '417840', '064800', '191420', '073640', '087600', '136480', '054040', '192410', '114920', '208890', '044990', '121060', '086460', '001380', '014820', '011930', '139480', '194370', '071320', '005440', '378850', '900280', '025900', '281740', '018310', '171090', '043260', '031310', '013310', '270660', '069410', '376190', '061970', '101730', '289220', '036890', '016790', '263700', '214370', '323280', '124560', '260870', '317860', '092590', '086220', '116100', '017940', '011200', '009140', '009190', '001440', '007860', '068270', '006220', '091810', '168490', '042670', '083450', '079940', '114190', '035290', '094860', '253590', '085670', '008830', '317330', '219550', '039980', '019570', '235980', '053030', '301300', '419120', '027040', '276040', '033170', '298060', '080000', '109610', '088800', '036810', '043090', '348370', '198080', '083310', '353590', '309930', '332570', '313760', '018000', '072520', '033100', '307930', '220260', '043590', '044490', '089030', '117730', '064760', '087010', '041590', '080720', '114810', '054920', '210120', '217320', '236030', '251280', '311960', '208850', '254160', '308700', '327610', '000270', '042660', '002410', '032830', '009470', '010600', '103590', '281820', '011280', '900290', '297890', '047920', '115450', '212560', '025950', '263720', '300120', '064550', '314930', '148780', '065350', '136410', '052770', '096610', '052020', '083500', '240810', '175140', '417500', '436530', '115180', '389140', '041020', '043370', '138360', '064240', '278990', '199150', '223220', '236340', '191600', '238170', '224760', '093510', '341310', '189350', '027410', '000680', '036530', '002880', '145720', '000150', '009310', '180640', '452260', '010660', '245620', '095340', '033640', '396270', '278650', '005160', '094170', '110990', '069540', '412350', '160980', '196170', '060540', '096630', '054630', '014940', '080580', '032500', '256940', '131290', '405000', '062970', '161580', '347770', '220180', '112190', '179720', '322190', '258250', '185190', '447690', '224810', '234070', '066830', '413300', '266870', '089470', '082740', '077500', '025620', '009540', '011500', '267260', '151910', '255220', '330860', '060900', '038290', '086820', '263810', '003100', '032680', '074430', '143160', '148250', '092600', '101490', '200470', '031860', '352910', '900340', '036200', '083470', '234920', '119860', '080530', '365270', '219130', '199800', '441270', '053160', '003380', '256840', '030520', '178600', '403360', '253610', '322970', '388610', '233990', '402420', '202960', '001250', '229640', '000500', '084690', '000400', '023530', '006400', '010140', '010780', '008730', '000650', '118000', '036460', '004090', '005110', '010690', '211270', '036540', '089230', '121600', '234690', '261200', '383930', '347700', '200350', '058470', '305090', '006920', '018290', '072950', '294630', '068760', '304100', '084180', '056700', '257720', '175250', '307280', '014190', '302430', '276730', '228760', '053050', '402030', '083790', '091440', '425420', '033540', '032800', '300080', '241820', '126700', '042520', '390110', '207490', '122830', '140660', '299480', '169670']
found_name = []
found_list = []
found_hpr_100 = []
found_hpr_30 = []
found_and = []
time_now = datetime.datetime.now()
# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()

    send_message("===종목 찾기 프로그램을 시작합니다===")
    for sym in symbol_list:
        ror_100 = get_ror(sym, 100)
        ror_30 = get_ror(sym,30)
        name = get_name(sym)
        if ror_100 > 1.1 and ror_30 > 1.1:
            found_name.append(name)
            found_list.append(sym)
            found_hpr_100.append(ror_100)
            found_hpr_30.append(ror_30)
            found_and.append(np.where((ror_100 > 1.1) & (ror_30 > 101), 1, 0))
    df = pd.DataFrame({
    '종목이름': found_name,
    '종목코드': found_list,
    '100일수익률': found_hpr_100,
    '30일수익률':found_hpr_30,
    '수익률비교':found_and
    })

        
    
    df.to_excel(f"{time_now.strftime('%Y%m%d')}종목추천(30,100 and).xlsx", index=False)

except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)
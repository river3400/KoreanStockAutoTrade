import requests
import json
import datetime
import time
import yaml
import concurrent.futures
import os
import sys
import numpy as np
from datetime import timedelta
import pandas as pd
from symbols import all_symbol
from symbols import holidays

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
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    print(ACCESS_TOKEN)

    return ACCESS_TOKEN
    
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

def get_current_price(code="005930"):
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

def get_price_lst(code="005930", k=0.5):
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
    hgpr_list = [item['stck_hgpr'] for item in res.json()['output']]
    last_date = res.json()['output'][0]['stck_bsop_date']
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * k
    return [target_price, hgpr_list, last_date]

def get_movingaverage(price_lst = ['0',['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0'], '20000001'], day='1'):
    """이동평균선 가격 조회"""
    time_now = datetime.datetime.now()
    str_today = time_now.strftime('%Y%m%d')
    if price_lst[2] == str_today:
        price_lst[1].pop(0)
    movingaverage = price_lst[1][0:day]
    average = [int(num) for num in movingaverage]
    return sum(average)/len(average)

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = [stock['hldg_qty'], stock['evlu_pfls_rt'], stock['prdt_name']]
    return stock_dict

def get_stock_balance_msg():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = [stock['hldg_qty'], stock['evlu_pfls_rt'], stock['prdt_name']]
            send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    send_message(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)

def buy(code="005930", qty="1", unpr = '0'):
    """주식 시장가 매수"""  
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": unpr
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0802U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매수 성공]{str(res.json())}")
        return res.json()['output']['ODNO']
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return True

def sell(code="005930", qty="1"):
    """주식 시장가 매도"""
    if code in dont_sell:
        return 0
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0801U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매도 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False
    
def cancel(code="0000001727"):
    """주문취소주문"""
    PATH = "uapi/domestic-stock/v1/trading/order-rvsecncl"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "KRX_FWDG_ORD_ORGNO": "",
        "ORGN_ODNO": code,
        "ORD_DVSN": "00",
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": "0",
        "ORD_UNPR": "0",
        "QTY_ALL_ORD_YN": "Y"
    }
    headers = {"Content-Type":"application/json",
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0803U",
        "custtype":"P",
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[취소 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[취소 실패]{str(res.json())}")
        return False
    
def check_buy_condition(sym, buy_amount, bought_list, buytry_list):
    '''목표가 달성여부 계산'''
    global soldout
    current_price = get_current_price(sym)
    price_lst = get_price_lst(sym, k)
    target_price = price_lst[0]
    ma5_price = float(get_movingaverage(price_lst,5))
    ma10_price = float(get_movingaverage(price_lst,10))
    if target_price*0.997 < current_price and ma5_price < current_price and ma10_price < current_price:
        buy_qty = 0  # 매수할 수량 초기화
        buy_qty = int(buy_amount // target_price)
        if buy_qty > 0:
            send_message(f"{sym} 목표가 근접(현{current_price} 목표{target_price} 5일{ma5_price} 10일{ma10_price}) 매수를 시도합니다.")
            if current_price < 2000:
                buy_price = int(target_price)
            elif current_price < 5000:
                buy_price = int(target_price//5+1)*5
            elif current_price < 20000:
                buy_price = int(target_price//10+1)*10
            elif current_price < 50000:
                buy_price = int(target_price//50+1)*50
            else:
                buy_price = int(target_price//100+1)*100
            result = buy(sym, buy_qty, str(buy_price))
            if result:
                soldout = False
                bought_list.append(sym)
                buytry_list.append(sym)
                t_buy = datetime.datetime.now()
                order_log[sym] = [t_buy + datetime.timedelta(minutes=10), result, sym]

def parallel_check_buy_conditions(symbol_list, buy_amount, bought_list, buytry_list):
    '''병렬처리'''
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for sym in symbol_list:
            if len(bought_list) < target_buy_count and sym not in bought_list and sym not in buytry_list:
                futures.append(executor.submit(check_buy_condition, sym, buy_amount, bought_list, buytry_list))
        concurrent.futures.wait(futures)

def restart_program():
    python = sys.executable
    print(python)
    print(*sys.argv)
    os.execl(python, python, *sys.argv)


def minus_business_days(start_date, business_days_to_add, holidays=[]):
    current_date = start_date
    while business_days_to_add > 0:
        current_date -= datetime.timedelta(days=1)
        if current_date.weekday() < 5 and current_date not in holidays:  # 월요일=0, 일요일=6
            business_days_to_add -= 1
    return current_date

def last_sales_days(holidays=holidays):
    t_now = datetime.datetime.now()
    today = t_now.weekday()
    while(today == 5 or today == 6 or t_now.date() in holidays):
        today -= 1
        t_now -= datetime.timedelta(days=1)
    return t_now.strftime('%Y%m%d')
        

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
        if res.json()['output2'][0] == {} or res.json()['output2'][0]['stck_bsop_date'] < last_sales_days():
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
    send_message("엑셀파일 생성완료")

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
            continue
        true_code.append(sym)
    return true_code
    

# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()

    file_path = '거래량이상종목.xlsx'

    symbol_list = read_symbol(file_path)

    bought_list = [] # 매수 완료된 종목 리스트
    buytry_list = []
    order_log = {}
    total_cash = get_balance() # 보유 현금 조회
    stock_dict = get_stock_balance_msg() # 보유 주식 조회
    for sym in stock_dict.keys():
        bought_list.append(sym)
    target_buy_count = 10 # 매수할 종목 수
    buy_percent = 0.1 # 종목당 매수 금액 비율
    buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산
    soldout = False
    last_executed = None
    new_list = True

    send_message("===국내 주식 자동매매 프로그램을 시작합니다===")
    while True:
        k=0.5
        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=10, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=30, second=0,microsecond=0)
        t_restart = t_now.replace(hour=8, minute=0, second=0, microsecond=0)
        t_reset = t_now.replace(hour=8, minute=10, second=0, microsecond=0)
        today = t_now.weekday()
        to_delete = []
        if today == 5 or today == 6 or t_now.date() in holidays:  # 주말이 되면 종목찾기
            if new_list:
                able_symbol = able_code(all_symbol)
                print(able_symbol)
                find_volume(able_symbol)
                new_list = False
            time.sleep(3600)
            continue

        if t_restart < t_now < t_reset:  #평일 8시 프로그램 재시작
            send_message("프로그램을 재시작합니다.")
            time.sleep(600)
            restart_program()
        

        
        if t_9 < t_now < t_start and soldout == False: # 잔여 수량 매도
            for sym, qty in stock_dict.items():
                qty = qty[0]
                sell(sym, qty)
            soldout = True
            bought_list = []
            stock_dict = get_stock_balance_msg()

        if t_start < t_now < t_sell :  # AM 09:05 ~ PM 03:15 : 매수
            for sym in bought_list: #수익률 2.5, 손해 2.5시 매도
                stock_dict = get_stock_balance()
                stock_list = stock_dict.get(sym, ["0","0"])
                rate = float(stock_list[1])
                if sym in dont_sell:
                    continue
        
                if rate > 2.5 or rate < -2.5:

                    qty = stock_list[0]
                    sell(sym, qty)
                    send_message("%s %s %.2f%%" % (stock_list[2], "익절" if rate>0 else "손절" ,rate))
                    bought_list.remove(sym)

            for item in order_log:
                stc = order_log[item]
                if stc[0] < t_now:
                    result = cancel(stc[1])
                    if result:
                        if item in bought_list:
                            bought_list.remove(item)
                    to_delete.append(item)
            for item in to_delete:
                del order_log[item]
                
            parallel_check_buy_conditions(symbol_list, buy_amount, bought_list, buytry_list)
            time.sleep(0.1)
            if t_now.minute > 30 and (last_executed is None or last_executed.hour != t_now.hour): 
                stock_dict = get_stock_balance_msg()
                last_executed = t_now
                time.sleep(1)
        if t_sell < t_now < t_exit:  # PM 03:10 ~ PM 03:30 : 일괄 매도
            if soldout == False:
                stock_dict = get_stock_balance_msg()
                for sym, qty in stock_dict.items():
                    qty = qty[0]
                    sell(sym, qty)
                soldout = True
                bought_list = []
                time.sleep(1)
        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            print("실행외 시간")
            print(t_now)
            time.sleep(3600)
            continue
except Exception as e:
    send_message(f"[<@921039947648073788>오류 발생]{e}")
    time.sleep(1)

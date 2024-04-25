import requests
import json
import datetime
import time
import yaml
from pytz import timezone

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
    print(res)
    ACCESS_TOKEN = res.json()["access_token"]
    print(ACCESS_TOKEN)
    '''
    
    return 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImEzZjg5NDllLWFjMGUtNDY4MC05ZGQyLTc3YTYyNzU2NmNlNCIsImlzcyI6InVub2d3IiwiZXhwIjoxNzExMTg1MDUyLCJpYXQiOjE3MTEwOTg2NTIsImp0aSI6IlBTSG1kTkVlMEpnWTluM0w0OUpVbjRxNERRNVZIaDUwUWM4TSJ9.BdEsb7jiIRbtHb8ix6KVVJ0Z-0Wuq0Ycd0ge5rpIyQh9nhYJCPiiriieFqDvfyBzBSY0D-g4puw3MRklziKvHQ'
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
    elif res.json()['rt_cd'] == '7':
        send_message(f"[취소 실패]{str(res.json())}")
        return True
    else:
        send_message(f"[취소 실패]{str(res.json())}")
        return False

# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()

    symbol_list = ['286750', '340360', '065650', '177350', '090150', '092870', '094970', '270520', '043220', '003580', '001210', '003160', '067630', '104200', '059210', '222080', '321820', '064800', '073640', '192410', '013310', '270660', '214370', '083450', '114190', '035290', '317330', '019570', '235980', '053030', '033170', '298060', '109610', '036810', '348370', '198080', '083310', '309930', '018000', '033100', '307930', '041590', '114810', '042660', '009470', '212560', '083500', '240810', '138360', '145720', '452260', '396270', '160980', '196170', '014940', '131290', '161580', '077500', '151910', '255220', '330860', '060900', '900340', '234920', '080530', '256840', '006400', '121600', '261200', '383930', '058470', '006920', '072950', '068760', '056700', '033540', '032800', '241820', '042520'] # 매수 희망 종목 리스트
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
    korea_timezone = timezone('Asia/Seoul')
    last_executed = None

    send_message("===국내 주식 자동매매 프로그램을 시작합니다===")
    while True:
        start_time = time.time()
        k=0.5
        t_now = datetime.datetime.now(korea_timezone)
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_sell = t_now.replace(hour=20, minute=15, second=0, microsecond=0)
        t_exit = t_now.replace(hour=20, minute=20, second=0,microsecond=0)
        today = t_now.weekday()
        to_delete = []
        for item in order_log:
            stc = order_log[item]
            if stc[0] < t_now:
                result = cancel(stc[1])
                if result:
                    bought_list.remove(item)
                to_delete.append(item)
        for item in to_delete:
            del order_log[item]
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
        if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
            send_message("주말이므로 프로그램을 종료합니다.")
            break
        if t_9 < t_now < t_start and soldout == False: # 잔여 수량 매도
            for sym, qty in stock_dict.items():
                qty = qty[0]
                sell(sym, qty)
            soldout = True
            bought_list = []
            stock_dict = get_stock_balance_msg()
        if t_start < t_now < t_sell :  # AM 09:05 ~ PM 03:15 : 매수
            for sym in symbol_list:
                if len(bought_list) < target_buy_count:
                    if sym in bought_list or sym in buytry_list:
                        continue
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
                                stock_dict = get_stock_balance_msg()
                                t_buy = datetime.datetime.now(korea_timezone)
                                order_log[sym] = [t_buy + datetime.timedelta(minutes=10), result, sym]
                            
                    time.sleep(1)
            time.sleep(1)
            if t_now.minute > 30 and (last_executed is None or last_executed.hour != t_now.hour): 
                stock_dict = get_stock_balance_msg()
                last_executed = t_now
                time.sleep(5)
        if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
            if soldout == False:
                stock_dict = get_stock_balance_msg()
                for sym, qty in stock_dict.items():
                    qty = qty[0]
                    sell(sym, qty)
                soldout = True
                bought_list = []
                time.sleep(1)
        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            send_message("프로그램을 종료합니다.")
            break
        end_time = time.time()
        print("작업수행시간", end_time - start_time)
        print(bought_list)
        print(buytry_list)
        print(order_log)
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)
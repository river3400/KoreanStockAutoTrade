import requests
import json
import datetime
import time
import yaml
from datetime import timedelta
import pandas as pd
import numpy as np
import os
from symbols import all_symbol

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

def get_target_price(code="005930", k=0.5):
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
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * k
    return target_price

def get_movingaverage(code='005930', day='1'):
    """이동평균선 가격 조회"""
    time_now = datetime.datetime.now()
    str_today = time_now.strftime('%Y%m%d')
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
    "FID_INPUT_DATE_2":str_today,
    "FID_PERIOD_DIV_CODE":"D",
    "FID_ORG_ADJ_PRC":"0"
    }
    res = requests.get(URL, headers=headers, params=params)
    data = res.json()
    if res.json()['output'][0]['stck_bsop_date'] == str_today:
        data['output'].pop(0)
    movingaverage = [item['stck_oprc'] for item in data['output'][0:day]]
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
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
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

def buy(code="005930", qty="1"):
    """주식 시장가 매수"""  
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
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
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return False

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
symbol_list = ['095570', '138930', '155660', '078930', '294870', '001390', '025000', '058860', '011070', '037560', '383800', '023150', '010060', '001740', '096770', '285130', '003570', '011810', '011420', '002100', '012320', '017900', '007690', '001140', '014530', '090350', '005250', '353200', '006570', '128820', '006040', '336260', '115390', '286940', '004990', '017180', '012690', '204210', '134380', '003850', '001270', '030790', '001470', '028050', '001360', '068290', '003230', '272550', '000070', '004380', '010960', '136490', '011300', '134790', '016590', '029530', '034300', '031430', '002870', '293940', '003560', '078520', '006740', '012280', '007310', '271560', '105840', '008600', '033270', '025820', '074610', '023800', '129260', '013360', '081000', '033240', '271980', '002620', '001550', '001630', '272450', '012600', '006380', '009070', '417310', '192820', '003070', '031820', '020120', '015890', '004100', '214420', '069260', '000970', '008930', '009240', '009180', '004710', '002220', '003300', '009460', '088350', '009830', '143210', '000720', '064350', '004560', '005380', '001500', '111110', '311690', '025440', '050120', '028300', '024120', '044180', '111870', '060720', '060370', '218410', '032540', '036620', '217730', '215000', '366030', '029480', '440790', '043650', '204020', '186230', '019660', '286750', '137080', '085910', '007390', '106520', '376930', '054050', '012340', '270870', '144960', '340360', '032190', '078140', '438220', '290120', '213420', '006620', '099410', '228340', '203650', '066900', '033130', '418420', '294140', '060240', '012700', '219420', '377480', '065650', '408920', '250060', '333050', '118990', '214610', '251120', '199730', '019010', '177350', '337930', '365900', '146320', '122350', '023600', '054540', '042600', '252990', '396300', '049180', '060230', '328380', '192440', '115570', '330730', '013810', '430220', '405640', '010280', '066790', '115530', '900120', '127710', '339950', '099190', '090150', '059100', '124500', '372800', '361570', '061040', '347860', '310200', '238090', '174900', '073570', '102120', '065420', '095910', '351320', '056190', '041510', '007820', '043340', '187660', '200710', '241840', '045660', '224110', '230980', '021080', '101360', '086520', '054940', '950130', '092870', '317870', '438580', '058630', '033310', '065150', '265560', '122640', '080520', '049480', '109080', '153710', '053080', '382840', '336060', '095270', '065950', '071460', '192390', '203450', '086390', '241690', '024800', '054930', '446150', '179900', '054210', '351330', '047560', '066980', '123570', '033230', '100030', '083640', '064290', '115310', '049550', '389020', '254120', '040420', '079370', '137950', '033320', '094970', '080220', '034940', '036930', '263860', '208350', '382480', '119850', '270520', '363250', '362320', '052300', '071850', '223310', '042040', '054410', '258610', '274090', '009730', '082660', '950160', '322780', '237880', '065130', '200230', '045340', '105550', '290090', '026150', '246710', '043220', '062860', '104480', '065690', '225590', '054300', '331380', '005670', '371950', '377220', '319660', '031980', '002230', '006140', '417180', '365590', '221840', '039340', '222980', '256150', '070590', '078350', '386580', '048410', '052260', '039610', '090710', '037440', '076340', '244880', '257990', '323350', '103660', '270210', '276240', '221800', '250030', '136660', '336040', '052960', '212310', '006840', '079160', '011150', '097950', '000590', '007340', '069730', '007700', '007070', '012630', '003580', '096760', '105560', '011790', '006120', '210980', '064960', '035250', '009450', '013580', '030610', '014280', '002990', '001210', '006280', '004370', '006370', '117580', '047040', '000430', '003220', '001070', '005880', '024900', '002150', '170900', '028100', '082640', '049770', '018500', '003160', '377190', '004000', '280360', '033920', '002760', '005180', '003960', '000390', '021050', '004360', '013000', '021820', '067830', '033530', '027970', '336370', '017550', '006880', '002700', '055550', '122900', '010580', '007460', '003060', '036570', '014440', '446070', '047400', '014990', '000230', '002600', '003780', '323410', '029460', '053210', '007810', '005420', '071950', '002020', '015590', '259960', '003240', '009410', '084870', '047050', '039130', '000080', '071050', '006200', '023350', '161390', '010100', '128940', '018880', '009420', '008770', '006060', '133820', '000850', '016580', '004800', '298000', '000540', '054620', '013720', '058820', '065770', '067630', '024850', '036640', '424760', '046440', '038340', '104200', '030190', '327260', '022220', '317240', '052220', '094480', '348150', '098460', '014200', '006050', '282720', '308100', '039860', '138610', '042420', '950220', '311390', '092730', '348210', '194700', '040160', '214870', '064260', '104040', '006580', '290380', '096350', '131220', '088130', '013120', '109860', '066670', '196490', '092070', '104460', '290550', '131180', '315640', '388790', '038390', '016100', '005990', '377030', '100590', '067280', '133750', '054180', '021880', '059210', '058110', '080160', '001810', '254490', '442900', '100790', '412930', '250000', '008470', '090460', '032790', '142760', '032850', '014970', '009620', '448740', '225190', '002290', '038500', '046390', '027580', '091580', '089980', '042940', '411080', '043710', '037350', '015750', '148150', '017510', '108860', '043100', '357780', '236200', '139050', '001000', '162300', '099320', '222080', '352480', '013990', '125210', '052710', '159010', '101390', '078860', '262840', '001540', '293780', '290740', '217480', '214310', '237690', '195990', '227100', '397030', '230360', '073540', '064090', '356680', '067570', '437780', '183490', '227950', '323230', '007530', '036560', '036000', '045060', '052420', '131030', '082210', '380540', '321820', '019210', '046970', '101170', '066590', '217820', '030530', '012620', '112040', '065370', '044960', '056090', '344860', '246960', '088390', '264850', '088290', '099750', '092130', '060150', '189300', '039290', '058450', '417840', '110020', '208140', '045510', '225220', '159580', '054950', '287410', '322510', '064800', '067000', '043610', '303030', '278280', '293490', '025880', '105330', '391710', '190650', '049430', '041960', '045970', '196450', '056360', '023160', '191420', '073640', '054450', '215480', '043200', '208340', '150900', '038950', '318010', '068050', '251970', '093380', '237820', '057880', '137400', '376180', '087600', '418170', '067310', '136480', '400840', '101680', '053300', '054040', '053590', '047080', '007770', '234340', '090850', '290270', '192410', '084110', '189980', '114920', '227420', '233250', '208890', '044990', '121060', '279060', '289860', '086460', '180060', '282330', '139130', '006360', '066570', '034120', '001380', '018670', '395400', '071970', '037270', '005320', '002720', '073240', '008350', '058730', '006650', '192080', '007590', '026960', '102260', '001520', '008970', '014820', '005300', '027740', '088980', '138040', '090370', '009680', '085620', '377740', '035150', '028260', '207940', '016360', '029780', '002810', '000520', '009770', '248170', '200880', '003080', '004980', '091090', '004430', '011930', '031440', '003410', '004920', '139990', '018250', '161000', '326030', '140910', '181710', '012160', '015360', '006980', '014830', '011330', '003460', '214320', '088260', '139480', '015020', '194370', '030000', '063160', '071320', '088790', '100250', '051630', '005070', '036420', '007980', '078000', '363280', '036580', '071090', '019490', '002200', '000240', '123890', '015760', '025890', '004150', '011700', '300720', '451800', '012450', '101530', '005440', '086280', '010620', '329180', '378850', '094280', '005870', '035760', '037370', '318000', '036670', '151860', '122450', '160550', '950110', '036120', '040610', '184230', '016250', '078890', '053950', '198440', '014570', '900280', '060480', '078130', '307750', '049080', '187790', '190510', '267320', '111710', '091590', '137940', '104620', '039560', '007720', '290670', '005710', '010170', '298540', '299170', '263800', '067990', '086450', '032960', '025900', '073190', '310870', '043360', '068930', '105740', '141080', '281740', '090360', '038060', '267980', '446190', '049950', '222160', '323990', '267790', '331520', '299910', '099390', '064480', '200780', '138580', '018310', '054090', '024950', '017480', '107600', '378800', '079650', '171090', '086710', '043260', '100700', '024830', '208370', '253450', '131090', '290520', '215600', '226330', '418210', '222420', '297090', '101240', '260930', '357580', '332370', '289010', '031310', '032080', '013310', '085810', '314140', '196300', '238120', '270660', '389500', '260970', '306040', '234300', '298380', '003800', '205100', '439410', '208860', '182400', '069410', '096870', '376190', '061970', '060850', '039830', '067170', '273060', '082850', '018620', '336570', '044340', '101730', '089850', '264450', '435380', '430700', '388800', '413630', '039020', '073490', '053350', '115610', '181340', '160600', '024810', '041830', '277410', '037330', '150840', '289220', '049630', '095700', '089790', '052670', '038010', '033340', '388050', '036890', '131100', '016790', '042000', '317530', '050110', '078340', '063080', '263700', '214370', '024880', '104540', '222040', '241710', '102940', '121850', '433530', '323280', '053620', '124560', '051360', '033830', '204610', '356860', '046210', '177830', '370090', '321260', '053610', '367000', '032580', '163730', '448370', '149980', '106080', '017890', '025770', '024740', '092300', '011080', '032860', '260870', '317860', '092590', '448780', '086220', '245450', '258540', '217910', '434190', '116100', '000120', '005830', '000990', '000210', '017940', '383220', '011200', '092220', '092230', '051910', '079550', '400760', '005940', '034310', '002360', '402340', '001510', '017670', '024070', '012610', '009140', '339770', '092440', '013700', '002350', '008060', '008110', '005750', '009190', '069620', '012800', '001440', '003490', '001230', '000020', '241560', '001530', '092200', '013570', '032350', '011170', '357430', '094800', '007120', '396690', '011390', '005030', '007160', '014710', '004440', '004450', '007860', '019440', '075580', '068270', '005390', '404990', '004770', '112610', '002310', '011090', '123700', '004250', '111770', '009970', '070960', '017370', '049800', '003470', '001200', '008250', '007660', '102460', '006490', '006220', '004910', '013870', '002380', '344820', '006890', '091810', '001020', '090080', '009810', '104700', '017960', '161890', '168490', '053690', '004960', '001750', '002320', '003480', '003530', '042670', '322000', '004020', '013520', '032560', '298040', '241520', '083450', '195940', '442770', '086960', '024940', '099220', '246690', '079940', '114190', '039240', '011040', '035290', '038530', '204620', '168330', '094860', '253590', '225570', '085670', '093640', '008830', '389260', '036480', '108380', '003310', '393890', '317330', '023790', '005290', '060570', '187870', '263690', '214680', '376300', '127120', '219550', '171010', '084650', '228850', '328130', '039980', '019570', '042500', '215200', '235980', '086900', '257370', '012860', '363260', '288980', '059090', '053030', '301300', '086040', '032980', '033560', '083650', '357880', '143240', '419120', '009300', '032280', '037460', '046890', '027040', '093920', '178320', '065710', '080470', '011560', '094840', '276040', '408900', '033170', '025320', '419270', '445970', '264660', '359090', '050860', '154030', '227610', '123010', '158430', '140670', '123750', '205500', '298060', '080000', '109610', '041910', '096690', '088800', '262260', '089970', '036810', '043090', '070300', '333620', '348370', '198080', '290650', '083310', '169330', '033160', '347890', '259630', '900300', '322310', '046120', '226400', '353590', '309930', '232140', '065530', '332570', '072470', '103840', '074600', '299900', '313760', '018000', '142210', '069330', '340930', '178780', '372170', '067920', '065440', '086890', '063760', '294090', '096040', '950140', '217190', '072520', '122310', '033100', '051980', '144510', '065060', '311320', '085660', '094850', '094360', '307930', '192250', '093320', '220260', '089890', '029960', '282880', '182360', '043590', '044490', '089030', '117730', '064760', '034230', '368770', '106240', '131760', '140860', '263750', '087010', '022100', '189690', '318020', '114630', '023900', '220100', '334970', '203690', '335810', '041590', '051380', '239890', '304840', '446750', '166090', '106190', '080720', '114810', '226440', '005860', '054920', '076610', '059270', '039010', '097870', '353190', '215090', '263920', '145020', '163430', '210120', '217320', '236030', '149300', '251280', '311960', '311060', '208850', '216400', '254160', '346010', '308700', '258050', '217950', '327610', '107640', '001040', '365550', '097230', '060980', '016380', '001940', '034220', '373220', '006260', '108320', '001120', '010950', '302440', '000660', '001570', '000270', '003920', '025860', '145210', '001680', '016710', '042660', '084010', '001790', '012510', '001080', '009900', '005360', '003650', '001340', '002410', '007210', '003000', '026940', '002070', '100220', '006660', '032830', '009470', '007540', '008490', '001430', '004970', '005800', '001720', '009270', '019170', '002790', '183190', '267850', '005850', '298690', '900140', '010600', '000910', '000100', '084680', '101140', '034590', '023810', '103590', '271940', '001560', '004700', '000480', '120030', '035720', '377300', '109070', '001620', '281820', '030200', '003690', '450140', '138490', '021240', '192400', '284740', '264900', '005740', '011280', '001420', '019180', '010820', '016800', '005430', '024720', '034830', '047810', '002390', '213500', '014680', '006390', '052690', '000880', '272210', '195870', '079430', '069960', '017800', '126560', '093240', '003010', '081660', '060310', '126600', '051500', '023460', '180400', '900290', '297890', '047920', '115450', '439730', '099520', '021320', '035600', '309960', '419530', '435870', '289080', '048770', '040300', '051390', '399720', '397880', '421800', '407400', '091970', '242040', '130580', '036800', '212560', '285490', '332290', '060260', '020180', '048910', '054670', '067080', '263600', '025950', '041930', '088910', '016670', '263720', '039840', '079810', '300120', '215100', '900260', '302550', '277070', '147760', '033200', '207760', '035620', '064550', '314930', '038460', '043150', '382900', '206400', '225530', '310210', '226340', '288330', '369370', '086670', '307870', '148780', '053700', '032750', '038540', '415580', '063170', '018680', '045300', '036630', '068940', '290690', '258790', '066910', '204630', '065350', '393360', '356890', '217330', '376290', '189330', '096530', '123860', '136410', '307180', '052770', '027360', '053800', '131370', '096610', '019990', '103230', '031330', '100090', '052020', '058610', '203400', '109960', '230240', '038870', '128540', '064850', '083500', '391060', '066970', '073110', '179290', '123040', '241790', '031510', '244460', '155650', '251370', '193250', '079000', '115440', '037400', '240810', '008290', '348350', '123420', '036090', '136540', '320000', '011320', '442130', '084370', '080010', '900110', '134060', '001840', '017250', '175140', '071200', '333430', '068330', '174880', '361390', '090470', '417500', '239340', '072020', '389030', '086060', '007370', '047820', '016920', '079190', '221980', '436530', '073010', '225430', '036030', '046070', '052330', '051780', '115180', '900250', '045520', '214150', '066700', '064520', '079970', '084730', '214450', '027710', '389140', '234100', '041020', '290720', '043370', '128660', '406760', '041460', '021650', '900270', '084990', '041440', '138360', '064240', '115160', '200670', '024060', '278990', '199150', '238500', '223220', '162120', '236340', '354390', '191600', '149010', '246250', '224020', '238170', '224760', '093510', '337840', '341310', '248020', '176590', '189350', '393210', '303360', '027410', '012030', '234080', '009440', '058850', '032640', '000680', '008260', '009160', '361610', '100840', '036530', '005610', '267290', '000050', '002240', '009290', '037710', '008870', '011780', '003540', '014160', '006340', '024890', '002880', '003830', '069460', '004830', '145720', '004140', '002210', '282690', '084670', '030720', '000150', '034020', '089860', '071840', '002840', '268280', '018260', '145990', '023000', '002450', '004690', '001290', '004410', '000180', '306200', '003030', '004170', '002030', '137310', '025530', '003520', '000670', '316140', '002920', '093230', '003120', '015860', '317400', '348950', '035000', '009310', '381970', '145270', '357120', '120110', '039490', '004720', '028670', '003670', '293480', '123690', '003350', '042700', '020000', '025750', '130660', '180640', '372910', '452260', '000370', '012330', '241590', '010660', '298020', '093370', '005010', '068790', '245620', '214270', '130500', '095340', '950170', '035900', '024840', '114450', '024910', '049720', '026910', '066620', '035460', '247660', '417010', '095660', '033640', '089140', '396270', '278650', '017650', '129920', '007680', '023910', '224060', '077360', '090410', '100130', '005160', '094170', '110990', '078590', '109740', '263020', '042510', '069540', '214260', '412350', '098120', '140410', '101330', '279600', '095500', '099430', '308080', '100120', '121800', '335890', '082920', '042370', '050090', '238200', '065450', '000250', '038070', '006730', '100660', '092190', '189860', '357550', '365340', '258830', '039310', '252500', '331920', '299660', '268600', '154040', '050960', '253840', '099440', '048870', '025870', '012790', '187270', '222800', '160980', '037760', '060590', '058220', '092040', '036010', '054800', '214430', '196170', '179530', '900100', '129890', '060540', '096630', '098660', '054630', '312610', '239610', '148930', '071670', '089530', '173940', '236810', '101400', '265740', '419080', '037950', '019590', '009780', '053280', '014940', '417860', '080580', '067900', '066430', '046940', '069080', '053580', '330350', '048430', '388720', '191410', '072770', '303530', '078020', '095190', '091120', '353810', '211050', '049070', '101930', '019540', '026040', '033050', '199820', '082270', '314130', '036180', '018120', '261780', '066360', '424140', '089150', '032500', '102370', '256940', '036690', '033290', '294570', '060280', '040350', '405100', '016600', '054780', '057680', '340570', '277880', '131290', '037070', '168360', '119500', '007330', '405000', '023770', '347740', '062970', '161580', '347770', '025550', '032300', '079170', '220180', '170030', '126640', '127980', '061250', '205470', '028080', '065510', '010240', '112190', '179720', '200580', '266470', '322190', '258250', '185190', '447690', '224810', '299670', '234070', '066830', '413300', '266870', '016610', '375500', '089470', '267250', '082740', '001060', '003620', '000040', '093050', '051900', '108670', '005490', '004060', '034730', '002820', '002710', '002900', '214390', '002140', '010130', '001260', '004270', '005720', '072710', '030210', '023590', '019680', '009320', '001130', '023450', '092780', '002690', '210540', '330590', '020150', '009580', '357250', '107590', '003610', '008040', '006090', '005930', '000810', '006110', '002170', '005680', '003720', '005500', '011230', '075180', '014910', '058650', '308170', '248070', '026890', '035510', '102280', '403550', '008700', '090430', '001780', '023960', '015260', '010120', '097520', '002630', '001800', '011690', '016880', '005820', '077500', '005950', '334890', '249420', '007110', '007570', '025620', '044380', '013890', '010640', '014580', '004870', '005690', '017810', '005810', '950210', '000140', '025540', '009540', '011500', '069640', '051600', '267270', '004310', '307950', '267260', '001450', '057050', '002460', '079980', '078150', '448760', '058400', '053290', '060250', '151910', '255220', '057030', '053270', '035080', '053260', '051490', '293580', '290660', '153460', '330860', '142280', '348340', '068240', '020400', '004780', '317850', '027830', '120240', '140520', '060900', '033500', '060380', '079960', '113810', '217500', '228670', '067730', '038290', '072870', '078160', '080420', '417970', '087260', '348030', '201490', '950190', '206640', '208710', '086820', '066410', '014470', '338220', '251630', '044480', '126340', '082800', '419540', '445360', '065170', '425290', '361670', '263810', '140070', '011370', '003100', '067370', '014620', '081580', '053450', '222810', '347000', '950200', '032680', '035610', '136510', '159910', '020710', '138070', '243840', '036710', '049960', '115480', '074430', '149950', '143160', '368600', '052860', '038880', '084850', '059120', '067160', '065660', '148250', '117670', '291650', '052790', '092600', '121890', '097780', '101490', '039440', '044780', '200470', '031860', '440820', '156100', '058970', '112290', '010470', '352910', '138080', '173130', '394280', '122990', '032820', '041190', '073560', '153490', '376980', '008370', '101160', '076080', '196700', '377460', '900340', '036200', '084440', '049520', '263770', '023410', '056080', '263050', '215790', '272290', '041520', '131400', '102710', '083470', '079950', '389470', '216050', '094820', '234920', '187420', '123330', '147830', '204270', '126880', '418550', '000440', '382800', '204840', '109820', '004650', '119860', '900310', '272110', '083550', '064820', '047770', '078940', '080530', '123410', '355150', '200130', '365270', '096240', '036170', '139670', '413600', '219130', '134580', '095610', '108230', '199800', '130740', '047310', '441270', '091700', '256630', '053160', '075130', '237750', '291810', '430230', '435620', '003380', '101670', '004590', '256840', '023760', '037230', '030520', '045100', '123840', '430460', '319400', '243070', '343090', '229500', '178600', '302920', '403360', '253610', '322970', '206950', '266170', '232830', '286000', '102950', '140610', '379390', '388610', '233990', '402420', '215570', '217880', '202960', '341170', '222670', '150440', '001460', '004840', '114090', '001250', '039570', '014790', '204320', '175330', '432320', '119650', '033180', '044450', '003550', '229640', '035420', '338100', '178920', '005090', '001770', '077970', '000500', '000860', '012200', '017040', '083420', '214330', '024110', '004540', '251270', '000320', '000490', '084690', '003090', '000300', '015230', '016090', '005960', '000640', '163560', '004890', '016740', '192650', '024090', '000400', '023530', '009200', '008420', '025560', '006800', '000890', '006400', '009150', '010140', '001820', '041650', '017390', '007610', '002420', '004490', '126720', '004080', '012170', '020560', '010780', '012750', '244920', '085310', '010400', '095720', '000700', '072130', '000220', '008730', '350520', '000760', '003200', '008500', '020760', '226320', '000950', '089590', '018470', '185750', '011000', '002780', '000650', '033250', '118000', '033780', '044820', '055490', '010770', '058430', '103140', '086790', '352820', '152550', '036460', '010040', '004090', '002960', '007280', '003680', '105630', '016450', '010420', '014130', '005110', '011210', '011760', '227840', '010690', '298050', '003280', '265520', '211270', '056730', '083660', '403870', '067290', '226360', '052900', '091340', '019550', '036540', '049470', '048550', '063440', '089230', '161570', '121440', '900070', '036190', '121600', '089600', '306620', '217270', '234690', '065560', '069140', '048470', '442310', '045390', '078600', '021040', '194480', '206560', '261200', '075970', '131970', '030350', '223250', '217620', '197140', '187220', '383930', '317120', '232680', '171120', '347700', '200350', '277810', '108490', '071280', '058470', '377450', '195500', '305090', '093520', '041920', '014100', '241770', '006920', '218150', '018700', '046310', '006910', '018290', '148140', '318410', '141000', '054220', '093190', '072950', '419050', '439250', '065570', '101000', '294630', '019770', '122690', '035890', '053060', '340440', '067770', '068760', '036830', '304100', '086980', '084180', '317770', '033790', '049830', '002800', '017000', '056700', '257720', '208640', '050890', '352700', '025980', '083930', '246720', '067390', '040910', '069920', '185490', '175250', '052460', '119830', '114840', '297570', '260660', '255440', '030960', '263540', '038680', '042110', '275630', '069510', '050760', '288620', '317830', '072990', '357230', '247540', '383310', '038110', '422040', '354200', '291230', '048830', '170920', '143540', '250930', '065500', '053980', '039200', '368970', '226950', '057540', '273640', '122870', '215360', '215380', '065680', '307280', '032940', '104830', '014190', '038620', '097800', '335870', '206650', '032620', '078070', '449020', '296640', '302430', '164060', '067010', '039030', '377330', '035810', '352940', '119610', '051370', '048530', '043910', '023440', '276730', '216080', '229000', '044060', '228760', '358570', '051160', '053050', '219750', '284620', '115500', '039420', '089010', '052400', '402030', '027050', '183300', '166480', '015710', '317690', '066310', '110790', '083790', '352770', '360070', '091440', '322180', '425420', '321550', '425040', '081150', '058530', '033540', '037030', '170790', '049120', '032800', '222110', '009520', '094940', '035200', '300080', '241820', '299030', '013030', '126700', '373200', '066130', '034950', '063570', '039740', '436610', '052600', '092460', '042520', '198940', '002680', '034810', '214180', '060560', '238490', '243870', '288490', '176750', '199290', '390110', '207490', '122830', '140660', '232530', '299480', '446600', '169670', '318660', '331660']
found_list = []
found_hpr = []
false_code = []
true_code = []
time_now = datetime.datetime.now()
# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()

    send_message("===종목 찾기 프로그램을 시작합니다===")
    a = 0
    for sym in all_symbol:
        
        df=get_holcv(sym, 5)
        print(sym, df)
        if isinstance(df, int) and df == -1:
            false_code.append(sym)
            print(f"{false_code}은 상폐")
            continue
        true_code.append(sym)
        a+=1
        if a == 100:
            print(f"truecode:{ true_code}")
            print(f"Falsecode:{false_code}") 
            a=0

    
    
    print(f"truecode:{ true_code}")
    print(f"Falsecode:{false_code}") 

    send_message(f"truecode:{ true_code}")
    send_message(f"Falsecode:{false_code}")
    with open('output.txt', 'w') as f:
        f.write("True Code:")
        f.write(str(true_code))
        f.write("\nFalse Code:\n")
        f.write(str(false_code))
    #os.system("shutdown -s -f")

except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)
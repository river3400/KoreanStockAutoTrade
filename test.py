import datetime

def check_buy_condition(sym):
    
                order_log[sym] = [t_now + datetime.timedelta(minutes=10), sym]
            

try:

    order_log = {}


    k=0.5
    t_now = datetime.datetime.now()
    t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
    t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
    t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
    t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
    t_restart = t_now.replace(hour=0, minute=1, second=0, microsecond=0)
    t_start = t_now.replace(hour=0, minute=2, second=0, microsecond=0)
    today = t_now.weekday()
    check_buy_condition('123456')
    print(order_log)
except:
    pass
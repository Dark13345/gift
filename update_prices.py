"""Берёт с Yahoo Finance цены и графики за 40 дней по акциям конструктора и пишет prices.json.

Запускается GitHub по расписанию (.github/workflows/prices.yml). Сайт читает prices.json
и обновляет карточки акций. Если Yahoo не ответил по какой-то бумаге, её старые данные
остаются в файле как были.
"""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone

TICKERS = ['AAPL', 'NVDA', 'TSLA', 'AMZN', 'MSFT', 'GOOGL', 'NFLX', 'AMD', 'DIS', 'KO', 'V', 'WMT',
           'PYPL', 'INTC', 'BABA', 'UBER', 'SBUX', 'NKE', 'MCD', 'JPM', 'BA', 'PEP', 'ADBE', 'CSCO']
DAYS = 40
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prices.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36'}


def fetch(tk):
    for host in ('query1', 'query2'):
        url = f'https://{host}.finance.yahoo.com/v8/finance/chart/{tk}?range=3mo&interval=1d'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                res = json.load(r)['chart']['result'][0]
            closes = [c for c in res['indicators']['quote'][0]['close'] if c is not None]
            price = res['meta']['regularMarketPrice']
            closes[-1] = price
            prev = closes[-2]
            return {
                'price': round(price, 2),
                'chg': round((price / prev - 1) * 100, 1),
                'series': [round(c, 2) for c in closes[-DAYS:]],
            }
        except Exception as e:
            err = e
    print(f'{tk}: не получилось ({err})', file=sys.stderr)
    return None


try:
    data = json.load(open(OUT, encoding='utf-8'))
except Exception:
    data = {'stocks': {}}

ok = 0
for tk in TICKERS:
    q = fetch(tk)
    if q:
        data['stocks'][tk] = q
        ok += 1
    time.sleep(0.3)

if ok == 0:
    sys.exit('Yahoo не ответил ни по одной акции — prices.json не трогаю')

data['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
# каждая акция и время обновления — на своей строке: так GitHub видит, поменялись ли сами цены
rows = [f'"{tk}":' + json.dumps(data['stocks'][tk], separators=(',', ':')) for tk in TICKERS if tk in data['stocks']]
text = '{\n"updated":"' + data['updated'] + '",\n"stocks":{\n' + ',\n'.join(rows) + '\n}}\n'
json.loads(text)
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print(f'обновлено {ok} из {len(TICKERS)}')

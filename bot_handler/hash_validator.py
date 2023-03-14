import requests

from django.conf import settings


class OkLinkValidator:
    API_KEY = settings.OKLINK_API_KEY
    BASE_URL = 'https://www.oklink.com'

    def get_transaction(self, tr_hash: str, chain_name: str):
        headers = {'Ok-Access-Key': self.API_KEY}
        url = self.BASE_URL + '/api/v5/explorer/transaction/transaction-fills'
        data = {'chainShortName': chain_name, 'txid': tr_hash}
        resp = requests.get(url, headers=headers, params=data)
        return resp


class CoingeckoApi:
    BASE_URL = 'https://api.coingecko.com/api/v3/'
    COINS = ('binancecoin', 'ethereum', 'matic-network', 'alium-finance')
    CURRENCY = 'usd'

    def get_rates(self):
        url = self.BASE_URL + '/simple/price'
        data = {'ids': ','.join(self.COINS), 'vs_currencies': self.CURRENCY}
        resp = requests.get(url, params=data)
        return resp

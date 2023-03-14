from celery import shared_task
from decimal import Decimal

from bot_handler.hash_validator import CoingeckoApi
from bot_handler.models import TokenPrice

MAP_CURRENCY = {
    'binancecoin': 'BSC',
    'ethereum': 'ETH',
    'matic-network': 'POLYGON',
    'alium-finance': 'ALM'
}


@shared_task
def get_rates():
    resp = CoingeckoApi().get_rates().json()
    for k, v in resp.items():
        obj, _ = TokenPrice.objects.get_or_create(name=MAP_CURRENCY.get(k))
        obj.price = Decimal(v.get('usd', None))
        obj.save()


import time
from decimal import ROUND_DOWN, Decimal, getcontext

import requests
from django.conf import settings
from django.core.cache import cache
from utils.exceptions import UtilsException


class CurrencyException(UtilsException):
    ...


class CurrencyNotSupported(CurrencyException):
    ...


class InvalidPriceReturned(CurrencyException):
    ...


class PriceReturnedIsNaN(CurrencyException):
    ...


currencies = {
    "eth": "ethereum",
}


def price_cache_keys(currency):
    return f"currency_price_{currency}", f"currency_price_{currency}_at"


def get_price(currency: str) -> Decimal:
    price_key, at = price_cache_keys(currency)
    timestamp = cache.get(at)
    if time.time() - timestamp < settings.CURRENCY_PRICE_EXPIRE_IN_SECONDS:
        return Decimal(cache.get(price_key))

    api_base_url = f"https://api.coingecko.com/api/v3/simple/price?ids={currency}&vs_currencies=usd"
    raw_price = requests.get(api_base_url).json().get(currency, {}).get("usd")
    if not raw_price:
        raise InvalidPriceReturned
    try:
        price_str = str(raw_price)
        price_decimal = Decimal(price_str)
    except BaseException:
        raise PriceReturnedIsNaN
    cache.set(price_key, price_str)
    cache.set(at, time.time())
    return price_decimal


def get_currency(c: str):
    if c not in currencies.values():
        parsed_currency = currencies.get(c.lower())
    else:
        parsed_currency = c
    if not parsed_currency:
        raise CurrencyNotSupported(f"the currency {c} is not supported for now!")
    return parsed_currency


def usd_to(currency: str, amount: str):
    amount = Decimal(amount)
    original_prec = int(getcontext().prec)
    getcontext().prec = 32
    parsed_currency = get_currency(currency)
    price = Decimal(1) / get_price(parsed_currency)
    val = (amount * price).quantize(Decimal(".000000001"), rounding=ROUND_DOWN)
    getcontext().prec = original_prec
    return str(val).rstrip("0")


def to_usd(amount: str, currency: str):
    original_prec = int(getcontext().prec)
    getcontext().prec = 32
    amount = Decimal(amount)
    parsed_currency = get_currency(currency)
    price = get_price(parsed_currency)
    val = (amount * price).quantize(Decimal(".000000001"), rounding=ROUND_DOWN)
    getcontext().prec = original_prec
    return str(val).rstrip("0")

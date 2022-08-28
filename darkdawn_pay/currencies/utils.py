from decimal import ROUND_DOWN, Decimal, getcontext

import requests

from utils.exceptions import UtilsException


class CurrencyNotSupported(UtilsException):
    ...


class InvalidCurrencyPriceReturned(UtilsException):
    ...


class PriceReturnedIsNaN(UtilsException):
    ...


currencies = {
    "eth": "ethereum",
}


def to_usd(amount: str, currency: str):
    original_prec = int(getcontext().prec)
    getcontext().prec = 32
    amount = Decimal(amount)
    if currency not in currencies.values():
        parsed_currency = currencies.get(currency.lower())
    else:
        parsed_currency = currency
    if not parsed_currency:
        raise CurrencyNotSupported(f"the currency {currency} is not supported for now!")
    api_base_url = f"https://api.coingecko.com/api/v3/simple/price?ids={parsed_currency}&vs_currencies=usd"
    raw_price = requests.get(api_base_url).json().get(parsed_currency, {}).get("usd")
    if not raw_price:
        raise InvalidCurrencyPriceReturned
    try:
        price = Decimal(str(raw_price))
    except BaseException:
        raise PriceReturnedIsNaN

    val = (amount * price).quantize(Decimal(".000000001"), rounding=ROUND_DOWN)

    getcontext().prec = original_prec
    return str(val).rstrip("0")

from sqlalchemy import TypeDecorator, String

from src.home_offer.money.cuerrency.model import Currency


class CurrencyEncode(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if (value is not None) and isinstance(value, Currency):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None and isinstance(value, str):
            return Currency[value]
        return value

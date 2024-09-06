from hikka import loader, utils
import requests

class CurrencyExchangeMod(loader.Module):
    """Модуль для перевода валют с использованием Fixer.io API"""
    strings = {"name": "CurrencyExchange"}

    def __init__(self):
        self.config = loader.ModuleConfig("api_token", "", "API токен для получения курсов валют")

    async def _get_exchange_rate(self, from_currency: str, to_currency: str, token: str) -> float:
        """Получение курса валюты с API Fixer.io"""
        url = f"http://data.fixer.io/api/latest?access_key={token}"
        response = requests.get(url)
        data = response.json()

        if not data.get("success"):
            return None

        rates = data.get("rates", {})
        if from_currency not in rates or to_currency not in rates:
            return None

        from_rate = rates[from_currency]
        to_rate = rates[to_currency]
        return to_rate / from_rate

    async def _convert(self, amount: float, from_currency: str, to_currency: str, token: str) -> str:
        """Конвертация валюты"""
        exchange_rate = await self._get_exchange_rate(from_currency, to_currency, token)
        if not exchange_rate:
            return f"Ошибка получения курса для {from_currency} в {to_currency}"
        converted = amount * exchange_rate
        return f"{amount} {from_currency} = {converted:.2f} {to_currency}"

    async def exchangecmd(self, message):
        """Использование команды .exchange для перевода валюты"""
        args = utils.get_args(message)
        token = self.config["api_token"]
        
        if not token:
            await message.edit("API токен не установлен. Используй .cfg --> внешние --> CurrencyExchange для добавления токена. (https://fixer.io/)")
            return

        if len(args) != 3:
            await message.edit("Пример: .exchange 4.94 EUR RUB")
            return

        try:
            amount = float(args[0].replace(",", "."))
        except ValueError:
            await message.edit("Некорректная сумма")
            return

        from_currency = args[1].upper()
        to_currency = args[2].upper()

        result = await self._convert(amount, from_currency, to_currency, token)
        await message.edit(result)

    async def watcher(self, message):
        """Автоматический перевод при ответе на сообщение с указанной валютой"""
        if message.out:
            return

        token = self.config["api_token"]
        
        if not token:
            return

        text = message.raw_text
        parts = text.split()

        if len(parts) != 3:
            return

        try:
            amount = float(parts[0].replace(",", "."))
        except ValueError:
            return

        from_currency = parts[1].upper()
        to_currency = parts[2].upper()

        result = await self._convert(amount, from_currency, to_currency, token)
        await message.respond(result)
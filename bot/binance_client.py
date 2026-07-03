import time
import hmac
import hashlib
import httpx
from urllib.parse import urlencode
from .logger import logger

class BinanceFuturesClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet.binancefuture.com"

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None):
        endpoint = "/fapi/v1/order"
        url = self.base_url + endpoint

        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }
        
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"

        query_string = urlencode(params)
        params["signature"] = self._generate_signature(query_string)

        headers = {"X-MBX-APIKEY": self.api_key}
        logger.info(f"API Request | {side} {order_type} {quantity} {symbol}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"API Success | OrderID: {data.get('orderId')} | Status: {data.get('status')}")
                return data
            except httpx.HTTPStatusError as e:
                error_msg = response.json().get('msg', str(e)) if response.content else str(e)
                logger.error(f"API Rejection: {error_msg}")
                raise Exception(f"Binance Error: {error_msg}")
            except Exception as e:
                logger.error(f"Network Failure: {e}")
                raise Exception(f"Network Error: {e}")

    async def get_balance(self):
        """
        Fetch futures account balances (signed).
        Returns: list of balance dicts as returned by /fapi/v2/balance
        """
        endpoint = "/fapi/v2/balance"
        url = self.base_url + endpoint
        params = {"timestamp": int(time.time() * 1000)}
        query_string = urlencode(params)
        params["signature"] = self._generate_signature(query_string)
        headers = {"X-MBX-APIKEY": self.api_key}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                logger.info("Fetched account balances from Binance Futures testnet.")
                return data
            except httpx.HTTPStatusError as e:
                try:
                    error_msg = resp.json().get('msg', str(e)) if resp.content else str(e)
                except Exception:
                    error_msg = str(e)
                logger.error(f"Balance API rejection: {error_msg}")
                raise Exception(f"Binance Error: {error_msg}")
            except Exception as e:
                logger.error(f"Network failure when fetching balances: {e}")
                raise Exception(f"Network Error: {e}")

    async def get_all_prices(self):
        """
        Fetch current futures ticker prices (public).
        Returns: dict mapping symbol -> float(price)
        """
        endpoint = "/fapi/v1/ticker/price"
        url = self.base_url + endpoint

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                return {item["symbol"]: float(item["price"]) for item in data}
            except Exception as e:
                logger.error(f"Failed to fetch prices: {e}")
                return {}
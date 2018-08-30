import flexmock
import psycopg2

from . import new_user, app, TestErebor, api


class TestPrices(TestErebor):
    def test_ticker(self):
        # B: Logged in users can access BTC/USD and ETH/USD pricing
        u_data, session_id = new_user(app)

        request, response = app.test_client.get(
            '/ticker',
            cookies={'session_id': session_id})
        assert response.status == 200
        data = response.json
        assert data.keys() == {'btc_usd', 'eth_usd'}
        # B: do it again to make sure caching works
        request, response = app.test_client.get(
            '/ticker',
            cookies={'session_id': session_id})
        assert response.status == 200

        request, response = app.test_client.get(
            '/ticker')
        assert response.status == 403

    def test_price_data(self):
        u_data, session_id = new_user(app)
        mock_multi_price_data = {
            "BTC": {"USD": 6711.79, "AUD": 9004.21},
            "ETH": {"USD": 516.4, "AUD": 694.4}
        }
        mock_histoday_price_data = {
            "Response": "Success",
            "Type": 100,
            "Aggregated": False,
            "Data": [
                {
                    "time": 1529280000,
                    "close": 6714.82,
                    "high": 6802.03,
                    "low": 6401.41,
                    "open": 6457.78,
                    "volumefrom": 65285.57,
                    "volumeto": 430241689.1299999952
                 },
                {
                    "time": 1529366400,
                    "close": 6719.72,
                    "high": 6839.6,
                    "low": 6672.2,
                    "open": 6714.56,
                    "volumefrom": 43175.8,
                    "volumeto": 291436647.1299999952}
                    ],
            "TimeTo": 1529366400,
            "TimeFrom": 1529280000,
            "FirstValueInArray": True,
            "ConversionType": {"type": "direct", "conversionSymbol": ""}
                }

        async def mock_price_func():
            return mock_multi_price_data

        async def mock_histoday_func():
            return mock_histoday_price_data

        flexmock(api.prices).should_receive(
            'current_prices').and_return(mock_price_func())
        flexmock(api.prices).should_receive(
            'historical_prices').and_return(mock_histoday_func())

        request, response = app.test_client.get(
            '/pricing_data/pricemulti?fsyms=BTC,ETH&tsyms=USD,AUD'
        )
        assert response.json == mock_multi_price_data

        request, response = app.test_client.get(
            '/pricing_data/histoday?fsym=BTC&tsym=USD&limit=1'
        )
        assert response.json == mock_histoday_price_data

    def test_local_prices(self):
        mock_price_data = [
            {'currency': 'ETH', 'time': 1451433600, 'close': 0.8925},
            {'currency': 'ETH', 'time': 1453334400, 'close': 1.54},
            {'currency': 'ETH', 'time': 1453420800, 'close': 1.52},
            {'currency': 'ETH', 'time': 1455321600, 'close': 5.22},
            {'currency': 'ETH', 'time': 1479859200, 'close': 9.78},
            {'currency': 'ETH', 'time': 1506643200, 'close': 292.58}
        ]
        INSERT_PRICES = """
        INSERT INTO ETH_USD (currency, date, price, fiat) VALUES """
        args = ", ".join('(\'{}\', to_timestamp({}), {}, \'{}\')'.format(
            entry['currency'], entry['time'], entry['close'], 'USD')
            for entry in mock_price_data)
        with psycopg2.connect(**app.db) as conn:
            with conn.cursor() as cur:
                cur.execute(INSERT_PRICES + args)

        # B: app requests range of dates
        request, response = app.test_client.get(
            '/local_prices/pricerange?currency=ETH&fiat=USD&'
            'from_date=1451433600&to_date=1479859200')
        p_data = response.json
        assert len(p_data['result']) == 5

        # B: app requests earliest timestamp
        request, response = app.test_client.get(
            '/local_prices/timestamp?currency=ETH&fiat=USD&'
            'ts=1234')
        p_data = response.json
        print(p_data)

        # B: app requests earliest timestamp
        request, response = app.test_client.get(
            '/local_prices/timestamp?currency=ETH&fiat=USD&'
            'ts=1453420000')
        p_data = response.json
        print(p_data)

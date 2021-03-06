import json
from decimal import Decimal

import requests
import flexmock

from erebor.blockchain import get_balance


class TestUnitTests(object):

    def test_mock_get_balance(self):
        flexmock(requests).should_receive('get').and_return(
            flexmock(json=lambda: json.loads(
                '{"jsonrpc": "2.0", "id": 1,'
                '"result": "0x37942530c308b7e7"}')))
        balance = get_balance("0xaC39b311DCEb2A4b2f5d8461c1cdaF756F4F7Ae9",
                              "ETH")
        assert balance == Decimal(4.004866859999999975)

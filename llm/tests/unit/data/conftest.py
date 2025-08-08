import pytest

import json
import moto


@pytest.fixture
def buy_order():
    return {
        "order_id": "e4fe65b7-3f27-4757-9792-5568eb8175b7",
        "product_id": "BTC-USD",
        "user_id": "58b20d15-617e-5ae2-8874-6a9b70a7d712",
        "order_configuration": {
            "market_market_ioc": {
                "quote_size": "1.5",
                "rfq_enabled": False,
                "rfq_disabled": False,
            }
        },
        "side": "BUY",
        "client_order_id": "835443cc-1535-4eee-be06-5f6def060efc",
        "status": "FILLED",
        "time_in_force": "IMMEDIATE_OR_CANCEL",
        "created_time": "2024-12-05T14:01:07.278515Z",
        "completion_percentage": "100",
        "filled_size": "0.0000144833961948",
        "average_filled_price": "102795.8999998081720639",
        "fee": "",
        "number_of_fills": "2",
        "filled_value": "1.488833746898263",
        "pending_cancel": False,
        "size_in_quote": True,
        "total_fees": "0.011166253101737",
        "size_inclusive_of_fees": True,
        "total_value_after_fees": "1.5",
        "trigger_status": "INVALID_ORDER_TYPE",
        "order_type": "MARKET",
        "reject_reason": "REJECT_REASON_UNSPECIFIED",
        "settled": True,
        "product_type": "SPOT",
        "reject_message": "",
        "cancel_message": "",
        "order_placement_source": "RETAIL_ADVANCED",
        "outstanding_hold_amount": "0",
        "is_liquidation": False,
        "last_fill_time": "2024-12-05T14:01:07.345053156Z",
        "edit_history": [],
        "leverage": "",
        "margin_type": "UNKNOWN_MARGIN_TYPE",
        "retail_portfolio_id": "4dec65fa-7599-41ce-8964-9a32837e5979",
        "originating_order_id": "",
        "attached_order_id": "",
        "attached_order_configuration": None,
    }


@pytest.fixture
def sell_order():
    return {
        "order_id": "e4fe65b7-3f27-4757-9792-5568eb8175b7",
        "product_id": "BTC-USD",
        "user_id": "58b20d15-617e-5ae2-8874-6a9b70a7d712",
        "order_configuration": {
            "market_market_ioc": {
                "base_size": "1.5",
                "rfq_enabled": False,
                "rfq_disabled": False,
            }
        },
        "side": "SELL",
        "client_order_id": "835443cc-1535-4eee-be06-5f6def060efc",
        "status": "FILLED",
        "time_in_force": "IMMEDIATE_OR_CANCEL",
        "created_time": "2024-12-05T14:01:07.278515Z",
        "completion_percentage": "100",
        "filled_size": "0.0000144833961948",
        "average_filled_price": "102795.8999998081720639",
        "fee": "",
        "number_of_fills": "2",
        "filled_value": "1.488833746898263",
        "pending_cancel": False,
        "size_in_quote": True,
        "total_fees": "0.011166253101737",
        "size_inclusive_of_fees": True,
        "total_value_after_fees": "1.5",
        "trigger_status": "INVALID_ORDER_TYPE",
        "order_type": "MARKET",
        "reject_reason": "REJECT_REASON_UNSPECIFIED",
        "settled": True,
        "product_type": "SPOT",
        "reject_message": "",
        "cancel_message": "",
        "order_placement_source": "RETAIL_ADVANCED",
        "outstanding_hold_amount": "0",
        "is_liquidation": False,
        "last_fill_time": "2024-12-05T14:01:07.345053156Z",
        "edit_history": [],
        "leverage": "",
        "margin_type": "UNKNOWN_MARGIN_TYPE",
        "retail_portfolio_id": "4dec65fa-7599-41ce-8964-9a32837e5979",
        "originating_order_id": "",
        "attached_order_id": "",
        "attached_order_configuration": None,
    }


@pytest.fixture
def sqs_event(buy_order, sell_order):
    return {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "provider": "COINBASE",
                        "product_id": "BTC-USD",
                        "orders": [buy_order, sell_order],
                    }
                )
            }
        ]
    }

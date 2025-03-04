import unittest
from unittest import mock
from betfairlightweight.resources.bettingresources import PriceSize

from flumine.order.order import OrderStatus, OrderTypes, BetdaqOrder
from flumine import config
from flumine.markets.market import Market
from flumine.markets.markets import Markets
from flumine.order.order import (
    BaseOrder,
    BetfairOrder,
)
from flumine.order import process
from flumine.strategy.strategy import Strategies
from flumine.utils import create_cheap_hash


class ProcessCurrentOrdersTest(unittest.TestCase):
    @mock.patch("flumine.order.process.process_current_order")
    def test_process_current_orders_with_default_sep(self, mock_process_current_order):
        mock_log_control = mock.Mock()
        mock_add_market = mock.Mock()
        market_book = mock.Mock()
        markets = Markets()
        market = Market(
            flumine=mock.Mock(), market_id="market_id", market_book=market_book
        )
        markets.add_market("market_id", market)
        strategies = Strategies()
        cheap_hash = create_cheap_hash("strategy_name", 13)
        trade = mock.Mock(market_id="market_id")
        trade.strategy.name_hash = cheap_hash
        current_order = mock.Mock(
            customer_order_ref=f"{cheap_hash}I123", market_id="market_id", bet_id=None
        )
        betfair_order = BetfairOrder(trade=trade, side="BACK", order_type=mock.Mock())
        betfair_order.id = "123"
        betfair_order.complete = True
        market.blotter["123"] = betfair_order
        event = mock.Mock(event=[mock.Mock(orders=[current_order])])

        process.process_current_orders(
            markets=markets,
            strategies=strategies,
            event=event,
            log_control=mock_log_control,
            add_market=mock_add_market,
        )
        mock_process_current_order.assert_called_with(
            betfair_order, current_order, mock_log_control
        )
        self.assertEqual(market.blotter._live_orders, [])

    def test_process_current_order(self):
        mock_order = mock.Mock(status=OrderStatus.EXECUTABLE)
        mock_order.current_order.status = "EXECUTION_COMPLETE"
        mock_current_order = mock.Mock()
        mock_log_control = mock.Mock()
        process.process_current_order(mock_order, mock_current_order, mock_log_control)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.execution_complete.assert_called()

    @mock.patch("flumine.order.process.OrderEvent")
    def test_process_current_order_async(self, mock_order_event):
        mock_order = mock.Mock(status=OrderStatus.EXECUTABLE, async_=True, bet_id=None)
        mock_order.current_order.status = "EXECUTION_COMPLETE"
        mock_current_order = mock.Mock(bet_id=1234)
        mock_log_control = mock.Mock()
        process.process_current_order(mock_order, mock_current_order, mock_log_control)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.execution_complete.assert_called()
        self.assertEqual(mock_order.bet_id, 1234)
        mock_order.responses.placed.assert_called_with()
        mock_order_event.assert_called_with(mock_order, exchange=mock_order.EXCHANGE)
        mock_log_control.assert_called_with(mock_order_event())

    def test_create_order_from_current(self):
        mock_add_market = mock.Mock()
        market_book = mock.Mock()
        mock_client = mock.Mock()
        mock_flumine = mock.Mock()
        markets = Markets()
        market = Market(
            flumine=mock.Mock(), market_id="market_id", market_book=market_book
        )
        markets.add_market("market_id", market)
        cheap_hash = create_cheap_hash("strategy_name", 13)
        strategy = mock.Mock(name_hash=cheap_hash)
        strategies = Strategies()
        strategies(strategy=strategy, clients=mock.Mock(), flumine=mock_flumine)
        current_order = mock.Mock(
            customer_order_ref=f"{cheap_hash}I123",
            market_id="market_id",
            bet_id=None,
            selection_id="selection_id",
            handicap="handicap",
            order_type="LIMIT",
            price_size=PriceSize(price=10.0, size=2.0),
            persistence_type="LAPSE",
        )

        new_order = process.create_order_from_current(
            markets=markets,
            strategies=strategies,
            current_order=current_order,
            add_market=mock_add_market,
            client=mock_client,
        )
        self.assertEqual(market.blotter["123"], new_order)
        self.assertEqual(new_order.market_id, "market_id")
        self.assertEqual(new_order.selection_id, "selection_id")
        self.assertEqual(new_order.handicap, "handicap")
        self.assertEqual(new_order.order_type.ORDER_TYPE, OrderTypes.LIMIT)
        self.assertEqual(new_order.order_type.size, 2.0)
        self.assertEqual(new_order.order_type.price, 10.0)
        self.assertEqual(new_order.client, mock_client)

    @mock.patch("flumine.order.process.process_betdaq_current_order")
    def test_process_betdaq_current_orders(self, mock_process_betdaq_current_order):
        mock_log_control = mock.Mock()
        mock_add_market = mock.Mock()
        market_book = mock.Mock()
        markets = Markets()
        market = Market(
            flumine=mock.Mock(), market_id="market_id", market_book=market_book
        )
        markets.add_market("market_id", market)
        strategies = Strategies()
        cheap_hash = create_cheap_hash("strategy_name", 13)
        trade = mock.Mock(market_id="market_id")
        trade.strategy.name_hash = cheap_hash
        current_order = mock.Mock(
            customer_order_ref=f"{cheap_hash}I123", market_id="market_id", bet_id=None
        )
        current_order = {"order_id": 456, "customer_reference": 123}
        betdaq_order = BetdaqOrder(trade=trade, side="BACK", order_type=mock.Mock())
        betdaq_order.id = "123"
        betdaq_order.complete = True
        market.blotter["123"] = betdaq_order
        event = mock.Mock(event=[current_order])

        process.process_betdaq_current_orders(
            markets=markets,
            strategies=strategies,
            event=event,
            log_control=mock_log_control,
            add_market=mock_add_market,
        )
        mock_process_betdaq_current_order.assert_called_with(
            betdaq_order, current_order
        )
        self.assertEqual(market.blotter._live_orders, [])

    def test_process_betdaq_current_order_pending(self):
        mock_order = mock.Mock(
            bet_id=123,
            status=OrderStatus.PENDING,
            current_order={"status": "Unmatched"},
        )
        mock_current_order = mock.Mock()
        process.process_betdaq_current_order(mock_order, mock_current_order)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.executable.assert_called()

    def test_process_betdaq_current_order_pending_matched(self):
        mock_order = mock.Mock(
            bet_id=123, status=OrderStatus.PENDING, current_order={"status": "Matched"}
        )
        mock_current_order = mock.Mock()
        process.process_betdaq_current_order(mock_order, mock_current_order)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.execution_complete.assert_called()

    def test_process_betdaq_current_order_matched(self):
        mock_order = mock.Mock(
            status=OrderStatus.EXECUTABLE, current_order={"status": "Matched"}
        )
        mock_current_order = mock.Mock()
        process.process_betdaq_current_order(mock_order, mock_current_order)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.execution_complete.assert_called()

    def test_process_betdaq_current_order_update(self):
        mock_order = mock.Mock(
            status=OrderStatus.UPDATING,
            current_order={"sequence_number": 1, "status": "Unmatched"},
        )
        mock_current_order = {"sequence_number": 2, "price": 999}
        process.process_betdaq_current_order(mock_order, mock_current_order)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.executable.assert_called()

    def test_process_betdaq_current_order_update_matched(self):
        mock_order = mock.Mock(
            status=OrderStatus.UPDATING,
            current_order={"sequence_number": 1, "status": "Matched"},
        )
        mock_current_order = {"sequence_number": 2, "price": 999, "status": "Matched"}
        process.process_betdaq_current_order(mock_order, mock_current_order)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.executable.assert_not_called()
        mock_order.execution_complete.assert_called()

    def test_process_betdaq_current_order_update_race(self):
        mock_order = mock.Mock(
            status=OrderStatus.UPDATING, current_order={"sequence_number": 1}
        )
        mock_current_order = {"sequence_number": 1}
        process.process_betdaq_current_order(mock_order, mock_current_order)
        mock_order.executable.assert_not_called()

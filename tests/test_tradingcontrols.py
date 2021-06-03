import unittest
from unittest import mock

from flumine.controls.tradingcontrols import (
    OrderValidation,
    StrategyExposure,
    OrderTypes,
    ExchangeType,
    OrderPackageType,
    MarketValidation,
)
from flumine.markets.blotter import Blotter


class TestOrderValidation(unittest.TestCase):
    def setUp(self):
        self.mock_flumine = mock.Mock()
        self.mock_client = mock.Mock()
        self.mock_client.min_bet_size = 2
        self.mock_client.min_bsp_liability = 10
        self.trading_control = OrderValidation(self.mock_flumine)

    def test_init(self):
        assert self.trading_control.NAME == "ORDER_VALIDATION"

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_order"
    )
    def test_validate_betfair(self, mock_validate_betfair_order):
        mock_order = mock.Mock()
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order.EXCHANGE = ExchangeType.BETFAIR
        mock_order.order_type.size = 12
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_validate_betfair_order.assert_called_with(mock_order)

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_min_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_price"
    )
    def test__validate_betfair_order_limit(
        self,
        mock__validate_betfair_price,
        mock__validate_betfair_size,
        mock__validate_betfair_min_size,
    ):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        self.trading_control._validate_betfair_order(order)
        mock__validate_betfair_price.assert_called_with(order)
        mock__validate_betfair_size.assert_called_with(order)
        mock__validate_betfair_min_size.assert_called_with(order, OrderTypes.LIMIT)

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_price"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_min_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_liability"
    )
    def test__validate_betfair_order_limit_on_close(
        self,
        mock__validate_betfair_liability,
        mock__validate_betfair_min_size,
        mock__validate_betfair_price,
    ):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        self.trading_control._validate_betfair_order(order)
        mock__validate_betfair_liability.assert_called_with(order)
        mock__validate_betfair_min_size.assert_called_with(
            order, OrderTypes.LIMIT_ON_CLOSE
        )
        mock__validate_betfair_price.assert_called_with(order)

    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_min_size"
    )
    @mock.patch(
        "flumine.controls.tradingcontrols.OrderValidation._validate_betfair_liability"
    )
    def test__validate_betfair_order_market_on_close(
        self, mock__validate_betfair_liability, mock__validate_betfair_min_size
    ):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        self.trading_control._validate_betfair_order(order)
        mock__validate_betfair_liability.assert_called_with(order)
        mock__validate_betfair_min_size.assert_called_with(
            order, OrderTypes.MARKET_ON_CLOSE
        )

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_order_unknown(self, mock_on_error):
        order = mock.Mock()
        order.order_type.ORDER_TYPE = "RUSH"
        self.trading_control._validate_betfair_order(order)
        mock_on_error.assert_called_with(order, "Unknown orderType")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = 2
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size_on_error(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = None
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_called_with(order, "Order size is None")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = -1
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_called_with(order, "Order size is less than 0")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_size_on_error_three(self, mock_on_error):
        order = mock.Mock()
        order.order_type.size = 1.999
        self.trading_control._validate_betfair_size(order)
        mock_on_error.assert_called_with(order, "Order size has more than 2dp")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_price(self, mock_on_error):
        order = mock.Mock()
        order.order_type.price = 2
        self.trading_control._validate_betfair_price(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_price_on_error(self, mock_on_error):
        order = mock.Mock()
        order.order_type.price = None
        self.trading_control._validate_betfair_price(order)
        mock_on_error.assert_called_with(order, "Order price is None")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_price_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.order_type.price = -1
        self.trading_control._validate_betfair_price(order)
        mock_on_error.assert_called_with(order, "Order price is not valid")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = 2
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability_on_error(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = None
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_called_with(order, "Order liability is None")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability_on_error_two(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = -1
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_called_with(order, "Order liability is less than 0")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_liability_on_error_three(self, mock_on_error):
        order = mock.Mock()
        order.order_type.liability = 2.999
        self.trading_control._validate_betfair_liability(order)
        mock_on_error.assert_called_with(order, "Order liability has more than 2dp")

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_no_validation(self, mock_on_error):
        self.mock_flumine.client.min_bet_validation = False
        order = mock.Mock(side="BACK")
        order.order_type.size = 0.01
        order.order_type.price = 2
        self.trading_control._validate_betfair_min_size(order, OrderTypes.LIMIT)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_limit(self, mock_on_error):
        self.mock_flumine.client.min_bet_size = 2
        self.mock_flumine.client.min_bet_payout = 10
        order = mock.Mock()
        order.side = "BACK"
        order.order_type.size = 2
        order.order_type.price = 2
        self.trading_control._validate_betfair_min_size(order, OrderTypes.LIMIT)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_limit_large(self, mock_on_error):
        self.mock_flumine.client.min_bet_size = 0.10
        self.mock_flumine.client.min_bet_payout = 100
        order = mock.Mock()
        order.side = "BACK"
        order.order_type.size = 2
        order.order_type.price = 2
        self.trading_control._validate_betfair_min_size(order, OrderTypes.LIMIT)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_limit_error(self, mock_on_error):
        self.mock_flumine.client.min_bet_size = 2
        self.mock_flumine.client.min_bet_payout = 10
        order = mock.Mock()
        order.side = "BACK"
        order.order_type.size = 1.99
        order.order_type.price = 2
        self.trading_control._validate_betfair_min_size(order, OrderTypes.LIMIT)
        mock_on_error.assert_called_with(
            order,
            "Order size is less than min bet size (2) or payout (10) for currency",
        )

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size(self, mock_on_error):
        self.mock_flumine.client.min_bet_size = 2
        order = mock.Mock()
        order.side = "BACK"
        order.order_type.liability = 2
        self.trading_control._validate_betfair_min_size(
            order, OrderTypes.LIMIT_ON_CLOSE
        )
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_two(self, mock_on_error):
        self.mock_flumine.client.min_bsp_liability = 10
        order = mock.Mock()
        order.side = "LAY"
        order.order_type.liability = 10
        self.trading_control._validate_betfair_min_size(
            order, OrderTypes.LIMIT_ON_CLOSE
        )
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_on_error(self, mock_on_error):
        self.mock_flumine.client.min_bet_size = 2
        order = mock.Mock()
        order.side = "BACK"
        order.order_type.liability = 1.99
        self.trading_control._validate_betfair_min_size(
            order, OrderTypes.LIMIT_ON_CLOSE
        )
        mock_on_error.assert_called_with(
            order, "Liability is less than min bet size (2) for currency"
        )

    @mock.patch("flumine.controls.tradingcontrols.OrderValidation._on_error")
    def test__validate_betfair_min_size_on_error_two(self, mock_on_error):
        self.mock_flumine.client.min_bsp_liability = 10
        order = mock.Mock()
        order.side = "LAY"
        order.order_type.liability = 9.99
        self.trading_control._validate_betfair_min_size(
            order, OrderTypes.LIMIT_ON_CLOSE
        )
        mock_on_error.assert_called_with(
            order, "Liability is less than min BSP payout (10) for currency"
        )


class TestMarketValidation(unittest.TestCase):
    def setUp(self):
        self.mock_market = mock.Mock(market_book=mock.Mock(status="OPEN"))
        self.mock_flumine = mock.Mock()
        self.mock_flumine.markets.markets = {"market_id": self.mock_market}
        self.trading_control = MarketValidation(self.mock_flumine)
        self.mock_order = mock.Mock()
        self.mock_order.market_id = "market_id"

    @mock.patch("flumine.controls.tradingcontrols.MarketValidation._on_error")
    def test__validate_betfair_market_status(self, mock_on_error):
        self.trading_control._validate_betfair_market_status(self.mock_order)
        mock_on_error.assert_not_called()
        self.mock_order.executable.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.MarketValidation._on_error")
    def test__validate_betfair_market_status_closed(self, mock_on_error):
        self.mock_market.market_book.status = "CLOSED"
        self.trading_control._validate_betfair_market_status(self.mock_order)
        mock_on_error.assert_called()
        self.mock_order.executable.assert_called()

    @mock.patch("flumine.controls.tradingcontrols.MarketValidation._on_error")
    def test__validate_betfair_market_status_suspended(self, mock_on_error):
        self.mock_market.market_book.status = "SUSPENDED"
        self.trading_control._validate_betfair_market_status(self.mock_order)
        mock_on_error.assert_called()
        self.mock_order.executable.assert_called()

    @mock.patch("flumine.controls.tradingcontrols.MarketValidation._on_error")
    def test__validate_betfair_market_not_found(self, mock_on_error):
        self.mock_flumine.markets.markets = {}
        self.trading_control._validate_betfair_market_status(self.mock_order)
        mock_on_error.assert_not_called()
        self.mock_order.executable.assert_not_called()


class TestStrategyExposure(unittest.TestCase):
    def setUp(self):
        self.market = mock.Mock()
        self.market.blotter = Blotter("market_id")
        self.mock_flumine = mock.Mock()
        self.mock_flumine.markets.markets = {"market_id": self.market}
        self.trading_control = StrategyExposure(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.trading_control.NAME, "STRATEGY_EXPOSURE")
        self.assertEqual(self.trading_control.flumine, self.mock_flumine)

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_strategy_validate_order(self, mock_on_error):
        mock_order = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        mock_order.trade.strategy.validate_order.return_value = True
        mock_runner_context = mock.Mock()
        mock_order.trade.strategy.get_runner_context.return_value = mock_runner_context
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_strategy_validate_order_error(self, mock_on_error):
        mock_order = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        mock_order.trade.strategy.validate_order.return_value = False
        mock_runner_context = mock.Mock()
        mock_order.trade.strategy.get_runner_context.return_value = mock_runner_context
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_called_with(
            mock_order,
            mock_order.violation_msg,
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_limit(self, mock_on_error):
        mock_order = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        mock_order.trade.strategy.max_order_exposure = 10
        mock_order.trade.strategy.max_selection_exposure = 100
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order.side = "BACK"
        mock_order.order_type.size = 12.0
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_called_with(
            mock_order,
            "Order exposure (12.0) is greater than strategy.max_order_exposure (10)",
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_limit_with_multiple_strategies_succeeds(self, mock_on_error):
        """
        The 2 orders would exceed selection_exposure limits if they were for the same strategy. But they are
        for different strategies. Assert that they do not cause a validation failure.
        """
        strategy = mock.Mock()
        strategy.max_order_exposure = 10
        strategy.max_selection_exposure = 10

        order1 = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        order1.trade.strategy.max_order_exposure = 10
        order1.trade.strategy.max_selection_exposure = 10
        order1.order_type.ORDER_TYPE = OrderTypes.LIMIT
        order1.side = "BACK"
        order1.order_type.price = 2.0
        order1.order_type.size = 9.0
        order1.size_remaining = 9.0
        order1.average_price_matched = 0.0
        order1.size_matched = 0

        order2 = mock.Mock(lookup=(1, 2, 3))
        order2.trade.strategy.max_order_exposure = 10
        order2.trade.strategy.max_selection_exposure = 10
        order2.trade.strategy = strategy
        order2.order_type.ORDER_TYPE = OrderTypes.LIMIT
        order2.side = "BACK"
        order2.order_type.price = 3.0
        order2.order_type.size = 9.0
        order2.size_remaining = 5.0
        order2.average_price_matched = 0.0
        order2.size_matched = 0

        self.market.blotter._orders = {"order1": order1, "order2": order2}

        self.trading_control._validate(order1, OrderPackageType.PLACE)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_limit_with_multiple_strategies_fails(self, mock_on_error):
        """
        The 2 orders are from the same strategy. And are each less than strategy.max_order_exposure.
        However, in combination, they exceed strategy.max_selection_exposure.
        """
        strategy = mock.Mock()
        strategy.max_order_exposure = 10
        strategy.max_selection_exposure = 10

        order1 = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        order1.trade.strategy = strategy
        order1.order_type.ORDER_TYPE = OrderTypes.LIMIT
        order1.side = "BACK"
        order1.order_type.price = 2.0
        order1.order_type.size = 9.0
        order1.size_remaining = 9.0
        order1.average_price_matched = 0.0
        order1.size_matched = 0

        order2 = mock.Mock(lookup=(1, 2, 3))
        order2.trade.strategy = strategy
        order2.order_type.ORDER_TYPE = OrderTypes.LIMIT
        order2.side = "BACK"
        order2.order_type.price = 3.0
        order2.order_type.size = 9.0
        order2.size_remaining = 5.0
        order2.average_price_matched = 0.0
        order2.size_matched = 0

        self.market.blotter["order2"] = order2

        self.trading_control._validate(order1, OrderPackageType.PLACE)
        self.assertEqual(1, mock_on_error.call_count)
        mock_on_error.assert_called_with(
            order1,
            "Potential selection exposure (14.00) is greater than strategy.max_selection_exposure (10)",
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_limit_on_close(self, mock_on_error):
        mock_order = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        mock_order.trade.strategy.max_order_exposure = 10
        mock_order.trade.strategy.max_selection_exposure = 100
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT_ON_CLOSE
        mock_order.side = "BACK"
        mock_order.order_type.liability = 12
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_called_with(
            mock_order,
            "Order exposure (12) is greater than strategy.max_order_exposure (10)",
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_market_on_close(self, mock_on_error):
        mock_market = mock.Mock()
        mock_market.blotter.selection_exposure.return_value = 10.0
        self.mock_flumine.markets.markets = {"1.234": mock_market}

        mock_order = mock.Mock(market_id="1.234", lookup=(1, 2, 3))
        mock_order.trade.strategy.max_order_exposure = 10
        mock_order.trade.strategy.max_selection_exposure = 100
        mock_order.order_type.ORDER_TYPE = OrderTypes.MARKET_ON_CLOSE
        mock_order.side = "BACK"
        mock_order.order_type.liability = 12
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_called_with(
            mock_order,
            "Order exposure (12) is greater than strategy.max_order_exposure (10)",
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_selection(self, mock_on_error):
        mock_market = mock.Mock()
        mock_market.blotter.get_exposures.return_value = {
            "worst_possible_profit_on_win": -12.0
        }
        self.mock_flumine.markets.markets = {"1.234": mock_market}
        mock_order = mock.Mock(market_id="1.234", lookup=(1, 2, 3), side="LAY")
        mock_order.trade.strategy.max_order_exposure = 10
        mock_order.trade.strategy.max_selection_exposure = 10
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order.order_type.size = 12.0
        mock_order.order_type.price = 1.01
        mock_market.blotter._live_orders = [mock_order]
        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_called_with(
            mock_order,
            "Potential selection exposure (12.12) is greater than strategy.max_selection_exposure (10)",
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_selection2a(self, mock_on_error):
        """
        test_validate_selection2a expects an error, as it attempts to place a lay bet with a £36 potential
        loss, which is more than the £10 max_selection_exposure
        """
        mock_market = mock.Mock()
        mock_market.blotter = Blotter(market_id="1.234")
        self.mock_flumine.markets.markets = {"1.234": mock_market}

        mock_strategy = mock.Mock()
        mock_strategy.max_order_exposure = 100
        mock_strategy.max_selection_exposure = 10

        mock_trade = mock.Mock()
        mock_trade.strategy = mock_strategy

        mock_order = mock.Mock(market_id="1.234", lookup=(1, 2, 3), side="LAY")
        mock_order.trade = mock_trade
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order.order_type.size = 9.0
        mock_order.order_type.price = 5.0

        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_called_with(
            mock_order,
            "Potential selection exposure (36.00) is greater than strategy.max_selection_exposure (10)",
        )

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_selection2b(self, mock_on_error):
        """
        test_validate_selection2b expects no error.
        Unlike test_validate_selection2a, the blotter contains an existing order. The order that it attempts
        to validate hedges the existing order, and reduces the total exposure.
        """
        mock_market = mock.Mock()
        mock_market.blotter = Blotter(market_id="1.234")

        self.mock_flumine.markets.markets = {"1.234": mock_market}

        mock_strategy = mock.Mock()
        mock_strategy.max_order_exposure = 100
        mock_strategy.max_selection_exposure = 10

        mock_trade = mock.Mock()
        mock_trade.strategy = mock_strategy

        existing_matched_order = mock.Mock(
            market_id="1.234", lookup=(1, 2, 3), side="BACK"
        )
        existing_matched_order.trade = mock_trade
        existing_matched_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        existing_matched_order.size_matched = 9.0
        existing_matched_order.average_price_matched = 6.0
        existing_matched_order.size_remaining = 0.0

        mock_order = mock.Mock(market_id="1.234", lookup=(1, 2, 3), side="LAY")
        mock_order.trade = mock_trade
        mock_order.order_type.ORDER_TYPE = OrderTypes.LIMIT
        mock_order.order_type.size = 9.0
        mock_order.order_type.price = 5.0

        mock_market.blotter["existing_order"] = existing_matched_order

        self.trading_control._validate(mock_order, OrderPackageType.PLACE)
        mock_on_error.assert_not_called()

    @mock.patch("flumine.controls.tradingcontrols.StrategyExposure._on_error")
    def test_validate_replace(self, mock_on_error):
        """
        Check that validating a REPLACE order does not lead to double counting of exposures.

        In this test, max_selection_exposure is 10.0, and the potential liability on the order is £9.
        If exposures are double counted, the validation would fail.
        If exposures aren't double counted, then the validation will succeed
        """

        strategy = mock.Mock()
        strategy.max_order_exposure = 10
        strategy.max_selection_exposure = 10

        order1 = mock.Mock(market_id="market_id", lookup=(1, 2, 3))
        order1.trade.strategy = strategy
        order1.order_type.ORDER_TYPE = OrderTypes.LIMIT
        order1.side = "BACK"
        order1.order_type.price = 2.0
        order1.order_type.size = 9.0
        order1.size_remaining = 9.0
        order1.average_price_matched = 0.0
        order1.size_matched = 0
        order1.selection_id = 1234
        order1.handicap = 0

        self.market.blotter._strategy_selection_orders = {(strategy, 2, 3): [order1]}

        # Show that the exposures aren't double counted when REPLACE is used
        self.trading_control._validate(order1, OrderPackageType.REPLACE)
        mock_on_error.assert_not_called()

        # Just to be sure, check that the validation fails if we try to validate order1 as a PLACE
        self.trading_control._validate(order1, OrderPackageType.PLACE)
        mock_on_error.assert_called_once()

import logging
from collections import defaultdict
from betfairlightweight.resources.bettingresources import RunnerBook

from ..order.order import OrderStatus
from ..utils import get_price

logger = logging.getLogger(__name__)


class Middleware:
    def __call__(self, market) -> None:
        raise NotImplementedError


class SimulatedMiddleware(Middleware):
    """
    Calculates matched amounts per runner
    to be used in simulated matching.
    # todo runner removal fucks everything
    # todo currency fluctuations fucks everything
    """

    def __init__(self):
        # {marketId: {(selectionId, handicap): RunnerAnalytics}}
        self.markets = defaultdict(dict)

    def __call__(self, market) -> None:
        market_analytics = self.markets[market.market_id]
        for runner in market.market_book.runners:
            if runner.status == "ACTIVE":
                self._process_runner(market_analytics, runner)
        market.context["simulated"] = market_analytics
        # process simulated orders
        self._process_simulated_orders(market, market_analytics)

    @staticmethod
    def _process_simulated_orders(market, market_analytics: dict) -> None:
        for order in market.blotter.live_orders:
            if order.simulated and order.status == OrderStatus.EXECUTABLE:
                runner_analytics = market_analytics.get(
                    (order.selection_id, order.handicap)
                )
                order.simulated(market.market_book, runner_analytics)

    @staticmethod
    def _process_runner(market_analytics: dict, runner: RunnerBook) -> None:
        try:
            runner_analytics = market_analytics[(runner.selection_id, runner.handicap)]
        except KeyError:
            runner_analytics = market_analytics[
                (runner.selection_id, runner.handicap)
            ] = RunnerAnalytics(runner)
        runner_analytics(runner)


class RunnerAnalytics:
    def __init__(self, runner: RunnerBook):
        self._runner = runner
        self.traded = {}
        self.middle = None  # middle of odds at last event
        self._traded_volume = runner.ex.traded_volume

    def __call__(self, runner: RunnerBook):
        self.middle = self._calculate_middle(self._runner)  # use last event
        self.traded = self._calculate_traded(runner)
        self._traded_volume = runner.ex.traded_volume
        self._runner = runner

    def _calculate_traded(self, runner: RunnerBook) -> dict:
        if self._traded_volume == runner.ex.traded_volume:
            return {}
        else:
            c_v, p_v, traded = {}, {}, {}
            # create dictionaries
            for i in runner.ex.traded_volume:
                c_v[i["price"]] = i["size"]
            for i in self._traded_volume:
                p_v[i["price"]] = i["size"]
            # calculate difference
            for key in c_v.keys():
                if key in p_v:
                    new_value = float(c_v[key]) - float(p_v[key])
                else:
                    new_value = float(c_v[key])
                if new_value > 0:
                    new_value = round(new_value, 2)
                    traded[key] = new_value
            return traded

    @staticmethod
    def _calculate_middle(runner: RunnerBook) -> float:
        back = get_price(runner.ex.available_to_back, 0) or 0
        lay = get_price(runner.ex.available_to_lay, 0) or 1001
        return (float(back) + float(lay)) / 2

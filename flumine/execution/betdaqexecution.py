import logging
import requests
from typing import Callable
from betdaq import BetdaqError

from ..clients import ExchangeType
from .baseexecution import BaseExecution
from ..order.order import BaseOrder
from ..order.orderpackage import BaseOrderPackage, OrderPackageType
from ..events.events import OrderEvent

logger = logging.getLogger(__name__)


class BetdaqExecution(BaseExecution):
    """
    BETDAQ execution for place, cancel and update, default
    single thread pool:

    'A Punter can not issue more than one order API (PlaceSimgleOrder,
    PlaceGroupOrder or ChangeOrder) at the same time'
    """

    EXCHANGE = ExchangeType.BETDAQ

    def execute_place(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.place, order_package)
        if response:
            for order, instruction_report in zip(order_package, response):
                with order.trade:
                    self._order_logger(
                        order, instruction_report, OrderPackageType.PLACE
                    )
                    if not instruction_report["return_code"]:
                        if int(order.id) != instruction_report["customer_reference"]:
                            logger.critical(
                                "Order id / ref missmatch",
                                extra={
                                    "order_id": int(order.id),
                                    "customer_reference": instruction_report[
                                        "customer_reference"
                                    ],
                                    "response": instruction_report,
                                },
                            )
                            continue
                        order.executable()  # let process.py pick it up
                    else:
                        logger.critical(
                            "Order error return code",
                            extra={
                                "order_id": int(order.id),
                                "return_code": instruction_report["return_code"],
                                "response": instruction_report,
                            },
                        )
                        order.execution_complete()
            # todo update transaction counts

    def place(self, order_package: BaseOrderPackage):
        return order_package.client.betting_client.betting.place_orders(
            order_list=order_package.place_instructions
        )

    def execute_cancel(
        self, order_package: BaseOrderPackage, http_session: requests.Session
    ) -> None:
        response = self._execution_helper(self.cancel, order_package)
        if response:
            for order, instruction_report in zip(order_package, response):
                with order.trade:
                    self._order_logger(
                        order, instruction_report, OrderPackageType.PLACE
                    )
                    if int(order.id) != instruction_report["customer_reference"]:
                        logger.critical(
                            "Order id / ref missmatch",
                            extra={
                                "order_id": int(order.id),
                                "customer_reference": instruction_report[
                                    "customer_reference"
                                ],
                                "response": instruction_report,
                            },
                        )
                        continue

                    order.execution_complete()

    def cancel(self, order_package: BaseOrderPackage):
        return order_package.client.betting_client.betting.cancel_orders(
            order_ids=order_package.cancel_instructions
        )

    def _execution_helper(
        self,
        trading_function: Callable,
        order_package: BaseOrderPackage,
    ):
        try:
            response = trading_function(order_package)
        except BetdaqError as e:
            logger.error(
                "Execution error",
                extra={
                    "trading_function": trading_function.__name__,
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        except Exception as e:
            logger.critical(
                "Execution unknown error",
                extra={
                    "trading_function": trading_function.__name__,
                    "response": e,
                    "order_package": order_package.info,
                },
                exc_info=True,
            )
            return
        logger.info(
            f"execute_{trading_function.__name__}",
            extra={
                "trading_function": trading_function.__name__,
                "response": response,
                "order_package": order_package.info,
            },
        )
        return response

    def _order_logger(
        self, order: BaseOrder, instruction_report: dict, package_type: OrderPackageType
    ):
        logger.info(
            "Order %s: %s",
            package_type.value,
            instruction_report.get("return_code"),
            extra={
                "bet_id": order.bet_id,
                "order_id": order.id,
                "return_code": instruction_report.get("return_code"),
            },
        )
        if package_type == OrderPackageType.PLACE:
            dt = False if order.async_ and not order.simulated else True
            order.responses.placed(instruction_report, dt=dt)
            if instruction_report["order_id"]:
                order.bet_id = instruction_report["order_id"]
                self.flumine.log_control(OrderEvent(order, exchange=order.EXCHANGE))
        elif package_type == OrderPackageType.CANCEL:
            order.responses.cancelled(instruction_report)
        elif package_type == OrderPackageType.UPDATE:
            order.responses.updated(instruction_report)
        elif package_type == OrderPackageType.REPLACE:
            order.responses.placed(instruction_report)
            order.bet_id = instruction_report["order_id"]
            self.flumine.log_control(OrderEvent(order, exchange=order.EXCHANGE))

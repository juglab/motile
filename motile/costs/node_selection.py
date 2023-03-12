from __future__ import annotations

from typing import TYPE_CHECKING

from ..variables import NodeSelected
from .costs import Costs
from .weight import Weight

if TYPE_CHECKING:
    from motile.solver import Solver


class NodeSelection(Costs):
    """Costs for :class:`motile.variables.NodeSelected` variables.

    Args:

        weight (float):
            The weight to apply to the cost given by the ``costs`` attribute of
            each node.

        attribute (string):
            The name of the node attribute to use to look up costs. Default is
            ``costs``.

        constant (float):
            A constant cost for each selected node.
    """

    def __init__(
        self, weight: float, attribute: str = "costs", constant: float = 0.0
    ) -> None:
        self.weight = Weight(weight)
        self.constant = Weight(constant)
        self.attribute = attribute

    def apply(self, solver: Solver) -> None:

        node_variables = solver.get_variables(NodeSelected)

        for node, index in node_variables.items():

            solver.add_variable_cost(
                index,
                solver.graph.nodes[node][self.attribute],
                self.weight)
            solver.add_variable_cost(
                index,
                1.0,
                self.constant)

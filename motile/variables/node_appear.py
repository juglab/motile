from __future__ import annotations

from typing import TYPE_CHECKING, Collection, Iterable

import ilpy

from .edge_selected import EdgeSelected
from .node_selected import NodeSelected
from .variable import Variable

if TYPE_CHECKING:
    from motile._types import NodeId
    from motile.solver import Solver


class NodeAppear(Variable["NodeId"]):
    r"""A binary variable for each node that indicates whether the node is the
    start of a track (i.e., the node is selected and has no selected incoming
    edges).

    This variable is coupled to the node and edge selection variables through
    the following linear constraints:

    .. math::

        |\\text{in_edges}(v)|\cdot x_v - &\sum_{e \in \\text{in_edges}(v)} x_e
        - a_v &\leq&\;\; |\\text{in_edges}(v)| - 1

        |\\text{in_edges}(v)|\cdot x_v - &\sum_{e \in \\text{in_edges}(v)} x_e
        - a_v\cdot |\\text{in_edges}(v)| &\geq&\;\; 0

    where :math:`x_v` and :math:`x_e` are selection indicators for node
    :math:`v` and edge :math:`e`, and :math:`a_v` is the appear indicator for
    node :math:`v`.
    """

    @staticmethod
    def instantiate(solver: Solver) -> Collection[NodeId]:
        return solver.graph.nodes

    @staticmethod
    def instantiate_constraints(solver: Solver) -> Iterable[ilpy.LinearConstraint]:
        appear_indicators = solver.get_variables(NodeAppear)
        node_indicators = solver.get_variables(NodeSelected)
        edge_indicators = solver.get_variables(EdgeSelected)

        for node in solver.graph.nodes:
            prev_edges = solver.graph.prev_edges[node]
            num_prev_edges = len(prev_edges)

            if num_prev_edges == 0:
                # special case: no incoming edges, appear indicator is equal to
                # selection indicator
                constraint = ilpy.LinearConstraint()
                constraint.set_coefficient(node_indicators[node], 1.0)
                constraint.set_coefficient(appear_indicators[node], -1.0)
                constraint.set_relation(ilpy.Relation.Equal)
                constraint.set_value(0.0)

                yield constraint

                continue

            # Ensure that the following holds:
            #
            # appear = 1 <=> sum(prev_selected) = 0 and selected
            # appear = 0 <=> sum(prev_selected) > 0 or not selected
            #
            # Two linear constraints are needed for that:
            #
            # let s = num_prev * selected - sum(prev_selected)
            # (1) s - appear <= num_prev - 1
            # (2) s - appear * num_prev >= 0

            constraint1 = ilpy.LinearConstraint()
            constraint2 = ilpy.LinearConstraint()

            # set s for both constraints:

            # num_prev * selected
            constraint1.set_coefficient(node_indicators[node], num_prev_edges)
            constraint2.set_coefficient(node_indicators[node], num_prev_edges)

            # - sum(prev_selected)
            for prev_edge in prev_edges:
                constraint1.set_coefficient(edge_indicators[prev_edge], -1.0)
                constraint2.set_coefficient(edge_indicators[prev_edge], -1.0)

            # constraint specific parts:

            # - appear
            constraint1.set_coefficient(appear_indicators[node], -1.0)

            # - appear * num_prev
            constraint2.set_coefficient(appear_indicators[node], -num_prev_edges)

            constraint1.set_relation(ilpy.Relation.LessEqual)
            constraint2.set_relation(ilpy.Relation.GreaterEqual)

            constraint1.set_value(num_prev_edges - 1)
            constraint2.set_value(0)

            yield constraint1
            yield constraint2

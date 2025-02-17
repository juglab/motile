import numpy as np

try:
    import plotly.graph_objects as go
except ImportError as e:
    raise ImportError(
        "This functionality requires the plotly package. Please install plotly."
    ) from e

from .variables import EdgeSelected, NodeSelected


def draw_track_graph(
    graph,
    position_attribute=None,
    position_func=None,
    alpha_attribute=None,
    alpha_func=None,
    label_attribute=None,
    label_func=None,
    node_size=20,
    node_color=(127, 30, 121),
    edge_color=(127, 30, 121),
    width=660,
    height=400,
):
    """Create a plotly figure showing the given graph, with time on the x-axis
    and node positions on the y-axis.

    Args:

        graph (:class:`TrackGraph`):
            The graph to plot.

        position_attribute (``string``):
            The name of the node attribute to use to place nodes on the y-axis.

        position_func (callable):
            A function returning the position of a given node on the y-axis.

        alpha_attribute (``string``):
            The name of a node or edge attribute to use for the transparency.

        alpha_func (callable):
            A function returning the alpha value to use for each node or edge.
            Can be a tuple for node and edge functions, respectively.

        label_attribute (``string``):
            The name of a node or edge attribute to use for a text label.

        label_func (callable):
            A function returning the label to use for each node or edge. Can be
            a tuple for node and edge functions, respectively.

        node_size (``float``):
            The size of nodes.

        node_color, edge_color (``tuple`` of ``int``):
            The RGB color to use for nodes and edges.

        width, height (``int``):
            The width and height of the plot, in pixels. Default: 700 x 400.

    Returns:

        ``plotly`` figure showing the graph.
    """

    if position_attribute is not None and position_func is not None:
        raise RuntimeError(
            "Only one of position_attribute and position_func can be given"
        )

    if position_attribute is None:
        position_attribute = "x"

    if position_func is None:

        def position_func(node):
            return graph.nodes[node][position_attribute]

    if alpha_attribute is not None and alpha_func is not None:
        raise RuntimeError("Only one of alpha_attribute and alpha_func can be given")

    if alpha_attribute is not None:

        def alpha_node_func(node):
            return graph.nodes[node].get(alpha_attribute, 1.0)

        def alpha_edge_func(edge):
            return graph.edges[edge].get(alpha_attribute, 1.0)

    elif alpha_func is None:

        def alpha_node_func(_):
            return 1.0

        def alpha_edge_func(_):
            return 1.0

    else:
        try:
            alpha_node_func, alpha_edge_func = alpha_func
        except TypeError:
            alpha_node_func = alpha_func
            alpha_edge_func = alpha_func

    if label_attribute is not None and label_func is not None:
        raise RuntimeError("Only one of label_attribute and label_func can be given")

    if label_attribute is not None:

        def label_node_func(node):
            return graph.nodes[node].get(label_attribute, "")

        def label_edge_func(edge):
            return graph.edges[edge].get(label_attribute, "")

    elif label_func is None:

        def label_node_func(node):
            return str(node)

        def label_edge_func(edge):
            return str(edge)

    else:
        try:
            label_node_func, label_edge_func = label_func
        except TypeError:
            label_node_func = label_func
            label_edge_func = label_func

    frame_attribute = graph.frame_attribute
    frames = list(range(*graph.get_frames()))

    node_positions = np.asarray(
        [
            (attrs[frame_attribute], position_func(node))
            for node, attrs in graph.nodes.items()
        ]
    )
    node_alphas = [alpha_node_func(node) for node in graph.nodes]
    edge_alphas = [alpha_edge_func(edge) for edge in graph.edges]
    # can be a list for different colors per node/edge
    node_colors = to_rgba(node_color, node_alphas)
    edge_colors = to_rgba(edge_color, edge_alphas)

    node_labels = [str(label_node_func(node)) for node in graph.nodes]
    edge_labels = [str(label_edge_func(edge)) for edge in graph.edges]

    def attr_hover_text(attrs):
        return "<br>".join([f"{name}: {value}" for name, value in attrs.items()])

    fig = go.Figure()

    node_trace = go.Scatter(
        x=node_positions[:, 0],
        y=node_positions[:, 1],
        mode="markers+text",
        marker={"color": node_colors, "size": 30},
        text=node_labels,
        textfont={"color": "white"},
        hoverinfo="text",
        hovertext=[attr_hover_text(attrs) for attrs in graph.nodes.values()],
    )

    fig.add_trace(node_trace)

    fig.update_layout(
        xaxis={
            "tickmode": "linear",
            "tick0": min(frames),
            "dtick": 1,
            "title": "time",
        },
        yaxis={
            "title": "space",
        },
        showlegend=False,
        margin={
            "t": 0,
            "b": 0,
            "l": 0,
            "r": 0,
        },
        modebar={
            "remove": [
                "lasso",
                "pan",
                "select",
                "autoscale",
                "zoomin",
                "zoomout",
                "resetscale",
            ]
        },
        width=width,
        height=height,
    )

    arrows = []
    for ((u, v), attrs), label, color in zip(
        graph.edges.items(), edge_labels, edge_colors
    ):
        start = node_positions[u, (0, 1)]
        end = node_positions[v, (0, 1)]
        mid = 0.6 * start + 0.4 * end
        first_half = go.layout.Annotation(
            dict(
                ax=start[0],
                ay=start[1],
                x=mid[0],
                y=mid[1],
                xref="x",
                yref="y",
                showarrow=True,
                startstandoff=node_size / 2,
                axref="x",
                ayref="y",
                arrowhead=0,
                arrowwidth=4,
                arrowcolor=color,
            )
        )
        second_half = go.layout.Annotation(
            dict(
                ax=mid[0],
                ay=mid[1],
                x=end[0],
                y=end[1],
                xref="x",
                yref="y",
                text=label,
                font={"color": "white"},
                hovertext=attr_hover_text(attrs),
                bgcolor=color,
                showarrow=True,
                standoff=node_size * 0.8,
                axref="x",
                ayref="y",
                arrowhead=2,
                arrowwidth=4,
                arrowsize=0.6,
                arrowcolor=color,
            )
        )

        arrows.append(first_half)
        arrows.append(second_half)

    fig.update_layout(annotations=arrows)

    return fig


def draw_solution(graph, solver, *args, **kwargs):
    """Wrapper around :func:`draw_track_graph` highlighting the solution found
    by the given solver.

    Args:

        graph (:class:`TrackGraph`):
            The graph to plot.

        solver :class:`Solver`):
            The solver that was used to find the solution.

        args, kwargs:
            Pass-through arguments to :func:`draw_track_graph`.

    Returns:

        ``plotly`` figure showing the graph.
    """

    solution = solver.solution
    node_indicators = solver.get_variables(NodeSelected)
    edge_indicators = solver.get_variables(EdgeSelected)

    def node_alpha_func(node):
        return solution[node_indicators[node]]

    def edge_alpha_func(edge):
        return solution[edge_indicators[edge]]

    kwargs["alpha_func"] = (node_alpha_func, edge_alpha_func)
    return draw_track_graph(graph, *args, **kwargs)


def to_rgba(color, alpha=1.0):
    if isinstance(color, list):
        if isinstance(alpha, list):
            return [to_rgba(c, a) for c, a in zip(color, alpha)]
        else:  # only color is list
            return [to_rgba(c, alpha) for c in color]
    elif isinstance(alpha, list):  # only alpha is list
        return [to_rgba(color, a) for a in alpha]

    # we fake alpha by mixing with white(ish)
    # transparancy is tricky...
    color = tuple(int(c * alpha + 220 * (1.0 - alpha)) for c in color)
    return f"rgb({color[0]},{color[1]},{color[2]})"

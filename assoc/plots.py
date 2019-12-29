import numpy as np
import networkx as nx
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.offsetbox import OffsetImage, AnnotationBbox, OffsetBox, DrawingArea
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from assoc.definitions import sprout

def sprout_plot(n, k, figsize=(10, 10), width=2, plot_trees=False):
  """Plots the boundary of a given n-sprout, with units injected at
  position specified by a list k."""
  fig, ax = plt.subplots(1, 1, figsize=figsize)

  # setup points and edges
  hierarchy = sprout(n, k).hierarchy() # full hierarchy for an n,[k]-sprout
  level = n + len(k) - 3               # level containing edges
  edges = hierarchy.level(level)       # list of edges

  # setup graph
  gph = nx.DiGraph()
  for left, right in edges:
    gph.add_edge(left, right)

  # layout nodes
  pos = nx.drawing.nx_agraph.graphviz_layout(gph, prog='dot')

  if plot_trees:
    # if we wish to plot edges as trees:
    for node in gph.nodes:
      coords = pos[node]
      box = AnnotationBbox(
        OffsetImage(render_tree(node), zoom=0.1, interpolation="bilinear"),
        coords, xycoords='data', frameon=False
      )
      ax.add_artist(box)
  else:
    # otherwise plot edges as their corresponding expression:
    labels = {
      node : f"${node}$"
      for node in gph.nodes
    }
    nx.draw_networkx_labels(gph, labels=labels, pos=pos, ax=ax)
  nx.draw(gph, pos=pos, node_color="w", node_size=20000, ax=ax, arrows=True, width=width)
  return fig, ax

def tree_plot(tree, ax=None, title_size=24, width=10):
  """Plots a tree object as the corresponding tree. Unit edges are marked in red."""
  fig = None
  if ax is None:
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

  # extract nodes and edges from the tree:
  edges = tree.edges()
  nodes = list(set([node for edge in edges for node in edge[:2]]))
  node_color = ["k" if node >= 0 else "r" for node in nodes]

  # setup directed graph:
  gph = nx.DiGraph()
  for node in nodes:
    gph.add_node(node)
  for left, right, label in edges:
    gph.add_edge(left, right, label=label)

  # layout and plot the tree:
  edge_color = ["k" if gph.edges[edge]["label"] >= 0 else "r" for edge in gph.edges]
  pos = nx.drawing.nx_agraph.graphviz_layout(gph, prog='dot')

  # flip the tree:
  pos = {
    key : (pos[key][0], -pos[key][1])
    for key in pos
  }

  nx.draw(gph, pos=pos, nodes=nodes, edge_color=edge_color,
          node_color=node_color, width=width, node_size=10 * (width - 1),
          ax=ax, arrows=False)
  ax.set_title(f"${tree}$", fontsize=title_size)
  plt.tight_layout()
  return fig, ax

def render_tree(tree, width=30):
  """Renders a tree object to numpy array, to allow for labelling nodes
  in plots by actual images of trees in a hacky way."""
  fig = Figure(figsize=(10, 10))
  canvas = FigureCanvas(fig)
  ax = fig.gca()
  tree_plot(tree, ax=ax, title_size=100, width=width)
  ax.axis('off')
  ax.patch.set_alpha(0.0)
  canvas.draw() # draw the canvas, cache the renderer
  s, (width, height) = canvas.print_to_buffer()
  image = np.fromstring(s, dtype='uint8')
  return image.reshape(height, width, 4)

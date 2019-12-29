from copy import copy

def sub(tup, data, index):
  result = list(tup)
  result[index] = data
  return list(result)

def unpack(x):
  if not isinstance(x, list):
    return [x]
  result = []
  for item in x:
    result += unpack(item)
  return result

# Nodes and Hierarchies of morphisms

memory = {}
hierarchy_memory = {}

class Hierarchy:
  """Hierarchy of boundaries for a given tree."""
  def __init__(self, data):
    """You should not construct a Hierarchy explicitly."""
    self.items = data[:-1]
    self.lower = []
    if data:
      self.lower = [
        Hierarchy(sub)
        for sub in data[-1]
      ]

  def level(self, depth):
    """Extracts all boundary elements at a given depth in the Hierarchy."""
    if depth == 0:
      return [self.items]
    result = []
    for lower in self.lower:
      result += lower.level(depth - 1)
    return result

class ImmutableNode(tuple):
  """Node of a tree representing a face inside a monoidahedron.

  This is effectively a thin wrapper around a tuple, fitted with
  some extra functionality for implementing helper functions
  and a derivation on trees giving the trees making up the boundary
  of the face given by a particular tree.
  """
  def __repr__(self):
    count = [-1]
    return self._repr_aux(count)

  def _repr_aux(self, count):
    r"""Represents a tree by its corresponding expression, e.g.:

    The tree:

    \/  /
     \ /
      |

    by the expression:

    ((ab)c)
    """
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    if len(self) == 0:
      count[0] += 1
      return alphabet[count[0]]
    inner = []
    for child in self:
      child_repr = None
      if isinstance(child, ImmutableNode):
        child_repr = child._repr_aux(count)
      else:
        child_repr = repr(child)
      inner.append(child_repr)
    inner = "".join(inner)
    return f"({inner})"

  @property
  def arity(self):
    """Number of children of a node."""
    return len(self)

  def edges(self, count=0):
    """Returns the edges of a given tree as a directed graph."""
    my_count = count
    edges = []
    for child in self:
      count += 1
      if not isinstance(child, ImmutableNode):
        edges.append((my_count, count, -1))
        continue
      edges.append((my_count, count, 1))
      addition, count = child.edges(count=count)
      edges += addition
    if my_count == 0:
      return edges
    return edges, count

  def normal_boundary(self):
    """Returns all trees containing which reduce to the given tree
    by contraction of a single edge. One rule of the derivation for monoidahedra,
    see Example 1 in the notes on monoidahedra and the bar construction
    by Todd Trimble."""
    if self in memory:
      return memory[self]

    result = []
    for idx in range(self.arity):
      prefix = self[:idx]
      for idy in range(idx + 1, self.arity):
        if idy + 1 - idx >= self.arity:
          continue
        expanded = self[idx:idy + 1]
        suffix = self[idy + 1:]
        result.append(
          ImmutableNode(prefix + (ImmutableNode(expanded),) + suffix)
        )
    for idx, child in enumerate(self):
      if not isinstance(child, ImmutableNode):
        continue
      partitions = child.normal_boundary()
      children = tuple(self)
      result += [
        ImmutableNode(sub(children, subpartition, idx))
        for subpartition in partitions
      ]

    memory[self] = result
    return result

  def unit_reduce(self):
    """Recursively remove units."""
    if self.arity == 0:
      return self
    if self.arity == 1 and self[0] == 1:
      return self
    if self.arity == 1 and self[0] != -1:
      return self[0]
    if self.arity == 1 and self[0] == -1:
      return None
    new_children = []
    for child in self:
      if isinstance(child, ImmutableNode):
        reduction = child.unit_reduce()
        if reduction is not None:
          new_children.append(reduction)
      else:
        if child is not None:
          new_children.append(child)
    if len(new_children) == 1:
      return new_children[0]
    result = ImmutableNode(new_children)
    return result

  def unit_elim(self):
    r"""Returns all trees, if any, obtainable by eliminating all left
    and right unitors, e.g.:
    expanding $\rho_x \otimes id_y$ to $id_x \otimes id_y$
    Another rule of the derivation for monoidahedra, to handle
    unit laws correctly."""
    new_children = []
    if self.arity == 2:
      for idx, child in enumerate(self):
        if isinstance(child, ImmutableNode):
          new_children.append(child.unit_elim())
      if not new_children and len(self) != 0:
        new_children = [-1]
    else:
      for child in self:
        elim = child
        if isinstance(child, ImmutableNode):
          elim = child.unit_elim()
        new_children.append(elim)
    result = ImmutableNode(new_children)
    return result.unit_reduce()

  def unit_expand(self):
    r"""Returns all trees, if any, obtainable by expanding all unitors
    to n-sprouts with attached units, e.g.:
    expanding $\rho_x \otimes id_y$ to $(id_x \otimes 1) \otimes id_y$
    Another rule of the derivation for monoidahedra, to handle
    unit laws correctly.
    """
    if self.arity == 1:
      return self
    new_children = []
    for idx, child in enumerate(self):
      if isinstance(child, ImmutableNode):
        if child.arity == 1:
          expanded = child
        else:
          expanded = child.unit_expand()
      else:
        expanded = ImmutableNode([child])
      new_children.append(expanded)
    expanded = ImmutableNode(new_children)
    return expanded

  def unit_boundary(self):
    """Combined rule to handle unit laws."""
    expansion = self.unit_expand()
    if expansion != self:
      expansion = [expansion]
    else:
      expansion = []
    reduction = self.unit_elim()
    if reduction != self:
      reduction = [reduction]
    else:
      reduction = []
    return expansion + reduction

  def boundary(self):
    """Derivation on trees representing monoidahedra."""
    result = []
    result += self.normal_boundary()
    result += self.unit_boundary()
    return result

  def hierarchy_aux(self):
    if self in hierarchy_memory:
      return hierarchy_memory[self]
    boundary = self.boundary()
    if len(boundary) == 0:
      return boundary
    result = list(boundary)
    faces = []
    for face in boundary:
      hierarchy = face.hierarchy_aux()
      if hierarchy:
        faces.append(hierarchy)
    result.append(faces)
    hierarchy_memory[self] = copy(result)
    return result

  def hierarchy(self):
    """Computes a hierarchy of boundaries of a given tree."""
    return Hierarchy(self.hierarchy_aux())

# Useful tree constructors:
leaf = ImmutableNode() # a leaf node
unit = 1               # the unit node, hackily represented by the integer 1.
def comp(x, y):
  """Creates a composition."""
  return ImmutableNode([x, y])
def assoc(x, y, z):
  """Creates an associator."""
  return ImmutableNode([x, y, z])
def sprout(n, k=None):
  """Creates an n-sprout with units injected at positions given by a list k."""
  k = k or []
  return ImmutableNode([unit if idx in k else leaf for idx in range(n)])
def tree(*args):
  """Creates a sprout with an arbitrary number children."""
  return ImmutableNode(list(args))

rho = comp(leaf, unit)
lamb = comp(unit, leaf)

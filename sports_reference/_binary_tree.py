"""
"""

import copy
import operator
import typing


class Node:
    """
    """
    _data: typing.Any = None

    _parent: "Node" = None
    _left: "Node" = None
    _right: "Node" = None

    def __init__(
        self, data: typing.Any = None, *,
        parent: "Node" = None, left: "Node" = None, right: "Node" = None
    ):
        self.data = data

        self.parent = parent
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"{type(self).__name__}(data={self.data})"

    def __str__(self) -> str:
        return str(self.data)

    def __eq__(self, other: "Node") -> bool:
        return self.data == other.data

    def __ne__(self, other: "Node") -> bool:
        return self.data != other.data

    def __lt__(self, other: "Node") -> bool:
        return self.data < other.data

    def __le__(self, other: "Node") -> bool:
        return self.data <= other.data

    def __gt__(self, other: "Node") -> bool:
        return self.data > other.data

    def __ge__(self, other: "Node") -> bool:
        return self.data >= other.data

    def __bool__(self) -> bool:
        return self.data is not None

    def __copy__(self) -> "Node":
        cls = self.__class__
        other = cls.__new__(cls)
        other.__dict__.update(self.__dict__)

        other.parent, other.left, other.right = None, None, None

        return other

    def __deepcopy__(self, memo: dict) -> "Node":
        cls = self.__class__
        other = cls.__new__(cls)

        memo[id(self)] = other
        for key, value in self.__dict__.items():
            setattr(other, key, copy.deepcopy(value, memo))

        return other

    @property
    def data(self) -> typing.Any:
        """
        :return:
        """
        return self._data

    @data.setter
    def data(self, value: typing.Any) -> None:
        self._data = value

    @property
    def parent(self) -> "Node":
        """
        :return:
        """
        return self._parent

    @parent.setter
    def parent(self, value: "Node") -> None:
        self._parent = value

    @property
    def left(self) -> "Node":
        """
        :return:
        """
        return self._left

    @left.setter
    def left(self, value: "Node") -> None:
        self._left = value

    @property
    def right(self) -> "Node":
        """
        :return:
        """
        return self._right

    @right.setter
    def right(self, value: "Node") -> None:
        self._right = value


class BinaryTree:
    """
    """
    def __init__(self, height: int):
        self._height = height
        self._root = self.build_tree(self.height)

    def __repr__(self) -> str:
        attributes = ("root", "height", "size")
        arguments = ", ".join(f"{k}={getattr(self, k)}" for k in attributes)

        return f"{type(self).__name__}({arguments})"

    def __str__(self) -> str:
        return self.to_string()

    @classmethod
    def build_tree(cls, height: int) -> Node:
        """
        :param height:
        :return:
        """
        if height == 0:
            return Node()

        node = Node()
        node.left = cls.build_tree(height - 1)
        node.right = cls.build_tree(height - 1)

        if node.left is not None:
            node.left.parent = node
        if node.right is not None:
            node.right.parent = node

        return node

    @property
    def root(self) -> Node:
        """
        :return:
        """
        return self._root

    @property
    def height(self) -> int:
        """
        :return:
        """
        return self._height

    @property
    def size(self) -> int:
        """
        :return:
        """
        return pow(2, self.height)

    def traverse(
        self, node: Node, order: typing.Literal["pre", "in", "post"] = "in",
        traversal: typing.List[Node] = None
    ) -> typing.List[Node]:
        """
        :param order:
        :param node:
        :param traversal:
        :return:
        """
        if traversal is None:
            traversal = []

        if node is None:
            return traversal

        if order == "pre":
            traversal.append(node)
        traversal = self.traverse(node.left, order, traversal)
        if order == "in":
            traversal.append(node)
        traversal = self.traverse(node.right, order, traversal)
        if order == "post":
            traversal.append(node)

        return traversal

    def levels(
        self, node: Node, nlevel: int = 0, levels: typing.Dict[int, typing.List[Node]] = None
    ) -> typing.Dict[int, typing.List[Node]]:
        """
        :param node:
        :param nlevel:
        :param levels:
        :return:
        """
        if levels is None:
            levels = {}

        if node is None:
            return levels

        levels.setdefault(nlevel, [])
        levels[nlevel].append(node)
        levels = self.levels(node.left, nlevel + 1, levels)
        levels = self.levels(node.right, nlevel + 1, levels)

        return levels

    def to_string(self, *, fill: str = "\t\t\t", ascending: bool = True) -> str:
        """
        :param fill:
        :param ascending:
        :return:
        """
        strings: typing.Dict[Node, str] = {}
        for nlevel, nodes in self.levels(self.root).items():
            for node in nodes:
                strings.setdefault(
                    id(node), (
                        nlevel * fill + str(node) + (self.height - nlevel) * fill
                    ) if ascending else (
                        (self.height - nlevel) * fill + str(node) + nlevel * fill
                    )
                )

        return "\n".join(strings[id(node)] for node in self.traverse(self.root))


class BracketSort:
    """
    """
    @classmethod
    def sort(cls, array: typing.List) -> typing.List:
        """
        :param array:
        :return:
        :raise ValueError:
        """
        result = [[x] for x in array]

        for _ in range(cls.height(array)):
            inorder = cls.selection_sort(result)
            result = [[*a, *b] for a, b in zip(inorder[::2], inorder[1::2])]

        return result[0]

    @classmethod
    def selection_sort(cls, array: typing.List) -> typing.List:
        """
        :param array:
        :return:
        """
        for i, _ in enumerate(array):
            index = None
            comp = operator.lt if i % 2 == 0 else operator.gt

            for j, value in enumerate(array[i:], i):
                index = (j if index is None or comp(value, array[index]) else index)

            array[i], array[index] = array[index], array[i]

        return array

    @classmethod
    def height(cls, array: typing.List) -> int:
        """
        :param array:
        :return:
        :raise ValueError:
        """
        if len(array) == 0:
            raise ValueError(array)

        height = 0
        while True:

            if (1 << height) == len(array):
                return height

            if (1 << height) > len(array):
                raise ValueError(array)

            height += 1

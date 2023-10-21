TREE_HEIGHT = 32
DEFAULT_VALUE = b"\x00" * 32


def init(list_):
    """返回移除最后一个元素后的新列表"""
    return list_[:-1]


def last(list_):
    """返回列表最后一个元素"""
    return list_[-1]


def first(list_):
    """返回列表第一个元素"""
    return list_[0]


def cal_right(f):
    """
    计算每一层右兄弟节点的默认值（从下往上）。
    """
    right = [DEFAULT_VALUE]
    for i in range(1, TREE_HEIGHT):
        right.append(f(right[i - 1], right[i - 1]))
    return right


def get_path(index):
    """
    返回根节点到索引 index 节点处的路径
    """
    p = []
    for _ in range(TREE_HEIGHT):
        p.append(index % 2)
        index = index // 2

    return list(reversed(p))


def merkle_root(values, right, f):
    """
    根据 Merkle Tree 的定义，从叶节点开始逐级往上计算根节点的值。

    values: 叶节点值列表
    right: 右兄弟节点不存在时的默认值
    f: 哈希函数
    """
    for h in range(TREE_HEIGHT):
        if len(values) % 2 == 1:
            values = values + [right[h]]
        values = [f(values[i], values[i + 1]) for i in range(0, len(values), 2)]
    return values[0]


def compute_root_up(p, left, right, seed, f):
    """
    根据传入的路径 p（从根到叶），路径 p 上所有节点的左兄弟节点的值 left、
    右兄弟节点的值 right 以及叶节点的值 seed，递归计算 Merkle 树的根。

    p: 路径 p（从根到叶）
    left: 路径 p 上所有节点的左兄弟节点的值
    right: 路径 p 上所有节点的右兄弟节点的值
    seed: 路径 p 上叶节点的值
    f: 哈希函数
    """

    if len(p) == 0:
        return seed

    if last(p) == 0:
        return compute_root_up(
            init(p), init(left), init(right), f(seed, last(right)), f
        )
    else:
        return compute_root_up(init(p), init(left), init(right), f(last(left), seed), f)


def insert_value(p, left, right, seed, f):
    """
    在路径 p 的叶节点处插入值为 seed 的节点，递归计算下一个节点所在路径所需的左兄弟节点的值。

    p: 待插入节点的路径（从根到叶）
    left: 路径 p 上所有节点的左兄弟节点的值
    right: 路径 p 上所有节点的右兄弟节点的值
    seed: 待插入节点的值
    f: 哈希函数
    """

    if len(p) == 1:
        return [seed] if first(p) == 0 else left

    if last(p) == 0:
        return init(left) + [seed]
    else:
        return insert_value(
            init(p), init(left), init(right), f(last(left), seed), f
        ) + [last(left)]


def branch_by_branch(values, right, f):
    left = [DEFAULT_VALUE] * TREE_HEIGHT

    for i, value in enumerate(values):
        p = get_path(i)
        left = insert_value(p, left, right, value, f)

    p = get_path(len(values))
    return compute_root_up(p, left, right, DEFAULT_VALUE, f)


def compute_root_up_iter(p, left, right, seed, f):
    h = len(p)

    root = seed
    for i in reversed(range(0, h)):
        if p[i] == 0:
            root = f(root, right[i])
        else:
            root = f(left[i], root)

    return root


def insert_value_iter(p, left, seed, f):
    if last(p) == 0:
        left[-1] = seed
    else:
        i = len(p) - 1
        node = seed
        while p[i] == 1:
            node = f(left[i], node)
            i -= 1

        left[i] = node

    return left


def branch_by_branch_iter(values, right, f):
    left = [DEFAULT_VALUE] * TREE_HEIGHT

    for i, value in enumerate(values):
        p = get_path(i)
        left = insert_value_iter(p, left, value, f)

    p = get_path(len(values))
    return compute_root_up_iter(p, left, right, DEFAULT_VALUE, f)


if __name__ == "__main__":
    from hashlib import blake2s

    f = lambda x, y: blake2s(x + y).digest()
    right = cal_right(f)
    right_rev = right[::-1]

    testdata = [(i + 2**255).to_bytes(32, "big") for i in range(10000)]

    # The Merkle root algo assumes trailing zero bytes
    assert merkle_root(testdata[:5], right, f) == merkle_root(
        testdata[:5] + [DEFAULT_VALUE] * 5, right, f
    )

    # Verify equivalence of the simple all-at-once method and the progressive method
    assert branch_by_branch(testdata[:1], right_rev, f) == merkle_root(
        testdata[:1], right, f
    )
    assert branch_by_branch(testdata[:2], right_rev, f) == merkle_root(
        testdata[:2], right, f
    )
    assert branch_by_branch(testdata[:3], right_rev, f) == merkle_root(
        testdata[:3], right, f
    )
    assert branch_by_branch(testdata[:5049], right_rev, f) == merkle_root(
        testdata[:5049], right, f
    )

    # Verify equivalence of the simple all-at-once method and the progressive method
    assert branch_by_branch_iter(testdata[:1], right_rev, f) == merkle_root(
        testdata[:1], right, f
    )
    assert branch_by_branch_iter(testdata[:2], right_rev, f) == merkle_root(
        testdata[:2], right, f
    )
    assert branch_by_branch_iter(testdata[:3], right_rev, f) == merkle_root(
        testdata[:3], right, f
    )
    assert branch_by_branch_iter(testdata[:5049], right_rev, f) == merkle_root(
        testdata[:5049], right, f
    )

# ERC-20 相关知识点总结

_2023-10-21_ · by zmrenwu · #Web3

[ERC-20 代币标准][1] 由 V 神等人于 2015 年提出后，很快就被广泛采纳。此后为了不断完善以太坊生态的代币标准，又有很多基于 ERC-20 的兼容或不兼容的拓展提案被提出，有些方案被广泛接受，有些则仍在讨论当中。

尽管 ERC-20 本身是一个简单的代币标准，但随着多年的发展，其所涉及的知识点众多。因此这篇文章将对 ERC-20 相关的知识点做一个梳理和总结，以加深对 ERC-20 的认识和理解。

## ERC-20 接口定义

以下是对 ERC-20 接口的定义，编程语言为 solidity。

```solidity
// SPDX-License-Identifier: MIT
// WTF Solidity by 0xAA

pragma solidity ^0.8.20;

/**
 * @dev ERC20 接口合约.
 */
interface IERC20 {
    /**
     * @dev 释放条件：当 `value` 单位的货币从账户 (`from`) 转账到另一账户 (`to`)时.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev 释放条件：当 `value` 单位的货币从账户 (`owner`) 授权给另一账户 (`spender`)时.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);

    /**
     * @dev 返回代币总供给.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev 返回账户`account`所持有的代币数.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev 转账 `amount` 单位代币，从调用者账户到另一账户 `to`.
     *
     * 如果成功，返回 `true`.
     *
     * 释放 {Transfer} 事件.
     */
    function transfer(address to, uint256 amount) external returns (bool);

    /**
     * @dev 返回`owner`账户授权给`spender`账户的额度，默认为0。
     *
     * 当{approve} 或 {transferFrom} 被调用时，`allowance`会改变.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev 调用者账户给`spender`账户授权 `amount`数量代币。
     *
     * 如果成功，返回 `true`.
     *
     * 释放 {Approval} 事件.
     */
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev 通过授权机制，从`from`账户向`to`账户转账`amount`数量代币。转账的部分会从调用者的`allowance`中扣除。
     *
     * 如果成功，返回 `true`.
     *
     * 释放 {Transfer} 事件.
     */
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) external returns (bool);
}
```

虽然下面这几个 function 在标准中没有强制规定，但绝大部分 ERC-20 的智能合约都会实现这些 function。

```solidity
    /**
     * @dev 返回代币名称.
     */
    function name() external view returns (string memory);

    /**
     * @dev 返回代币名称的缩写.
     */
    function symbol() external view returns (string memory);

    /**
     * @dev 返回代币使用的小数位数.
     */
    function decimals() external view returns (uint8);
```

## ERC-20 简单实现

实现上，通常用一个 `mapping` 记录账户和余额（account address -> balance）。

再用一个 `mapping` 的 `mapping` 记录 `owner` 账户给 `spender` 账户的授权额度（owner account address -> spender account address -> allowance）。

以下是一个 ERC-20 标准的简单实现，编程语言为 solidity。

```solidity
// SPDX-License-Identifier: MIT

pragma solidity 0.8.20;

contract MyToken{
    string public name;
    string public symbol;
    uint8 public decimals;
    uint256 public totalSupply;

    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(string memory name_, string memory symbol_, uint8 decimals_, uint256 totalSupply_) {
        name = name_;
        symbol = symbol_;
        decimals = decimals_;
        totalSupply = totalSupply_;
        _balances[msg.sender] = totalSupply_; // 将全部代币转入合约创建者的账户
    }

    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    function allowance(address owner, address spender) external view returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        _allowances[msg.sender][spender] = amount;

        emit Approval(msg.sender, spender, amount);

        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        _balances[msg.sender] -= amount;
        _balances[to] += amount;

        emit Transfer(msg.sender, to, amount);

        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        _allowances[from][msg.sender] -= amount;
        _balances[from] -= amount;
        _balances[to] += amount;

        emit Transfer(from, to, amount);

        return true;
    }
}
```

## ERC-20 存在的问题

ERC-20 因为接口简单清晰而被广泛采用，但也存在设计不合理的地方，导致在安全性、用户体验等方面存在一些瑕疵。为了消除这些瑕疵，一些拓展提案被提了出来。这一节将对 ERC-20 存在的问题和解决方案做一个总结。

### approve / transferFrom 存在安全瑕疵

`approve` 和 `transferFrom` 是一对孪生方法，可以说这是 ERC-20 标准的精髓所在。

通过 `approve` 方法，`owner` 账户可以授权 `spender` 账户一定的额度，授权后允许 `spender` 操作 `owner` 账户指定额度的代币。

通过 `transferFrom` 方法，`spender` 可操作 `owner` 账户指定额度的代币。

很多以太坊应用基于这个功能玩出了花。例如 UniSwap，当给 UniSwap 的池子添加流动性时，首先需要通过 `approve` 授权 UniSwap 智能合约操作用户的代币，授权后，智能合约就可以通过调用 `transferFrom` 将池子中的两种代币从用户账户划入合约。

看上去似乎没有问题，但当用户已经授权了某个 `spender` 一定额度后，又尝试修改其授权额度时，就可能出现被恶意攻击的地方。具体场景如下：

1. Alice 授权 Bob 操作某个代币，额度为 N。
2. Alice 想将授权额度修改为 M，于是发起了一笔交易，此交易正在等待矿工确认。
3. Bob 发现了这个交易，于是他立即发起一个交易，将 N 额度的代币从 Alice 的账户转走，由于 Bob 给的 gas 费比较高，这个交易先于 Alice 的交易被确认（即所谓抢跑交易）。
4. 随后 Alice 的交易被确认，将授权 Bob 的额度修改为 M。
5. Bob 趁 Alice 不注意，再次发起一笔交易，将 M 额度的代币从 Alice 的账户转走。

上述场景中，Alice 本意只允许 Bob 操作 M 额度的代币，但实际 Bob 坑走了 Alice N+M 的代币。

要防止出现这种问题，一种方案是将修改额度的操作分为 2 步。第一步发起一笔交易将授权额度改为 0，然后确认 `spender` 没有恶意花费代币后，再发起一笔交易将授权额度改为新的值。但缺点是需要付出双倍 gas 费，且操作很麻烦。

另一种是 [OpenZeppelin](https://www.openzeppelin.com/) 的方案，其实现的 ERC-20 合约中新增了`increaseAllownce` 和 `decreaseAllowance` 方法。如果要增加授权额度，调用 `increaseAllownce` 方法；减少授权额度则调用 `decreaseAllowance` 方法。这两个方法都接收 2 个参数，一个是被授权账户的地址，另外一个是需要增加或减少的授权额度。

```solidity
function increaseAllowance(address spender, uint256 addedValue) public returns (bool);

function decreaseAllowance(address spender, uint256 requestedDecrease) public returns (bool)
```

`increaseAllownce` 不存在上述抢跑交易的问题，因为无论 spender 有没有通过抢跑交易花费代币，授权额度增加的总是预期的增量。

`decreaseAllowance` 仍然存在抢跑风险，如果 spender 抢在 `decreaseAllowance` 的交易被确认前用掉一定或者全部的额度，使得剩余的额度低于需减少的额度，将导致额度扣减失败。

[ERC20 API: An Attack Vector on the Approve/TransferFrom Methods][2] 中还提到一种方案可完全解决这个问题，但需要修改 `approve` 方法的参数：

```solidity
function approve(
  address _spender,
  uint256 _currentValue,
  uint256 _value)
returns (bool success)
```

授权者在发起新的 `approve` 交易修改授权额度为 `_value` 时，需要将当前授权额度 `_currentValue` 传递给 `approve` 方法。只有 `approve` 方法在执行时发现查询到的授权额度和授权者传递的 `_currentValue` 相等时，说明在这个过程中被授权者没有通过抢跑交易使用授权额度，才执行更新操作。

这个方案的缺点是需要修改 `approve` 方法的参数，会导致不兼容改动，因此并未被采纳。

虽然存在这样一个安全上的小瑕疵，但通常来说，用户只会给一些知名的智能合约授权，这些合约中不一定存在可以执行以上攻击的代码逻辑，所以总体来说不算一个大的安全漏洞。

### approve / transferFrom 用户体验不佳

假如要让智能合约操作用户账户中的代币（例如向 UniSwap 池子中添加流动性或者移除流动性），用户需要执行 2 步操作：

1. 发起一笔交易，调用 `approve` 授权智能合约操作用户账户中的代币。
2. 授权完成后，再发起一笔交易调用智能合约的某个方法，这个方法会调用 `transferFrom` 来划转用户账户中已授权的代币。

2 笔交易就要支付 2 次 gas 费，且操作麻烦。

为了优化上述问题，[ERC-2612][3] 提案在 ERC-20 标准的基础上新增了一个 `permit` 方法，该方法也可以用来执行授权操作。通过这个方法执行授权的方式就像签署一张银行支票一样，用户签署一张支票，拥有此支票的人（包括用户自己）就可以执行授权操作。

有了 `permit` 方法，智能合约要操作用户账户中的代币，就可以将之前的 2 个交易合并为 1 个交易。

1. 用户线下签署授权消息（不涉及链上交易）。
2. 再发起一笔交易调用智能合约的某个方法，将签署的授权消息作为参数传递，合约调用 `permit` 和 `transferFrom` 同时完成授权和代币划转的操作。

可能有人会疑惑，既然这样，只需要智能合约的实现中，同时调用 `approve` 和 `transferFrom` 就行了，为什么还要 `permit` 方法呢？

我们可以仔细看一下 `approve` 接口的定义：

```solidity
function approve(address spender, uint256 amount) external returns (bool);
```

这里 `approve` 的参数只有被授权账户 `spender` 和授权额度 `amount`，那么授权人是谁呢？答案是授权交易的发起人。因此，为了完成授权操作，只能由授权人亲自发起交易才行。

通过 `permit`，则可以将授权人和授权的交易分离。授权人只需要负责签署授权消息，后续他可以亲自发起交易，也可以将签署的消息交给第三方，由第三方来代为发起交易，节省了 gas 的同时提高了灵活性。而且为后续解决“账户中需要 ETH 才能操作代币”的问题奠定了基础。

### 账户中需要 ETH 才能操作代币

ERC-20 代币还有一个体验不佳的地方，为了操作代币，账户中必须要有 ETH 用来支付 gas 费用。例如钱包账户中有 USDT，但没有 ETH，那么用户就无法转账 USDT，必须向钱包转入一定的 ETH 后，才能发起转账交易。

为了解决这个问题，人们提出了 _gasless transaction_，或者叫 _meta transaction_ 的概念。其基本思想是，用户线下签署某个授权转账的消息，将其发给第三方，第三方收到这个消息后，代替用户支付 gas 费，发起交易执行转账操作。同时消息中也会授权第三方扣除用户账户中一定的代币数量，以补偿第三方支付的 gas 费用。这样在用户端看来，他只需要支付代币，而不需要支付 ETH 即可完成转账交易。

其中这个第三方可以是中心化的服务商，也可以是去中心化的服务商。例如 [OpenGSN](https://opengsn.org/) 就是提供此类服务去中心化解决方案的项目。[OpenZeppelin Defender](https://www.openzeppelin.com/defender) 也提供了此类服务中心化的解决方案。

## 总结

[ERC-20 代币标准][1] 被提出后得到了广泛的采纳，但该标准也存在一些安全瑕疵和用户体验不佳的地方。为了消除这些瑕疵和优化用户体验，一些拓展方案被提了出来，其中一些已经得到了广泛的支持和应用。虽然 ERC-20 接口简单，但以其为基础建立的应用生态非常繁荣，涉及的知识点也非常的多，需要花精力了解和学习。

## 参考文章

1. [ERC-20: Token Standard][1]
2. [ERC20 API: An Attack Vector on the Approve/TransferFrom Methods][2]
3. [ERC-2612: Permit Extension for EIP-20 Signed Approvals][3]

[1]: https://eips.ethereum.org/EIPS/eip-20
[2]: https://docs.google.com/document/d/1YLPtQxZu1UAvO9cZ1O2RPXBbT0mooh4DYKjA_jp-RLM/edit?pli=1#heading=h.m9fhqynw2xvt
[3]: https://eips.ethereum.org/EIPS/eip-2612

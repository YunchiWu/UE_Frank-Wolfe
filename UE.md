# 用户均衡问题及其求解方法

1. 什么是交通网络？

交通网络是对现实交通的一种数学抽象，由节点、有向路段、路段阻抗三部分组成。

---

2. 什么是交通网络上的用户均衡？

对于同一个起讫点对，所有实际被使用的路径的旅行时间都相等，且都不大于任何未被使用的路径的旅行时间。

---

3. 用户均衡如何使用数学语言描述？
$$
f^{rs}_k > 0 \Rightarrow c^{rs}_k = u_{rs} \\
f^{rs}_k = 0 \Rightarrow c^{rs}_k \ge u_{rs}
$$

其中，
- $f^{rs}_k$ 表示起点为$r$、终点为$s$的路径$k$的路径流量。
- $c^{rs}_k$ 表示路径$(r,s)$上路径$k$的旅行成本。
- $u_{rs}$ 表示路径$(r,s)$的最小旅行成本。

---

4. 为什么不直接根据用户均衡的定义求解用户均衡问题？

不直接根据用户均衡定义求解，是因为用户均衡条件是关于路径流量和路径成本的非线性互补条件；而路径成本又由路段流量决定，路段流量又由路径流量汇总得到。若直接在路径层面求解，需要枚举大量路径，在大规模网络中计算不可行。因此通常将其转化为等价的凸最小化问题，再用算法求解。

---

5. 如何将用户均衡问题表述为最小化问题？

Beckmann 变换：
$$
\min z(x) = \sum_a \int_0^{x_a} t_a (\omega) d\omega
$$

约束为：
$$
\sum_k f^{rs}_k = q_{rs}, \quad \forall r,s \\
f^{rs}_k \ge 0, \quad \forall k,r,s
$$

并且路段流量由路径流量决定：
$$
x_a = \sum_{r} \sum_{s} \sum_{k} f^{rs}_k \delta^{rs}_{a, k}
$$

其中：
- $x_a$：路段$a$上的流量
- $t_a(x_a)$：路段$a$的旅行时间函数
- $f^{rs}_k$：OD对$(r,s)$间第$k$条路径上的流量
- $q_{rs}$：OD对$(r,s)$的出行需求
- $\delta^{rs}_{a,k}$：为1表示路段$a$在路径$k$上，否则为0

Beckmann 变换成立的前提是路段旅行时间函数是可分离的，即$t_a$只依赖于本路段流量$x_a$，并且通常假定$t_a(x_a)$为正且单调递增。

---

6. 为什么Beckmann变换等价于用户均衡定义？

通过将Beckmann变换写为：
$$
\min L(f, u) = z(x(f)) + \sum_{rs} u_{rs} \left(q_{rs} - \sum_{k} f^{rs}_k\right)
$$

约束为：
$$
f^{rs}_k \ge 0
$$

且$x_a = \sum_{r} \sum_{s} \sum_{k} f^{rs}_k \delta^{rs}_{a,k}$。

根据KKT条件：
$$
f^{rs}_k (c^{rs}_k - u_{rs}) = 0, \quad \forall r, s, k \\
c^{rs}_k - u_{rs} \ge 0, \quad \forall r, s, k \\
f^{rs}_k \ge 0, \quad \forall r, s, k \\
\sum_k f^{rs}_k = q_{rs}, \quad \forall r, s
$$

其中，$u_{rs}$表示OD对$(r,s)$的最小旅行成本。

与用户均衡的定义一致。因此，Beckmann变换的解与用户均衡的解相同。

---

7. 如何求解最小化问题？（凸组合方法）

对于可行域内的点$x^n$，下一步希望移动到点$x^{n+1}$，使得$z(x^{n+1}) < z(x^n)$。因此，将$z(x)$在$x=x^{n}$一阶泰勒展开：$z(x) \approx z(x^n) + \nabla z(x^n) (x - x^n)^T$，由于 $z(x^n), \ x^n, \ z(x^n)x^n$ 是常数。所以在第$n$次迭代中，用$z(x)$在$x^n$处的一阶线性近似构造一个辅助线性规划：
$$
\min_{y} \nabla z(x^n) y^T
$$。

在获得$y^n$后，则$x^{n+1} = x^n + \alpha_n (y^n - x^n) = (1 - \alpha_n)x^n + \alpha_n y^n$，其中$0 \le \alpha_n \le 1$。

然后，再通过
$$
\min_{0 \le \alpha \le 1} z\left((1-\alpha)x^n + \alpha y^n\right)
$$

求得步长$\alpha$。

通过$x^{n+1} = x^n + \alpha (y^n - x^n)$更新$x$，直到$x$满足精度要求结束迭代。

---

8. 如何使用凸组合方法求解Beckmann变换？

- Step 0：初始化
计算$t_a^0 = t_a(0)$，将所有出行需求分配到最短路径上，得到初始可行流量$x^0$。

- Step 1：更新旅行时间

根据当前路段流量$x^n$，计算每条路段的旅行时间$t_a^n = t_a(x_a^n), \ \forall a$。

- Step 2：方向寻找

对每个OD对$(r,s)$，在当前路段旅行时间$t_a^n$下寻找最短路径，并将该OD对的全部需求$q_{rs}$分配到当前最短路径上，得到辅助流量$y^n$。

- Step 3：一维搜索求步长

在 $\alpha \in [0,1]$ 上做一维搜索：
$$
\min_{0 \le \alpha \le 1} z\left(x^n + \alpha (y^n - x^n)\right)
$$

由于函数$z(x)$可导：
$$
\frac{d}{d\alpha} z[x^n + \alpha (y^n - x^n)]
= \sum_a t_a[x_a^n + \alpha (y_a^n - x_a^n)] (y_a^n - x_a^n)
$$

可以采用二分法求解。

- Step 4：更新流量

更新$x^{n+1} = x^n + \alpha (y^n - x^n)$。

- Step 5：收敛判断

若满足收敛条件，则停止；否则令$n := n + 1$返回Step 1开始下一轮迭代。
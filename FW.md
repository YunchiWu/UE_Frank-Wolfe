# 使用 Frank-Wolfe 算法求解用户均衡（UE）问题的规划

基于 `paper/chapter_5.pdf` 第 5.2 节内容，以下是使用 Frank-Wolfe（凸组合）算法求解用户均衡（UE）问题的完整步骤规划。

---

## 一、问题与数学模型

**UE 等价优化问题**（Beckmann 形式）：

$$\min z(\mathbf{x}) = \sum_a \int_0^{x_a} t_a(\omega)\, d\omega$$

约束条件：
- $\sum_k f_k^{rs} = q_{rs}, \quad \forall r,s$（流量守恒）
- $f_k^{rs} \geq 0, \quad \forall k,r,s$（非负性）
- $x_a = \sum_{rs}\sum_k f_k^{rs}\delta_{a,k}^{rs}$（路径-链路关联）

其中 $x_a$ 是链路 $a$ 上的流量，$t_a(\cdot)$ 是链路性能函数（如 BPR 函数），$f_k^{rs}$ 是 OD 对 $r\!-\!s$ 路径 $k$ 上的流量，$q_{rs}$ 是 OD 需求。

---

## 二、算法核心思想

Frank-Wolfe 算法在每次迭代中：
1. 在当前解处将非线性目标函数**线性化**；
2. 求解所得线性子问题（即"全有全无"分配）得到一个辅助流量解；
3. 在当前解与辅助解之间做**一维线搜索**，确定移动步长；
4. 更新流量并检查收敛。

线性化子问题的关键观察：$\partial z/\partial x_a = t_a(x_a)$，所以线性化后变成
$$\min \sum_a t_a^n \, y_a$$
其在固定旅行时间 $\{t_a^n\}$ 下的最优解，正是把每个 OD 对的全部流量都分配到最短路上——即标准的"全有全无"（AON）网络加载。

---

## 三、详细算法步骤

### Step 0 — 初始化
1. 取空网络旅行时间 $t_a^0 = t_a(0), \forall a$。
2. 基于 $\{t_a^0\}$ 对每个 OD 对求最短路径树（用 5.3 节的 label-correcting 算法）。
3. 执行 AON 加载，把每个 $q_{rs}$ 全部加到最短路上，得到初始链路流量 $\{x_a^1\}$。
4. 设迭代计数器 $n := 1$。

### Step 1 — 更新旅行时间
基于当前链路流量更新链路旅行时间：
$$t_a^n = t_a(x_a^n), \quad \forall a$$

### Step 2 — 方向寻找（求解线性子问题）
1. 以 $\{t_a^n\}$ 为固定链路时间，对每个 OD 对计算最短路径树。
2. 执行 AON 加载，得到**辅助流量** $\{y_a^n\}$。
3. 下降方向为 $\mathbf{d}^n = \mathbf{y}^n - \mathbf{x}^n$。

### Step 3 — 线搜索（确定步长）
求解一维优化：
$$\min_{0 \leq \alpha \leq 1} \sum_a \int_0^{x_a^n + \alpha(y_a^n - x_a^n)} t_a(\omega)\, d\omega$$

由于目标函数在搜索方向上单变量凸，其导数为
$$\frac{d}{d\alpha} z = \sum_a (y_a^n - x_a^n)\, t_a\!\big[x_a^n + \alpha(y_a^n - x_a^n)\big]$$

推荐用二分法（Bolzano search）寻找使该导数为零的 $\alpha_n \in [0,1]$。

### Step 4 — 移动（更新流量）
$$x_a^{n+1} = x_a^n + \alpha_n(y_a^n - x_a^n), \quad \forall a$$

### Step 5 — 收敛性检验
若满足收敛准则则停止，否则 $n := n+1$ 回到 Step 1。常用准则：

- **基于 OD 最短路时间变化**：
  $$\sum_{rs} \frac{|u_{rs}^n - u_{rs}^{n-1}|}{u_{rs}^n} \leq \kappa$$
- **基于链路流量变化**：
  $$\frac{\sqrt{\sum_a (x_a^{n+1} - x_a^n)^2}}{\sum_a x_a^n} \leq \kappa'$$
- 实践中也可用 relative gap 等其他准则。

---

## 四、关键子模块

1. **最短路径算法**（Section 5.3）：Moore-Pape label-correcting 方法，使用 forward-star 网络存储 + sequence list 管理（新节点入队尾，重新激活的节点入队首）。每次迭代对每个 origin 求一棵最短路树。

2. **AON 网络加载**：沿最短路径树回溯（用 predecessor 列表），把 $q_{rs}$ 累加到树上对应链路。

3. **线搜索**：每次评估只需代入公式 [5.7]，计算量小。

---

## 五、计算复杂度

总计算量（公式 [5.10]）：
$$\text{cost} \approx K \times (\text{迭代次数}) \times (\text{起点数}) \times (\text{节点数})$$

实际应用中 4–6 次迭代通常足够（取决于拥堵程度）。

---

## 六、针对当前项目的实施建议

针对 `data/` 下的 SiouxFalls / ChicagoSketch / Winnipeg 三个网络，建议：

1. 先在 SiouxFalls（小规模）上验证算法正确性，再扩展到大网络。
2. 复用已有的 `shortest_paths.py` 作为 Step 0/Step 2 的最短路模块。
3. 用 `demand.omx` 读取 OD 矩阵作为 $q_{rs}$。
4. 链路性能函数用 BPR：$t_a(x_a) = t_a^0\!\left[1 + 0.15(x_a/c_a)^4\right]$，参数从网络数据文件读取。
5. 线搜索建议二分法实现，$\alpha$ 区间 $[0,1]$，精度 $10^{-4}$ 左右即可。
6. 收敛门槛 $\kappa$ 视网络规模设为 $10^{-3}$ 到 $10^{-4}$。
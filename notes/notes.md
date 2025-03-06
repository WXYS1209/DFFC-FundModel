

# strategy
premises:
1. fund are described by $f_0(t) + f_1(t)$, where $f_0(t)$ is the baseline, and $f_1(t)$ is disordered
2. $f_0(t)$ can be excatly predicted
3. $f_1(t)$ is a random variable due to price: $f(x)$, where $x$ stands for price
4. we make money through the distribution of $f_1(t)$, by buying when $f_1(t) < - \sigma$ and selling when $f_1(t) > \sigma$

## average operation time of normal distribution
define average operation time $T$, to measure how long does we take one buy-in($T_1$) or sell-out($T_2$) operation.
$T = T_1 + T_2$. These 2 are the same for normal distribution. Also, assumes that after buy-in, we cannot take any moves except sell-out.
i.e. we invest all of our money into one window at once.

- For normal distribution, $T$ is unrelated to $\sigma$:
  $T_i = \frac{1}{p}$, $p = \int_\sigma^\infty f(x) dx$

We may also define a /average profit/ $V$, measuring how much money we can make for one window. In our strategy
described below, $V \propto \sigma$.

Thus, the money-generating rate $M = V/T$. Higher $M$ means more money.

## Strategy for 2 funds
we have 2 funds $f$ and $g$.

1. let h = $f - g$, then buy&sell based on h
   the joint distribution can be calculated through momentum generating functional:
   $$h(x) = \int f(x) g(x + u) du$$
   for 2 identical uncorrelated normal distributions, we find $\sigma_h = \sqrt{2} \sigma$. T would not change

   - $T \to T, V \to \sqrt{2}V$
2. buy in whenever one of $f$ or $g$ goes below $-\sigma$. Result in different $T_1$.
   $p_1 \to 2(1 - p)p$, $T_1 = 1/p_1, T_2 = 1/p, T = T_1 + T_2$

   - $T \to \frac{3T-2}{2T-4}T, V \to V$

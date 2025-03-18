

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

## stochastic strategy model for one fund
### Fund Price Expression
Fund price at time $t$ can be describe by 2 part, the baseline part $f_0(t)$ and the fluctuative part $\xi(t)$, where

$$
f(t)=f_0(t)+\xi(t)
$$

$$
f(t)=f_0(t)+\zeta(t)
$$

   The fluctuation can be fully discribed by

$$
   \langle\xi(t)\rangle=0
$$

$$
   \langle\xi(t')\xi(t'+t)\rangle=C(t)
$$

   For white Gaussian noise, $C(t)=\sigma^2\delta(t)$. For real fund fluctuation data, $C(t)=\sigma^2 e^{-\lambda t}$(???Seems this definition is WRONG!)

### Strategy Expression
For sake of simplisity, we consider continuous strategy expression, the fund we bought per unit time $B$ is a function of fluctuation. 

$$
\frac{dB}{dt}=g(\xi)
$$

For example, a linear strategy

$$
\frac{dB}{dt}=-k \xi(t)
$$

### Calculation
Cost $U(t)$, 

$$
U(t)=\int dB=\int _0^t -k \xi(t') dt'
$$

Assets $M(t)$,

$$
M(t)=f(t)\cdot\int _0^t \frac{dB}{f_0 (t)+\xi(t)}=-f(t) \int _0^t \frac{k\xi(t')}{f(t')}dt'
$$

Profet $M-U$

$$
\begin{aligned}
M(t)-U(t)&=-f(t)\cdot \int _0^t \frac{k\xi(t')}{f(t')}dt'+\int _0^t k \xi(t') dt'\\
&=- \int _0^t \frac{f(t)-f(t')}{f(t')}k\xi(t')dt'
\end{aligned}
$$

Suppose $\xi(t)<<f_0(t)$

$$
\begin{aligned}
M(t)-U(t)&=-f(t)\cdot \int _0^t \frac{k\xi(t')}{f(t')}dt'+\int _0^t k \xi(t') dt'\\
&=-f(t)\cdot \int _0^t \frac{k\xi(t')}{f_0(t')}\left(1-\frac{\xi(t')}{f_0(t')}\right)dt'+\int _0^t k \xi(t') dt'\\
&=-f(t)\cdot \int _0^t \frac{k\xi(t')}{f_0(t')}dt'+f(t)\cdot \int _0^t \frac{k\xi^2(t')}{f_0^2(t')}dt'+\int _0^t k \xi(t') dt'
\end{aligned}
$$

Consider $f_0(t)$ as a linear function of t, which

$$
f_0(t)=a t+1
$$

We get

$$
\begin{aligned}
M(t)-U(t)
&=-f(t)\cdot \int _0^t \frac{k\xi(t')}{f_0(t')}dt'+f(t)\cdot \int _0^t \frac{k\xi^2(t')}{f_0^2(t')}dt'+\int _0^t k \xi(t') dt'\\
&=-(a t+1)\cdot \int _0^t \frac{k\xi(t')}{at'+1}dt'+(a t+1)\cdot \int _0^t \frac{k\xi^2(t')}{(at'+1)^2}dt'+\int _0^t k \xi(t') dt'\\
\end{aligned}
$$

### Result
The Expectation of Profet

$$
\begin{aligned}
   \langle M-U\rangle&=(a t+1)\cdot \int _0^t \frac{k\langle\xi^2(t')\rangle}{(at'+1)^2}dt'\\
   &=(a t+1)kC(0)\cdot \int _0^t \frac{1}{(at'+1)^2}dt'\\
   &=a^2kC(0)t\\
\end{aligned}
$$

The Variance of Cost

$$
\begin{aligned}
   \langle U^2\rangle&=\langle\int _0^t  k \xi(t') dt'\cdot \int _0^t  k \xi(t'') dt''\rangle\\
&=k^2\int _0^t  \int _0^t \langle\xi(t') \cdot  \xi(t'')\rangle dt' dt''\\
&=k^2\int _0^t  \int _0^t C(t'-t'') dt' dt''\\
\end{aligned}
$$
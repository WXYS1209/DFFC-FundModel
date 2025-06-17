from base import BaseIndicator
import numpy as np

class HoltWintersIndicator(BaseIndicator):
   def fit(self, alpha: float, beta: float, gamma: float, season_length: int) -> np.ndarray:
        """
        对单位净值数据进行HoltWinters平滑。
        返回与数据等长的平滑结果数组。
        """
        arr = self.data
        n = len(arr)
        smoothed = np.zeros(n)
        
        for t in range(n):
            prefix = arr[:t+1]
            m = season_length
            if len(prefix) < m:
                level = prefix[0]
                for i in range(1, len(prefix)):
                    level = alpha * prefix[i] + (1 - alpha) * level
                smoothed[t] = level
            else:
                level = np.mean(prefix[:m])
                if len(prefix)==m:
                    trend = prefix[m-1] - prefix[m-2] if m >= 2 else 0
                else:
                    trend = (np.mean(prefix[m:]) - np.mean(prefix[:m])) / m
                seasonal = [prefix[i] - level for i in range(m)]
                for i in range(m, len(prefix)):
                    last_level = level
                    last_trend = trend
                    seasonal_index = (i - m) % m
                    level = alpha * (prefix[i] - seasonal[seasonal_index]) + (1 - alpha) * (last_level + last_trend)
                    trend = beta * (level - last_level) + (1 - beta) * last_trend
                    seasonal[seasonal_index] = gamma * (prefix[i] - level) + (1 - gamma) * seasonal[seasonal_index]
                fitted = level + trend + seasonal[(len(prefix)-m) % m]
                smoothed[t] = fitted
        return smoothed
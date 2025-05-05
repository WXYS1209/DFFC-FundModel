from abc import ABC, abstractmethod
from typing import Sequence

class BaseIndicator(ABC):
    """
    Base class for indicators that provide smoothing lines for a sequence of data.
    """

    def __init__(self, data: Sequence[float]):
        """
        Initialize the indicator with a sequence of data.
        :param data: A sequence of numerical data to be smoothed.
        """
        self.data = data

    @abstractmethod
    def fit(self) -> Sequence[float]:
        """
        Abstract method to compute the smoothed data.
        Must be implemented by subclasses.
        :return: A sequence of smoothed data.
        """
        pass

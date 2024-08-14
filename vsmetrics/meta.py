from typing import List, Optional, Union
from abc import ABC, abstractmethod
from vstools import vs

class MetricBase(ABC):
    formats: List[int] = []
    props: List[str] = []

    def __init__(self, **kwargs):
        self.params = kwargs
        self.result: Optional[vs.VideoNode] = None

    def validate_format(self, input: vs.VideoNode):
        if input.format.id not in self.formats:
            fmts = [vs.Format.name(fmt) for fmt in self.formats]
            raise ValueError(f"Expected {fmts} but got {input.format.name}")

    @abstractmethod
    def _calculate(self, reference: vs.VideoNode, distorted: Optional[vs.VideoNode] = None) -> vs.VideoNode:
        pass

    def calculate(self, reference: vs.VideoNode, distorted: Optional[vs.VideoNode] = None) -> 'MetricVideoNode':
        self.validate_format(reference)
        if distorted is not None:
            self.validate_format(distorted)
        self.result = self._calculate(reference, distorted)
        return MetricVideoNode(self.result, self)


class MetricVideoNode:
    def __init__(self, clip: vs.VideoNode, metric: MetricBase):
        self._clip = clip
        self._metric = metric

    def __getattr__(self, name):
        return getattr(self._clip, name)


class NoReferenceMetric(MetricBase):
    def calculate(self, reference: vs.VideoNode) -> 'MetricVideoNode':
        return super().calculate(reference)

    @abstractmethod
    def _calculate(self, reference: vs.VideoNode, distorted: None = None) -> vs.VideoNode:
        pass


class FullReferenceMetric(MetricBase):
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> 'MetricVideoNode':
        return super().calculate(reference, distorted)

    @abstractmethod
    def _calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        pass

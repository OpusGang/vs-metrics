from enum import Enum
import torch
import lpips

from vstools import inject_self, vs
from ..meta import MetricBase

import numpy as np
from numpy import ndarray

__all__ = [
    "LPIPS"
]

class LPIPS(MetricBase):
    props: list[str] = ["lpips"]
    formats: list[int] = [
        vs.RGBS
    ]

    class Network(Enum):
        ALEX = 'alex'
        VGG = 'vgg'
        SQUEEZE = 'squeeze'

    def __init__(self, network: Network = Network.ALEX):
        self.network = network.value
        self.loss_fn_alex = lpips.LPIPS(net=self.network)

    @inject_self
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)
        self.validate_format(distorted)
        
        reference = reference.std.Limiter(0, 1)
        distorted = distorted.std.Limiter(0, 1)

        clip = reference.std.ModifyFrame([reference, distorted], self._process_frame)
        self._register_metadata(clip)
        return clip

    def _process_frame(self, n: int, f: list[vs.VideoFrame]) -> vs.VideoFrame:
        f1, f2 = f
        fout = f1.copy()

        arr1 = np.asarray(f1)
        arr2 = np.asarray(f2)

        blur_score = self._metric(arr1, arr2)
        fout.props[self.props[0]] = float(blur_score)

        return fout

    def _metric(self, reference: ndarray, distorted: ndarray) -> float:
        reference = torch.from_numpy(reference).float().div(255).sub(0.5).div(0.5) # type: ignore
        distorted = torch.from_numpy(distorted).float().div(255).sub(0.5).div(0.5) # type: ignore

        data = self.loss_fn_alex(reference, distorted) # type: ignore
        data = data.item()

        return data
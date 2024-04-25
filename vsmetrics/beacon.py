import torch
import lpips

from enum import Enum
import numpy as np
from numpy.typing import NDArray

from vstools import vs, core
from .util import validate_format
from .meta import BaseUtil, MetricVideoNode

class LPIPS(BaseUtil):
    props: list[str] = ["lpips"]
    formats: tuple[int, ...] = (
        vs.RGBS,
    )

    class Network(Enum):
        ALEX = 'alex'
        VGG = 'vgg'
        SQUEEZE = 'squeeze'

    def __init__(self, network: Network = Network.ALEX):
        self.network = network.value
        self.loss_fn_alex = lpips.LPIPS(net=self.network)

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:
        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)
        
        reference = reference.std.Limiter(0, 1)
        distorted = distorted.std.Limiter(0, 1)

        clip = reference.std.ModifyFrame([reference, distorted], self._process_frame)
        return MetricVideoNode(clip, self)

    def _process_frame(self, n: int, f: list[vs.VideoFrame]) -> vs.VideoFrame:
        f1, f2 = f
        fout = f1.copy()

        arr1 = np.asarray(f1)
        arr2 = np.asarray(f2)

        blur_score = self._metric(arr1, arr2)
        fout.props[self.props[0]] = float(blur_score)

        return fout

    def _metric(self, reference: NDArray, distorted: NDArray) -> float:
        reference = torch.from_numpy(reference).float().div(255).sub(0.5).div(0.5)
        distorted = torch.from_numpy(distorted).float().div(255).sub(0.5).div(0.5)

        data = self.loss_fn_alex(reference, distorted)
        data = data.item()

        return data

from enum import IntEnum
from typing import List
from vstools import vs, core
from .meta import NoReferenceMetric

class CAMBI(NoReferenceMetric):
    formats: List[int] = [vs.GRAY10, vs.YUV420P10, vs.YUV422P10, vs.YUV444P10]
    props: List[str] = ['CAMBI']

    class EOTF(IntEnum):
        AUTO = 0
        BT1886 = 1
        ST2084 = 2

    def __init__(
        self,
        window_size: int = 63,
        topk: float = 0.6,
        tvi_threshold: float = 0.019,
        max_log_contrast: int = 2,
        eotf: EOTF = EOTF.BT1886
    ):
        """
        Compute CAMBI banding score with CAMBI.

        :param window_size:        Window size to compute CAMBI. Range: min=15, max=127, default=63 (corresponds to ~1 deg at 4K res & 1.5H).
        :param topk:               Ratio of pixels for spatial pooling computation. Range: min=0.0001, max=1.0, default=0.6.
        :param tvi_threshold:      Visibility threshold for luminance ΔL < tvi_threshold * L_mean for BT.1886. Range: min=0.0001, max=1.0, default=0.019.
        :param max_log_contrast    Maximum contrast in log luma level (2^max_log_contrast) at 10-bits. Default 2 is equivalent to 4 luma levels at 10-bit and 1 luma level at 8-bit.
                                   The default is recommended for banding artifacts coming from video compression.
        
        :return: clip with calculated CAMBI scores as a frame property.
        """
        super().__init__(
            window_size=window_size,
            topk=topk,
            tvi_threshold=tvi_threshold,
            max_log_contrast=max_log_contrast,
            eotf=eotf
        )

    def _calculate(self, reference: vs.VideoNode, distorted: None = None) -> vs.VideoNode:
        return core.cambi.Cambi(reference, **self.params)

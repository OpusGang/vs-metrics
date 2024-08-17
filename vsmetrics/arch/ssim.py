from vstools import vs, core

from ..parent.vmaf import VMAFMetric
from ..meta import MetricBase

# class SSIM(VMAFMetric):
#     feature_id = 2
#     props: list[str] = [
#         'float_ssim'
#     ]


class SSIM(MetricBase):
    props: list[str] = ["PlaneSSIM"]
    formats: list[int] = [
        vs.GRAY8,
        vs.GRAY16,
        vs.RGBS
    ]

    def __init__(
        self,
        plane: list[int] = [0, 1, 2],
        downsample: bool = True,
        k1: float = 0.01,
        k2: float = 0.03,
        dynamic_range: int = 1
    ):
        self.plane = plane
        self.downsample = downsample
        self.k1 = k1
        self.k2 = k2
        self.dynamic_range = dynamic_range

    class Mask:
        SSIM_MAP = "PlaneSSIM_map"

    def calculate(
        self,
        reference: vs.VideoNode,
        distorted: vs.VideoNode
    ) -> vs.VideoNode:
        from muvsfunc import SSIM as _SSIM

        self.validate_format(reference)
        self.validate_format(distorted)

        ssim_map = _SSIM(
            reference,
            distorted,
            plane=None,
            downsample=self.downsample,
            k1=self.k1,
            k2=self.k2,
            L=self.dynamic_range,
            show_map=True
        )

        ssim_clip = distorted.std.CopyFrameProps(ssim_map, self.props[0])
        ssim_clip = ssim_clip.std.ClipToProp(
            ssim_map.std.RemoveFrameProps("_Matrix"),
            prop=self.Mask.SSIM_MAP
        )

        return ssim_clip


class MSSSIM(VMAFMetric):
    feature_id = 3
    props: list[str] = [
        'float_ms_ssim'
    ]

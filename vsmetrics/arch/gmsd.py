from vstools import inject_self, vs

from ..meta import MetricBase

__all__ = [
    "GMSD"
    ]


class GMSD(MetricBase):
    props: list[str] = ["PlaneGMSD"]
    formats: list[int] = [
        vs.GRAYS,
        vs.RGBS,
        vs.YUV444PS
    ]

    def __init__(self, plane: int = 0, downsample: bool = True, c: float = 0.0026):
        self.plane = plane
        self.downsample = downsample
        self.c = c

    class Mask:
        GRADIENT = "PlaneGMSD_gradient_map"

    @inject_self
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import GMSD as _GMSD

        self.validate_format(reference)
        self.validate_format(distorted)

        gmsd = _GMSD(
            reference,
            distorted,
            self.plane,
            self.downsample,
            self.c,
            show_map=True
        )

        gmsd_clip = distorted.std.CopyFrameProps(gmsd, self.props[0])
        gmsd_clip = gmsd_clip.std.ClipToProp(
            gmsd.std.RemoveFrameProps("_Matrix"),
            prop=GMSD.Mask.GRADIENT
            )

        self._register_metadata(gmsd_clip)
        return gmsd_clip
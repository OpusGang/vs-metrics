from vstools import vs, core

from ..meta import MetricBase

class MDSI(MetricBase):
    props: list[str] = ["FrameMDSI"]
    formats: list[int] = [
        vs.RGB24,
        vs.RGB48,
        vs.RGBS
    ]

    class Mask:
        GRADIENT = "FrameMDSI_gradient_map"
        CHROMATICITY = "FrameMDSI_chromaticity_map"
        GRADIENT_PLUS_CHROMA = "FrameMDSI_gradient_chromaticity_map"

    def __init__(self, alpha: float = 0.6, scale: float = 1.0):
        self.alpha = alpha
        self.scale = scale

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import MDSI as _MDSI

        self.validate_format(reference)
        self.validate_format(distorted)

        clip, gradient_map, chromaticity_map, gradient_chromaticity_map = _MDSI(
            reference, distorted, self.scale, self.alpha, show_maps=True # type: ignore
        )

        maps = [gradient_map, chromaticity_map, gradient_chromaticity_map]

        for map_clip, map_name in zip(maps, [self.Mask.GRADIENT, self.Mask.CHROMATICITY, self.Mask.GRADIENT_PLUS_CHROMA]):
            clip = core.std.ClipToProp(clip, map_clip.std.RemoveFrameProps("_Matrix"), map_name)
        
        return clip

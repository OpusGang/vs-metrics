from vstools import vs, core

from ..meta import MetricBase
from ..enums import ColormapTypes

class VisualizeDiffs(MetricBase):
    ColormapTypes = ColormapTypes

    formats: list[int] = [
        vs.YUV410P8,
        vs.YUV420P8,
        vs.YUV422P8,
        vs.YUV444P8,
        vs.GRAY8,
        vs.RGB24,
    ]

    def __init__(self, auto_gain: bool = True, type: ColormapTypes = ColormapTypes.JET):
        self.auto_gain = auto_gain
        self.type = type

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:

        self.validate_format(reference)
        self.validate_format(distorted)

        return core.julek.VisualizeDiffs(
            reference,
            distorted,
            self.auto_gain,
            self.type.value
        )


class ColorMap(MetricBase):
    ColormapTypes = ColormapTypes

    formats: list[int] = [
        vs.YUV410P8,
        vs.YUV420P8,
        vs.YUV422P8,
        vs.YUV444P8,
        vs.GRAY8,
        vs.RGB24,
    ]

    def __init__(self, type: ColormapTypes = ColormapTypes.JET):
        self.type = type

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)

        return core.julek.ColorMap(reference, type=self.type.value)

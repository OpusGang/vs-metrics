from vstools import vs

from vsmetrics.meta import MetricBase
from ...enums.visualizediffs import ColormapTypes

class VisualizeDiffs(MetricBase):
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

        return reference.julek.VisualizeDiffs(
            distorted,
            self.auto_gain,
            self.type.value
        )


class ColorMap(MetricBase):
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

        return reference.julek.ColorMap(type=self.type.value)
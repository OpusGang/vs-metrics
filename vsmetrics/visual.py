from vstools import vs, core
from .util import validate_format
from .enums import ColormapTypes

class VisualizeDiffs:
    formats: tuple[int, ...] = (
        vs.YUV410P8,
        vs.YUV420P8,
        vs.YUV422P8,
        vs.YUV444P8,
        vs.GRAY8,
        vs.RGB24,
    )

    def __init__(self, auto_gain: bool = True, type: ColormapTypes = ColormapTypes.JET):
        self.auto_gain = auto_gain
        self.type = type

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:

        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)

        return core.julek.VisualizeDiffs(
            reference,
            distorted,
            self.auto_gain,
            self.type.value
        )


class ColorMap:
    formats: tuple[int, ...] = (
        vs.YUV410P8,
        vs.YUV420P8,
        vs.YUV422P8,
        vs.YUV444P8,
        vs.GRAY8,
        vs.RGB24,
    )

    def __init__(self, type: ColormapTypes = ColormapTypes.JET):
        self.type = type

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        validate_format(reference, self.formats)

        return core.julek.ColorMap(reference, type=self.type.value)
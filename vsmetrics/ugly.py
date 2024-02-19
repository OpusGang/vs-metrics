from enum import Enum, auto
from vstools import vs, core

# https://github.com/HomeOfVapourSynthEvolution/mvsfunc/blob/865c7486ca860d323754ec4774bc4cca540a7076/mvsfunc/mvsfunc.py#L1169

class MAE:
    pass

class MSE:
    pass

class RMSE:
    pass

class COVARIANCE:
    pass

class CORRELATION:
    pass

class ColormapTypes(Enum):
    AUTUMN = 0
    BONE = 1
    JET = 2
    WINTER = 3
    RAINBOW = 4
    OCEAN = 5
    SUMMER = 6
    SPRING = 7
    COOL = 8
    HSV = 9
    PINK = 10
    HOT = 11
    PARULA = 12
    MAGMA = 13
    INFERNO = 14
    PLASMA = 15
    VIRIDIS = 16
    CIVIDIS = 17
    TWILIGHT = 18
    TWILIGHT_SHIFTED = 19
    TURBO = 20
    DEEPGREEN = 21


class VisualizeDiffs:
    def __init__(self, auto_gain: bool = True, type: ColormapTypes = ColormapTypes.AUTUMN):
        self.auto_gain = auto_gain
        self.type = type
    
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        return core.julek.VisualizeDiffs(
            reference,
            distorted,
            self.auto_gain,
            self.type.value
        )


class ColorMap:
    def __init__(self, type: ColormapTypes = ColormapTypes.AUTUMN):
        self.type = type

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        return core.julek.ColorMap(reference, type=self.type.value)

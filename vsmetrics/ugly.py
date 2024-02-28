from .enums import ColormapTypes
from .util import validate_format
from typing import Optional
from vstools import vs, core

class PlaneStatistics:
    def __init__(self, plane=None):
        self.plane = plane
        self.meany = False
        self.mad = False
        self.var = False
        self.std = False
        self.rms = False
        self.psnr = False
        self.cov = False
        self.corr = False

    def calculate(
        self,
        reference=vs.VideoNode,
        distorted: Optional[vs.VideoNode] = None
    ) -> vs.VideoNode:

        from mvsfunc import PlaneStatistics as _PlaneStatistics
        from mvsfunc import PlaneCompare as _PlaneCompare

        if distorted:
            return _PlaneCompare(
                reference,
                distorted,
                self.plane,
                self.mae,
                self.rms,
                self.psnr,
                self.cov,
                self.corr
            )

        return _PlaneStatistics(
            reference,
            self.plane,
            self.meany,
            self.mad,
            self.var,
            self.std,
            self.rms
        )
    
    def mean(self):
        self.meany = True

    def mean_abs_dev(self):
        self.mad = True
        
    def variance(self):
        self.var = True

    def standard_dev(self):
        self.std = True

    def rmse(self):
        self.rms = True
    
    def covariance(self):
        self.corr = True

    def correlation(self):
        self.corr = True


class VisualizeDiffs:
    formats: tuple[int] = (
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
        self.fmts = [fmt.name for fmt in self.formats]
    
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        
        validate_format(reference, self.formats, self.fmts)
        validate_format(distorted, self.formats, self.fmts)

        return core.julek.VisualizeDiffs(
            reference,
            distorted,
            self.auto_gain,
            self.type.value
        )


class ColorMap:
    formats: vs.GRAY8

    def __init__(self, type: ColormapTypes = ColormapTypes.AUTUMN):
        self.type = type

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        return core.julek.ColorMap(reference, type=self.type.value)
from .enums import ColormapTypes
from .util import validate_format
from vstools import vs, core, plane
from mvsfunc import PlaneStatistics, PlaneCompare

class MetricsWrapper:
    def __init__(self, plane: int):
        self.plane = plane
        # no ref
        self.mean = False
        self.mad = False
        self.var = False
        self.std = False
        self.rms = False
        # full ref
        self.mae = False
        self.rmse = False
        self.cov = False
        self.corr = False
        # evil
        self.psnr = False


class NoReferenceWrapper(MetricsWrapper):
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        # bypass bug in function
        _reference = plane(reference, self.plane)

        calculate = PlaneStatistics(
            clip=_reference,
            mean=self.mean,
            mad=self.mad,
            var=self.var,
            std=self.std,
            rms=self.rms
        ) # type: ignore
        
        return reference.std.CopyFrameProps(calculate) # type: ignore


class FullReferenceWrapper(MetricsWrapper):
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        return PlaneCompare(
            clip1=reference,
            clip2=distorted,
            plane=self.plane,
            mae=self.mae,
            rmse=self.rmse,
            psnr=self.psnr,
            cov=self.cov,
            corr=self.corr
        )


class Mean(NoReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.mean = True


class MAD(NoReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.mad = True


class Variance(NoReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.var = True


class StandardDev(NoReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.std = True


class RMS(NoReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.rms = True


class MAE(FullReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.mae = True


class RMSE(FullReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.rmse = True


class Covariance(FullReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.cov = True


class Correlation(FullReferenceWrapper):
    def __init__(self, plane: int = 0):
        super().__init__(plane)
        self.corr = True


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
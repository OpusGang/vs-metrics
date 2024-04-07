from vsmasktools import Prewitt, PrewittTCanny
from .enums import ColormapTypes
from .util import validate_format
from vstools import vs, core, plane
from mvsfunc import PlaneStatistics, PlaneCompare
from .util import MetricVideoNode

class Edge():
    def calculate(self, reference: vs.VideoNode, mask = PrewittTCanny) -> vs.VideoNode:
        mask = mask.edgemask(reference)
        measure = core.std.PlaneStats(mask)
        return reference.std.CopyFrameProps(measure)

# TODO
# COME UP WITH SOME WAY TO HANDLE SUBCLASSES REQUESTING DIFFERENT PLANES
class MetricsWrapper:
    def __init__(self, plane: int):
        self.plane = plane

    @property
    def props(self) -> list[str]:
        raise NotImplementedError("props must be defined in subclass")

class NoReferenceWrapper(MetricsWrapper):
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:
        # bypass bug in function
        _reference = plane(reference, self.plane)

        calculate = PlaneStatistics(
            clip=_reference,
            mean=getattr(self, 'mean', False),
            mad=getattr(self, 'mad', False),
            var=getattr(self, 'var', False),
            std=getattr(self, 'std', False),
            rms=getattr(self, 'rms', False)
        )  # type: ignore
        
        clip = reference.std.CopyFrameProps(calculate)  # type: ignore
        return MetricVideoNode(clip, self)

class FullReferenceWrapper(MetricsWrapper):
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:

        clip = PlaneCompare(
            clip1=reference,
            clip2=distorted,
            plane=self.plane,
            mae=getattr(self, 'mae', False),
            rmse=getattr(self, 'rmse', False),
            cov=getattr(self, 'cov', False),
            corr=getattr(self, 'corr', False),
            psnr=False
        )

        return MetricVideoNode(clip, self)

class Mean(NoReferenceWrapper):
    mean = True
    props: list[str] = ['PlaneMean']

class MAD(NoReferenceWrapper):
    mad = True
    props: list[str] = ['PlaneMAD']

class Variance(NoReferenceWrapper):
    var = True
    props: list[str] = ['PlaneVar']

class StandardDeviation(NoReferenceWrapper):
    std = True
    props: list[str] = ['PlaneStd']

class RMS(NoReferenceWrapper):
    rms = True
    props: list[str] = ['PlaneRMS']

class MAE(FullReferenceWrapper):
    mae = True
    props: list[str] = ['PlaneMAE']

class RMSE(FullReferenceWrapper):
    rmse = True
    props: list[str] = ['PlaneRMSE']

class Covariance(FullReferenceWrapper):
    cov = True
    props: list[str] = ['PlaneCov']

class Correlation(FullReferenceWrapper):
    corr = True
    props: list[str] = ['PlaneCorr']

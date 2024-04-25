from enum import Enum
from vsmasktools import Prewitt, PrewittTCanny
from vstools import vs, merge_clip_props, split, plane
from mvsfunc import PlaneStatistics, PlaneCompare
from .meta import BaseUtil, MetricVideoNode

class Edge(BaseUtil):
    props: list[str] = [
        'Edge'
    ]
    
    class Operator(Enum):
        MAXIMUM = 'Max'
        AVERAGE = 'Average'
        MINIMUM = 'Min'

    def calculate(self, reference: vs.VideoNode, planes: list[int] | int = [0, 1, 2]) -> vs.VideoNode | MetricVideoNode:

        if isinstance(planes, int):
            planes = [planes]

        self.props = self._generate_props(
            self.props, reference.format.color_family, planes # type: ignore
        )
        
        edge = PrewittTCanny.edgemask(reference, planes=planes)
        s = split(edge)

        measure_results = []
        for i, plane in enumerate(planes):
            actual_index = plane if plane < len(s) else len(s) - 1  # dumb hack
            measure_results.append(s[actual_index].std.PlaneStats(prop=f"{self.props[i]}_"))

        merge = merge_clip_props(reference, *measure_results)
        
        updated_props = []
        for prop in self.props:
            for operator in Edge.Operator:
                updated_props.append(f"{prop}_{operator.value}")

        self.props = updated_props

        return MetricVideoNode(merge, self)


# TODO
# COME UP WITH SOME WAY TO HANDLE SUBCLASSES REQUESTING DIFFERENT PLANES
class MetricsWrapper:
    def __init__(self, plane: int = 0):
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

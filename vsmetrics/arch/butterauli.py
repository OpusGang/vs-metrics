from vstools import inject_self, vs
from vsmetrics.meta import MetricBase

__all__ = [
    "BUTTERAUGLI"
]

class BUTTERAUGLI(MetricBase):
    formats: list[int] = [
        vs.RGB24,
        vs.RGB48,
        vs.RGBS
    ]

    props: list[str] = [
        '_FrameButteraugli'
    ]
    
    @inject_self
    def calculate(
        self, reference: vs.VideoNode,
        distorted: vs.VideoNode,
        intensity_target: float = 80.0,
        linear: bool = False
    ) -> vs.VideoNode:

        heatmap = reference.julek.Butteraugli(
            distorted=distorted,
            intensity_target=intensity_target,
            linput=linear,
            distmap=True
        )
        
        clip = distorted.std.CopyFrameProps(prop_src=heatmap, props="_FrameButteraugli")
        self._register_metadata(clip)
        return clip
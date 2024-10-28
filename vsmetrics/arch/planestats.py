from typing import Optional
from vstools import vs, core, inject_self
from ..meta import MetricBase

__all__ = [
    "PlaneStatsDiff"
]

class PlaneStatsDiff(MetricBase):
    formats: list[int] = []  # all formats supported
    props: list[str] = ["PlaneStatsDiff"]
    
    @inject_self
    def calculate(self, distorted: vs.VideoNode, reference: vs.VideoNode, planes: Optional[int | list[int]] = None) -> vs.VideoNode:

        if planes is None:
            planes = list(range(reference.format.num_planes))   # type: ignore
        elif isinstance(planes, int):
            planes = [planes]
        
        #self.props = self._generate_props(self.props, reference.format.color_family, planes)
#
        #metric = self._process_planes(distorted, reference, planes, core.std.PlaneStats)
        metric = core.std.PlaneStats(distorted, reference)
        self._register_metadata(metric)
        return metric
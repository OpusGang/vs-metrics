from typing import Optional
from vstools import vs, core, inject_self
from ..meta import MetricBase

__all__ = [
    "PSNR"
]


class PSNR(MetricBase):
    formats: list[int] = [vs.GRAY10]  # all formats supported
    props: list[str] = ["psnr"]
    
    @inject_self
    def calculate(self, distorted: vs.VideoNode, reference: vs.VideoNode, planes: Optional[int | list[int]] = None) -> vs.VideoNode:

        if planes is None:
            planes = list(range(reference.format.num_planes))   # type: ignore
        elif isinstance(planes, int):
            planes = [planes]
        
        self.props = self._generate_props(self.props, reference.format.color_family, planes)   # type: ignore

        metric = self._process_planes(distorted, reference, planes, core.complane.PSNR)

        self._register_metadata(metric)
        return metric
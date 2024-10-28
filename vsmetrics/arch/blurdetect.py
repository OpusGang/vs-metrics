from vstools import inject_self, vs
from vsmetrics.meta import MetricBase
import numpy as np


class Blur(MetricBase):
    props: list[str] = ["blur"]
    formats: list[int] = [
        vs.GRAYS,
        vs.YUV420PS,
        vs.YUV422PS,
        vs.YUV444PS,
        vs.RGBS
    ]
    
    def __init__(self):
        from skimage.measure import blur_effect
        self.detect_blur = blur_effect

    @inject_self
    def calculate(self, reference: vs.VideoNode, planes: list[int] | int = 0) -> vs.VideoNode:
        self.validate_format(reference)

        if isinstance(planes, int):
            planes = [planes]

        self.props = self._generate_props(self.props, reference.format.color_family, planes)    # type: ignore
        clip = reference.std.ModifyFrame(reference, self._process_frame)

        self._register_metadata(clip)
        return clip

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        for i, plane in enumerate(self.props):
            arr = np.asarray(fout[i])
            difference = self.detect_blur(arr, h_size=11) # type: ignore [np.float32]
            fout.props[plane] = float(difference)   # type: ignore

        return fout

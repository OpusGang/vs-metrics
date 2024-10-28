from functools import partial
from vsrgtools import gauss_blur
from vstools import inject_self, vs, core

from ...meta import MetricBase

__all__ = [
    "Diff",
    "Diffv2"
]

class Diff(MetricBase):
    props: list[str] = ["scenechange"]
    formats: list[int] = [
        vs.GRAY8
    ]

    def __init__(self, thr: float = 0.15):
        self.thr = thr

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)
        
        offset = core.std.BlankClip(reference, length=1) + reference
        diff_clip = core.std.PlaneStats(reference, offset)
        
        prop = reference.std.SetFrameProp("scenechange", 1)

        diff_clip = core.akarin.Select(
            [reference, prop], diff_clip, f'x.PlaneStatsDiff {self.thr} >'
            )

        self._register_metadata(diff_clip)

        return diff_clip


class Diffv2(MetricBase):
    props: list[str] = ["scenechange"]
    formats: list[int] = [
        vs.GRAY8
    ]

    def __init__(self, thr: float = 0.15):
        self.thr = thr

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)
        
        blur = gauss_blur(reference)
        offset = core.std.BlankClip(blur, length=1) + blur
        diff_clip = core.std.PlaneStats(blur, offset)
        
        # state = []
        
        def blur_some_frames(n: int, f: vs.VideoFrame, clip: vs.VideoNode) -> vs.VideoNode:
            val: float = f.props["PlaneStatsDiff"]
            
            if val > self.thr:
                clip = clip.std.SetFrameProp("_debug", floatval=val)
                return clip.std.SetFrameProp("scenechange", 1)

            return clip.std.SetFrameProp("_debug", floatval=val)

        diff_clip = reference.std.FrameEval(
            eval=partial(blur_some_frames, clip=reference),
            prop_src=diff_clip
            )


        self._register_metadata(diff_clip)

        return diff_clip
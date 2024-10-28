from vstools import inject_self, vs, core

from ...meta import MetricBase

__all__ = [
    "Vectors"
]

class Vectors(MetricBase):
    props: list[str] = ["scenechange"]
    formats: list[int] = [
        vs.GRAY8,
        vs.GRAY10,
        vs.GRAY12,
        vs.GRAY14,
        vs.GRAY16,
    ]

    def __init__(self):
        ...

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)

        sup = reference.mv.Super()
        vec = sup.mv.Analyse(isb=True)
        clip = reference.mv.SCDetection(vec)
        
        stats = clip.std.PlaneStats()

        with_prop = reference.std.SetFrameProp("scenechange", 1)
        diff_clip = core.akarin.Select([reference, with_prop], stats, 'x.PlaneStatsMax 255 0 ?'
            )
        
        self._register_metadata(diff_clip)

        return clip
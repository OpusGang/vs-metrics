from vstools import inject_self, vs

from ...meta import MetricBase

__all__ = [
    "WWXD"
]

class WWXD(MetricBase):
    props: list[str] = ["Scenechange"]
    formats: list[int] = [
        vs.YUV420P8
    ]

    def __init__(self):
        ...

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)

        clip = reference.wwxd.WWXD()

        self._register_metadata(clip)

        return clip
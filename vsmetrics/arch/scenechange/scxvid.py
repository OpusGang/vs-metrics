from vstools import inject_self, vs

from ...meta import MetricBase

__all__ = [
    "SCXVID"
]

class SCXVID(MetricBase):
    props: list[str] = ["_SceneChangePrev"]
    formats: list[int] = [
        vs.YUV420P8
    ]

    def __init__(self):
        ...

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)

        clip = reference.scxvid.Scxvid()

        self._register_metadata(clip)

        return clip
from datetime import datetime
import os
from os import PathLike
from vstools import vs, core, clip_async_render
from pathlib import Path

class VMAFMetric:
    feature_id = None
    formats: list[int] = [
        vs.YUV410P12,
        vs.YUV420P12,
        vs.YUV422P12,
        vs.YUV444P12
    ]

    def __init__(self):
        if self.feature_id is None:
            raise ValueError("feature_id must be defined in subclass")

    def prefilter(self):
        ...

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:

        for input in (reference, distorted):
            if input.format.id not in VMAFMetric.formats:
                raise ValueError(f"Expected {self.formats} but got {input.format.name}")

        return core.vmaf.Metric(reference=reference, distorted=distorted, feature=self.feature_id)


class PSNR(VMAFMetric):
    feature_id = 0

class PSNRHVS(VMAFMetric):
    feature_id = 1

class SSIM(VMAFMetric):
    feature_id = 2

class MSSSIM(VMAFMetric):
    feature_id = 3

class CIEDE2000(VMAFMetric):
    feature_id = 4


class CAMBI:
    def calculate(
        self,
        reference: vs.VideoNode,
        window_size: int = 63,
        topk: float = 0.6,
        tvi_threshold: float = 0.019,
        scores: bool = False,
        scaling: float = None
    ) -> vs.VideoNode:

        return reference.akarin.Cambi(
            window_size=window_size,
            topk=topk,
            tvi_threshold=tvi_threshold,
            scores=scores,
            scaling=scaling
            )


class VMAF:
    @staticmethod
    def get_log_path(method_name: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        subdir_name = ".vsmetrics"

        subdir_path = os.path.join(os.getcwd(), subdir_name)

        os.makedirs(subdir_path, exist_ok=True)

        return Path(subdir_path) / f"{method_name}_{timestamp}.txt"

    def vmaf(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> None:
        log_path = self.get_log_path("vmaf")

        _vmaf = core.vmaf.VMAF(
            reference=reference,
            distorted=distorted,
            log_path=str(log_path),
            model=1
            )

        clip_async_render(_vmaf, outfile=None, progress="calculating VMAF")

    def cambi(self, reference: vs.VideoNode) -> None:
        log_path = self.get_log_path("cambi")

        _cambi = core.vmaf.CAMBI(
            clip=reference,
            log_path=str(log_path)
            )

        clip_async_render(_cambi, outfile=None, progress="calculating CAMBI")

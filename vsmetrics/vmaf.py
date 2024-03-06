from dataclasses import dataclass
from datetime import datetime
import os
from vstools import vs, core, clip_async_render
from pathlib import Path
from .util import validate_format

class VMAFMetric:
    feature_id: None | int = None
    formats: tuple[int, ...] = (
        vs.YUV410P12,
        vs.YUV420P12,
        vs.YUV422P12,
        vs.YUV444P12
    )
    
    def __init__(self):
        if self.feature_id is None:
            raise ValueError("feature_id must be defined in subclass")

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        """
        Calculates the metric score between two video nodes.

        Args:
            reference (vs.VideoNode): The reference video node.
            distorted (vs.VideoNode): The distorted video node.

        Returns:
            distorted (vs.VideoNode) with frame props

        Raises:
            ValueError: If one of the inputs has an unsupported format.
            """

        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)

        return core.vmaf.Metric(reference=reference, distorted=distorted, feature=self.feature_id)  # type: ignore


class PSNRHVS(VMAFMetric):
    feature_id = 1

class SSIM(VMAFMetric):
    feature_id = 2

class MSSSIM(VMAFMetric):
    feature_id = 3

class CIEDE2000(VMAFMetric):
    feature_id = 4


class CAMBI:
    formats: tuple[int, ...] = (
        vs.GRAY8,
        vs.GRAY10,
        vs.YUV420P8,
        vs.YUV422P8,
        vs.YUV444P8,
        vs.YUV410P8,
        vs.YUV411P8,
        vs.YUV440P8,
        vs.YUV420P10,
        vs.YUV422P10,
        vs.YUV444P10
    )

    def __init__(self,
        window_size: int = 63,
        topk: float = 0.6,
        tvi_threshold: float = 0.019,
        scaling: None | float = None
    ):
        
        """
        Compute CAMBI banding score as CAMBI frame property.

        :param window_size:        Window size to compute CAMBI. Range: min=15, max=127, default=63 (corresponds to ~1 deg at 4K res & 1.5H).
        :param topk:               Ratio of pixels for spatial pooling computation. Range: min=0.0001, max=1.0, default=0.6.
        :param tvi_threshold:      Visibility threshold for luminance ΔL < tvi_threshold * L_mean for BT.1886. Range: min=0.0001, max=1.0, default=0.019.
        :param scaling:            Scaling factor used to normalize c-scores for each scale when ``scores`` is True. Default: 1.0 divided by ``window_size``.

        :return: New Clip object containing input clip with added frame properties representing calculated CAMBI scores.
        """

        self.window_size = window_size
        self.topk = topk
        self.tvi_threshold = tvi_threshold
        self.scaling = scaling
        self.cambi = None

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        """
        :param clip:               Input clip. Must be in Grayscale or YUV format with integer sample type of 8/10 bit depth (subsampling can be arbitrary as cambi only uses the Y channel).
        """

        validate_format(reference, self.formats)

        self.cambi = reference.akarin.Cambi(
            window_size=self.window_size,
            topk=self.topk,
            tvi_threshold=self.tvi_threshold,
            scaling=self.scaling,
            scores=True
        )

        return self.cambi

    def mask(self) -> list[vs.VideoNode]:
        if self.cambi:
            return [self.cambi.std.PropToClip('CAMBI_SCALE%d' % i) for i in range(5)]
        else:
            raise ValueError("Cambi object not yet created. Call calculate() first.")


class VMAF:
    def get_log_path(self, method_name: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        subdir_name = ".vsmetrics"

        subdir_path = os.path.join(os.getcwd(), subdir_name)

        os.makedirs(subdir_path, exist_ok=True)

        return Path(subdir_path) / f"{method_name}_{timestamp}.txt"

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> None:
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

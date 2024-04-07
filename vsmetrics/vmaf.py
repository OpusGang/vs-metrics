from datetime import datetime
import os
from vstools import vs, core, clip_async_render
from pathlib import Path
from .util import name, validate_format, MetricVideoNode

class VMAFMetric:
    feature_id: int
    formats: tuple[int, ...] = (
        vs.YUV410P12,
        vs.YUV420P12,
        vs.YUV422P12,
        vs.YUV444P12
    )

    def __init__(self):
        if not hasattr(self, 'feature_id') or self.feature_id is None:
            raise ValueError("feature_id must be defined in subclass")

    def calculate(self, reference, distorted) -> vs.VideoNode | MetricVideoNode:
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

        clip = core.vmaf.Metric(
            reference=reference, distorted=distorted, feature=self.feature_id  # type: ignore
        )

        return MetricVideoNode(clip, self)

    @property
    def props(self) -> list[str]:
        raise NotImplementedError("props must be defined in subclass")


class PSNRHVS(VMAFMetric):
    feature_id = 1
    props: list[str] = [
        'psnr_hvs_y',
        'psnr_hvs_cb',
        'psnr_hvs_cr',
        'psnr_hvs'
    ]


class SSIM(VMAFMetric):
    feature_id = 2
    props: list[str] = [
        'float_ssim'
    ]


class MSSSIM(VMAFMetric):
    feature_id = 3
    props: list[str] = [
        'float_ms_ssim'
    ]


class CIEDE2000(VMAFMetric):
    feature_id = 4
    props: list[str] = [
        'ciede2000'
    ]
    
# add as fallback or something
# less CPU but less throughput

#class PSNR(VMAFMetric):
#    feature_id = 0
#class SSIM2(VMAFMetric):
#    feature_id = 2

class CAMBI:
    formats: list[int] = [
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
    ]

    props: list[str] = [
        'CAMBI'
    ]

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
        self.cambi: vs.VideoNode

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:
        """
        :param clip:               Input clip. Must be in Grayscale or YUV format with integer sample type of 8/10 bit depth (subsampling can be arbitrary as cambi only uses the Y channel).
        """

        validate_format(reference, self.formats) # type: ignore

        self.cambi = reference.akarin.Cambi(
            window_size=self.window_size,
            topk=self.topk,
            tvi_threshold=self.tvi_threshold,
            scaling=self.scaling,
            scores=True
        )

        return MetricVideoNode(self.cambi, self)

    def mask(self, merge: bool = True, scale: float = 2) -> list[vs.VideoNode] | vs.VideoNode:
        if self.cambi:
            obj =  [self.cambi.std.PropToClip('CAMBI_SCALE%d' % i) for i in range(5)]
        
            if merge:
                from vsexprtools import combine, ExprOp
                from vskernels import Point

                cambi_masks = [Point.scale(i, self.cambi.width, self.cambi.height) for i in obj]
 
                banding_mask = combine(
                    cambi_masks, ExprOp.ADD, zip(range(1, 6), ExprOp.LOG, ExprOp.MUL),
                    expr_suffix=[ExprOp.SQRT, scale, ExprOp.LOG, ExprOp.MUL]
                ).std.Convolution([1, 2, 1, 2, 4, 2, 1, 2, 1])

                return banding_mask

            return obj
        else:
            raise ValueError("Cambi object not yet created. Call calculate() first.")


# .eval method hack
# write vmaf to file in frameeval
# probably slow!
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

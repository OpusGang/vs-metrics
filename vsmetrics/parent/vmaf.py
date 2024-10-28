from vstools import inject_self, vs, core

from ..meta import MetricBase

class HolyVMAF(MetricBase):

    class Metric:
        """
        https://github.com/HomeOfVapourSynthEvolution/VapourSynth-VMAF/blob/master/VMAF/VMAF.cpp#L513-L535
        """
        PSNR = 0
        PSNR_HVS = 1
        SSIM = 2
        MS_SSIM = 3
        CIEDE2000 = 4
    
    class Props:
        """
        https://github.com/HomeOfVapourSynthEvolution/VapourSynth-VMAF/blob/master/VMAF/VMAF.cpp#L513-L535
        """
        PSNR = ["psnr_y", "psnr_cb", "psnr_cr"]
        PSNR_HVS = ["psnr_hvs_y", "psnr_hvs_cb", "psnr_hvs_cr", "psnr_hvs"]
        SSIM = ["float_ssim"]
        MS_SSIM = ["float_ms_ssim"]
        CIEDE2000 = ["ciede2000"]

    """
    HolyWu VMAF implementation of simple metrics
    https://github.com/HomeOfVapourSynthEvolution/VapourSynth-VMAF
    """

    feature_id: int
    props: list[str]
    formats: list[int] = [
        vs.YUV420P12,
        vs.YUV422P12,
        vs.YUV444P12
    ]

    def __init__(self):
        if not hasattr(self, 'feature_id') or self.feature_id is None:
            raise ValueError("feature_id must be defined in subclass")

    @inject_self
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        """
        Calculates the metric score between two VideoNodes.

        Args:
            reference (vs.VideoNode): The reference VideoNode.
            distorted (vs.VideoNode): The distorted VideoNode.

        Returns:
            distorted (vs.VideoNode) with frame props

        Raises:
            ValueError: If one of the inputs has an unsupported format.
            """

        self.validate_format(reference)
        self.validate_format(distorted)

        clip = core.vmaf.Metric(
            reference=reference, distorted=distorted, feature=self.feature_id  # type: ignore
        )

        self._register_metadata(clip)
        return clip
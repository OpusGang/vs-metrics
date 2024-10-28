from ..parent.vmaf import HolyVMAF

__all__ = ["MSSSIM"]

class MSSSIM(HolyVMAF):
    formats = HolyVMAF.formats
    feature_id = HolyVMAF.Metric.MS_SSIM
    props: list[str] = [
        'float_ms_ssim'
    ]

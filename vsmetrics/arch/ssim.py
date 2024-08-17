from ..parent.vmaf import VMAFMetric

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

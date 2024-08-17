from ..parent.vmaf import VMAFMetric

class PSNR(VMAFMetric):
    feature_id = 0
    props: list[str] = [
        'psnr_y',
        'psnr_cb',
        'psnr_cr',
    ]

class PSNRHVS(VMAFMetric):
    feature_id = 1
    props: list[str] = [
        'psnr_hvs_y',
        'psnr_hvs_cb',
        'psnr_hvs_cr',
        'psnr_hvs'
    ]
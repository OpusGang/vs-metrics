from ..parent.vmaf import HolyVMAF

__all__ = ["PSNRHVS"]

class PSNRHVS(HolyVMAF):
    feature_id = HolyVMAF.Metric.PSNR_HVS
    props: list[str] = HolyVMAF.Props.PSNR_HVS

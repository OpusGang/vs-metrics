from vsmetrics.parent.vmaf import HolyVMAF

class CIEDE2000(HolyVMAF):
    feature_id = HolyVMAF.Metric.CIEDE2000
    props: list[str] = HolyVMAF.Props.CIEDE2000

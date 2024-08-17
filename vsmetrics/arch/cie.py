from ..parent.vmaf import VMAFMetric

class CIEDE2000(VMAFMetric):
    feature_id = 4
    props: list[str] = [
        'ciede2000'
    ]
from vstools import vs, core

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

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:

        #for input in (reference, distorted):
        #    if input.format.name not in VMAFMetric.formats:
        #        raise ValueError(f"Expected {self.formats} but got {input.format.name}")

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
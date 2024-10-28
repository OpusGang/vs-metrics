from vstools import inject_self, vs, plane as _plane

from ..parent.vmaf import HolyVMAF
from ..meta import MetricBase

class _FallbackSSIM(HolyVMAF):
    feature_id = 2
    props = ['float_ssim']


class SSIM(MetricBase):
    formats = [
        vs.GRAY8,
        vs.GRAY10,
        vs.GRAY12,
        vs.GRAY14,
        vs.GRAY16,
        vs.GRAYS
    ]
    
    props = ["PlaneSSIM"]

    def __init__(
        self,
        plane: int = 0,
        k1: float = 0.01,
        k2: float = 0.03,
        dynamic_range: int = 1
    ):

        self.plane = plane
        self.k1 = k1
        self.k2 = k2
        self.dynamic_range = dynamic_range

    @inject_self
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode, plane: int = 0) -> vs.VideoNode:
        try:
            from muvsfunc import SSIM as _SSIM
            
            reference = _plane(reference, plane)
            distorted = _plane(distorted, plane)
            
            self.validate_format(reference)
            self.validate_format(distorted)

            ssim_map = _SSIM(reference, distorted, plane=self.plane, downsample=False,
                             k1=self.k1, k2=self.k2, dynamic_range=self.dynamic_range, show_map=True)

            ssim_clip = distorted.std.CopyFrameProps(ssim_map, self.props[0])
            return ssim_clip.std.ClipToProp(
                ssim_map.std.RemoveFrameProps("_Matrix"),
                prop="PlaneSSIM_map"
            )

        except ImportError:
            print("muvsfunc missing, falling back to limited VMAF implementation")
            try:
                return _FallbackSSIM.calculate(reference, distorted)
            except ImportError:
                raise ImportError("Both muvsfunc and VMAF are missing. Cannot proceed with SSIM calculation.")

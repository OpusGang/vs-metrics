from numpy._typing import NDArray
from vstools import vs, core
from scipy.ndimage import gaussian_filter
import numpy as np
from ..meta import MetricBase


class VIF(MetricBase):
    """igv ver"""
    props: list[str] = ["VIF"]
    formats: list[int] = [
        vs.RGBS
        ]
    
    def __init__(self):
        self.gaussian_filter = gaussian_filter

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)

        clip = reference.std.ModifyFrame([reference, distorted], self._process_frame)
        self._register_metadata(clip)
        return clip

    def _process_frame(self, n: int, f: list[vs.VideoFrame]) -> vs.VideoFrame:
        f1, f2 = f
        fout = f1.copy()

        arr1 = np.asarray(f1[0])
        arr2 = np.asarray(f2[0])

        difference = self._vif(arr1, arr2)

        fout.props[self.props[0]] = float(difference)

        return fout
    
    def _vif(self, reference: NDArray, distorted: NDArray):
        sigma_nsq = 0.5
        eps = 1e-5

        num = 0.0
        den = 0.0

        for scale in range(1, 5):
            N = 2**(4-scale+1) + 1
            sd, t = N/3.0, 1.4  # kernel radius = round(sd * truncate)

            if scale == 2:
                sigma_nsq = .1

            if scale > 1:
                reference = self.gaussian_filter(reference, 1.08, truncate=1.5)[::2, ::2]
                distorted = self.gaussian_filter(distorted, 1.08, truncate=1.5)[::2, ::2]

            L1 = np.where(reference > 0.008856, np.power(reference, 1./3.) * 116 - 16, reference * 903.3)
            L2 = np.where(distorted > 0.008856, np.power(distorted, 1./3.) * 116 - 16, distorted * 903.3)

            mu1 = self.gaussian_filter(L1, sd, truncate=t)
            mu2 = self.gaussian_filter(L2, sd, truncate=t)

            mu1_sq = mu1 * mu1
            mu2_sq = mu2 * mu2
            mu1_mu2 = mu1 * mu2

            sigma1_sq = self.gaussian_filter(L1 * L1, sd, truncate=t) - mu1_sq
            sigma2_sq = self.gaussian_filter(L2 * L2, sd, truncate=t) - mu2_sq

            sigma12 = self.gaussian_filter(L1 * L2, sd, truncate=t) - mu1_mu2

            sigma1_sq[sigma1_sq<eps] = eps
            sigma2_sq[sigma2_sq<eps] = eps

            sigma12[sigma12<eps] = eps

            g = sigma12 / sigma1_sq
            sv_sq = sigma2_sq - g * sigma12

            g[sigma1_sq<sigma_nsq] = 1
            sv_sq[sv_sq<0] = 0

            num += np.sum(np.log2(1 + g * g * sigma1_sq / (sv_sq + sigma_nsq)))
            den += np.sum(np.log2(1 + sigma1_sq / sigma_nsq))

        return num/den
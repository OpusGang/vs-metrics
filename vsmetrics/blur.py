from enum import Enum
import cv2
import numpy as np
from vstools import vs, core
from .util import validate_format
from .meta import BaseUtil, MetricVideoNode
from skimage.measure import blur_effect
from skimage.feature import local_binary_pattern
from skimage.feature import graycomatrix, graycoprops
from scipy.ndimage import gaussian_filter
from typing import Any
from numpy.typing import NDArray

#import numpy
#class NumpyHelper():
#    def get_read_array(self, index) -> NDArray:
#        return numpy.asarray(self[index])
#
#    def get_write_array(self, index) -> NDArray:
#        if not self.f:
#            raise Error("frame is not writable")
#        return self.get_read_array(index)
#    
#    def frame_to_array(self, f: vs.VideoFrame) -> NDArray[Any]:
#        return np.dstack([self.get_read_array(f[i]) for i in range(f.format.num_planes)]) 
#
#    def array_to_frame(self, array: NDArray[Any], frame: vs.VideoFrame) -> vs.VideoFrame:
#        fout = frame.copy()
#
#        for plane in range(fout.format.num_planes):
#            np.copyto(
#                np.asarray(fout[plane]),
#                array[plane, ...]
#            )
#
#        return fout

class VIF(BaseUtil):
    props: list[str] = ["VIF"]
    formats: tuple[int, ...] = (
        vs.RGBS,
    )

    def __init__(self):
        self.gaussian_filter = gaussian_filter

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:
        validate_format(reference, self.formats)

        clip = reference.std.ModifyFrame([reference, distorted], self._process_frame)
        return MetricVideoNode(clip, self)

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

class Blur(BaseUtil):
    props: list[str] = ["blur"]
    formats: tuple[int, ...] = (
        vs.GRAYS,
        vs.YUV420PS,
        vs.YUV422PS,
        vs.YUV444PS,
        vs.RGBS
    )
    
    def __init__(self):
        self.detect_blur = blur_effect

    def calculate(self, reference: vs.VideoNode, planes: list[int] | int = 0) -> vs.VideoNode | MetricVideoNode:
        validate_format(reference, self.formats)

        if isinstance(planes, int):
            planes = [planes]

        self.props = self._generate_props(self.props, reference.format.color_family, planes)

        clip = reference.std.ModifyFrame(reference, self._process_frame)
        return MetricVideoNode(clip, self)

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()
        
        f = [f[n] for n in range(len(self.props))]

        for i, plane in enumerate(self.props):
            arr = np.asarray(f[i])
            difference = self.detect_blur(arr, h_size=11)
            fout.props[plane] = float(difference)

        return fout


class LocaLBinaryPattern(BaseUtil):
    props: list[str] = ["texture"]
    formats: tuple[int, ...] = (
        vs.GRAYS,
    )
    
    class Methods(str, Enum):
        DEFAULT = 'default'
        ROR = 'ror'
        UNIFORM = 'uniform'
        NRI_UNIFORM = 'nri_uniform'
        VAR = 'var'

    class LocaLBinaryPatternVideoNode(MetricVideoNode):
        def __init__(self, clip: vs.VideoNode, lbp_map: vs.VideoNode, metric):
            super().__init__(clip, metric)
            self.lbp_map_node = lbp_map

        def lbp_map(self) -> vs.VideoNode:
            return self.lbp_map_node

    def __init__(self, radius: int = 3, n_points = int, method: Methods = Methods.UNIFORM):
        self.radius = radius
        self.n_points = 8 * self.radius if n_points else n_points
        self.method = method
        
        self.lbp = local_binary_pattern
        self.hist = np.histogram

    def calculate(self, reference: vs.VideoNode) -> LocaLBinaryPatternVideoNode | vs.VideoNode:
        validate_format(reference, self.formats)

        processed_clip = reference.std.ModifyFrame(reference, self._process_frame)
        output_clip = reference.std.CopyFrameProps(prop_src=processed_clip, props=self.props)

        return self.LocaLBinaryPatternVideoNode(output_clip, processed_clip, self)

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout_props = f.copy()

        arr = np.asarray(f[0])
        score, lbp_map = self._process(arr)
        fout_props.props[self.props[0]] = float(score)
        np.copyto(np.asarray(fout_props[0]), lbp_map)

        return fout_props

    def _process(self, frame) -> tuple[float, Any]:
        lbp = self.lbp(frame, self.n_points, self.radius, self.method)

        n_bins = int(lbp.max() + 1)
        hist, _ = self.hist(lbp.ravel(), bins=n_bins, range=(0, n_bins))

        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)

        score = -np.sum(hist * np.log2(hist + 1e-7))

        lbp_map = (lbp / lbp.max() * 255).astype(np.uint8)

        return score, lbp_map

# make parent class so props can be autocompleted
#   class GLCMProps:
#       texture_contrast = "texture_contrast"
#       texture_dissimilarity = "texture_dissimilarity"
#       texture_homogeneity = "texture_homogeneity"
#       texture_energy = "texture_energy"
#       texture_correlation = "texture_correlation"

class GLCM(BaseUtil):
    props: list[str] = [
        "texture_contrast",
        "texture_dissimilarity",
        "texture_homogeneity",
        "texture_energy",
        "texture_correlation"
    ]

    formats: tuple[int, ...] = (
        vs.GRAYS,
    )

    def calculate(self, reference: vs.VideoNode, planes: int = 0) -> vs.VideoNode | MetricVideoNode:
        validate_format(reference, self.formats)

        if isinstance(planes, int):
            planes = [planes]

        self.output_props = self._generate_props(self.props, reference.format.color_family, planes)

        clip = reference.std.ModifyFrame(reference, self._process_frame)
        return MetricVideoNode(clip, self)

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        for i in range(f.format.num_planes):
            arr = np.asarray(f[0])
            features = self._process(arr)
            for feature, value in features.items():
                fout.props[feature] = float(value)

        return fout

    def _process(self, frame) -> dict[str, any]:
        frame = (frame * 255).astype(np.uint8)

        glcm = graycomatrix(
            frame,
            distances=[1],
            angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
            levels=256,
            symmetric=True,
            normed=True
        )

        contrast = graycoprops(glcm, 'contrast')[0, 0]
        dissimilarity = graycoprops(glcm, 'dissimilarity')[0, 0]
        homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
        energy = graycoprops(glcm, 'energy')[0, 0]
        correlation = graycoprops(glcm, 'correlation')[0, 0]
        # TODO
        # return list here
        features = {
            'texture_contrast': contrast,
            'texture_dissimilarity': dissimilarity,
            'texture_homogeneity': homogeneity,
            'texture_energy': energy,
            'texture_correlation': correlation
        }

        return features

class Sharpness(BaseUtil):
    props: list[str] = ["sharpness"]
    formats: tuple[int, ...] = (
        vs.GRAYS,
    )

    def calculate(self, reference: vs.VideoNode, planes: list[int] | int = 0) -> vs.VideoNode | MetricVideoNode:
        validate_format(clip, self.formats)

        if isinstance(planes, int):
            planes = [planes]

        self.output_props = self._generate_props(self.props, reference.format.color_family, planes)

        clip = reference.std.ModifyFrame(reference, self._process_frame)
        return MetricVideoNode(reference, self)

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        for i in range(f.format.num_planes):
            arr = np.asarray(f[i])
            blur_score = self._laplacian(arr)
            fout.props[self.output_props[i]] = float(blur_score)

        return fout

    def _laplacian(self, frame):
        frame = (frame * 255).astype(np.uint8)

        laplacian = cv2.Laplacian(frame, cv2.CV_64F)

        blur_score = laplacian.var()

        return blur_score

class BRISQUE(BaseUtil):
    def __init__(self, model, range):
        self.model = model
        self.range = range
        self.filter = cv2.quality.QualityBRISQUE_create(self.model, self.range)  # type: ignore

    props: list[str] = ["BRISQUE"]
    formats: tuple[int, ...] = (
        vs.GRAYS,
    )

    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:
        validate_format(reference, self.formats)

        self.output_props = self.props[0]

        clip = reference.std.ModifyFrame(reference, self._process_frame)
        return MetricVideoNode(clip, self)

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        arr = np.asarray(f[0])
        sharpness_score = self._brisque(arr)
        fout.props[self.output_props] = float(sharpness_score)

        return fout

    def _brisque(self, frame):
        frame = (frame * 255).astype(np.uint8)

        sharpness_score = self.filter.compute(frame)

        return sharpness_score[0]

class SVD(BaseUtil):
    props: list[str] = [
        "compression_error",
        "texture_entropy",
        "texture_energy",
        "singular_value_spectrum",
        "singular_value_ratio",
        "left_singular_vector_entropy",
        "right_singular_vector_entropy",
        "percentage_retained"
        ]

    formats: tuple[int, ...] = (
        vs.RGBS,
    )

    def calculate(self, reference: vs.VideoNode, planes: list[int] | int = 0) -> vs.VideoNode | MetricVideoNode:
        validate_format(reference, self.formats)

        if isinstance(planes, int):
            planes = [planes]

        self.props = self._generate_props(self.props, reference.format.color_family, planes)
        print(self.props)
        clip = reference.std.ModifyFrame(reference, self._process_frame)
        return MetricVideoNode(clip, self)

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        for _, k in enumerate([0, 1, 2]):
            arr = np.asarray(f[k])
            score = self._process(arr)
            for i in range(len(score)):
                fout.props[self.props[i]] = float(score[i])

        print(fout.props)
        return fout

    def _process(self, frame) -> list:
        U, S, VT = np.linalg.svd(frame)

        compression_ratio = 0.1
        k = int(compression_ratio * len(S))
        compressed_image = U[:, :k] @ np.diag(S[:k]) @ VT[:k, :]
        compression_error = np.sum((frame - compressed_image) ** 2)

        texture_entropy = -np.sum(S * np.log2(S))
        texture_energy = np.sum(S ** 2)
        
        singular_value_spectrum = np.mean(S / np.sum(S))

        singular_value_ratio = S[0] / np.sum(S)

        left_singular_vector_entropy = -np.sum(U[:, 0]**2 * np.log2(U[:, 0]**2))
        right_singular_vector_entropy = -np.sum(VT[0, :]**2 * np.log2(VT[0, :]**2))

        threshold = 0.1
        num_retained_values = np.sum(S > threshold)
        percentage_retained = num_retained_values / len(S)

        return [
            compression_error,
            texture_entropy,
            texture_energy,
            singular_value_spectrum,
            singular_value_ratio,
            left_singular_vector_entropy,
            right_singular_vector_entropy,
            percentage_retained
        ]
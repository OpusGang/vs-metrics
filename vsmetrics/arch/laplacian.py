import numpy as np
from scipy import ndimage
from enum import Enum
from typing import Callable

from vstools import vs, inject_self

from vsmetrics.meta import MetricBase

class LaplacianMethod(Enum):
    VARIANCE_OF_LAPLACIAN = 'VarianceOfLaplacian'
    MODIFIED_LAPLACIAN = 'ModifiedLaplacian'
    ENERGY_OF_LAPLACIAN = 'EnergyOfLaplacian'
    TENENGRAD = 'Tenengrad'

class Laplacian(MetricBase):
    """
    Supported Methods:
        - Variance of Laplacian
        - Modified Laplacian
        - Energy of Laplacian
        - Tenengrad

    Usage:
        metric = Laplacian(method=LaplacianMethod.TENENGRAD)
        output_clip = metric.calculate(input_clip)
    """
    props: list[str] = ["Laplacian"]
    formats: list[int] = [vs.GRAY8, vs.GRAY16, vs.GRAY32]

    def __init__(self, method: LaplacianMethod = LaplacianMethod.TENENGRAD):
        super().__init__()
        self.method = method

        if self.method == LaplacianMethod.VARIANCE_OF_LAPLACIAN:
            self._compute_focus_score: Callable[[np.ndarray], float] = self._variance_of_laplacian
        elif self.method == LaplacianMethod.MODIFIED_LAPLACIAN:
            self.kernelx = np.array([[0, 0, 0],
                                     [-1, 2, -1],
                                     [0, 0, 0]], dtype=np.float32)
            self.kernely = np.array([[0, -1, 0],
                                     [0, 2, 0],
                                     [0, -1, 0]], dtype=np.float32)
            self._compute_focus_score = self._modified_laplacian
        elif self.method == LaplacianMethod.ENERGY_OF_LAPLACIAN:
            self._compute_focus_score = self._energy_of_laplacian
        elif self.method == LaplacianMethod.TENENGRAD:
            self._compute_focus_score = self._tenengrad
        else:
            raise ValueError(f"Unsupported Laplacian method: {self.method}")

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        """
        Calculate the Laplacian-based focus measure for each frame in the clip.

        Parameters:
            reference (vs.VideoNode): The input video clip.

        Returns:
            vs.VideoNode
        """
        self.validate_format(reference)
        self.output_props = self.props[0]

        clip = reference.std.ModifyFrame(reference, self._process_frame)
        self._register_metadata(clip)
        return clip

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:

        fout = f.copy()

        arr = np.asarray(f[0], dtype=np.float32)
        focus_score = self._compute_focus_score(arr)
        fout.props[self.output_props] = float(focus_score)

        return fout

    def _variance_of_laplacian(self, img: np.ndarray) -> float:
        """
        Compute the variance of the Laplacian of the image.

        Parameters:
            img (np.ndarray): Grayscale image.

        Returns:
            float: Variance of the Laplacian.
        """
        lap = ndimage.laplace(img, mode='reflect')
        return float(np.var(lap))

    def _modified_laplacian(self, img: np.ndarray) -> float:
        """
        Compute the modified Laplacian of the image.

        Parameters:
            img (np.ndarray): Grayscale image.

        Returns:
            float: Mean of the absolute gradients in both directions.
        """
        lx = ndimage.convolve(img, self.kernelx, mode='reflect')
        ly = ndimage.convolve(img, self.kernely, mode='reflect')
        return float((np.abs(lx) + np.abs(ly)).mean())

    def _energy_of_laplacian(self, img: np.ndarray) -> float:
        """
        Compute the energy (mean squared value) of the Laplacian of the image.

        Parameters:
            img (np.ndarray): Grayscale image.

        Returns:
            float: Mean squared Laplacian.
        """
        lap = ndimage.laplace(img, mode='reflect')
        return float(np.mean(lap ** 2))

    def _tenengrad(self, img: np.ndarray) -> float:
        """
        Compute the Tenengrad focus measure of the image.

        Parameters:
            img (np.ndarray): Grayscale image.

        Returns:
            float: Mean gradient magnitude.
        """
        gx = ndimage.sobel(img, axis=1, mode='reflect')
        gy = ndimage.sobel(img, axis=0, mode='reflect')

        magnitude = np.hypot(gx, gy)
        return float(magnitude.mean())

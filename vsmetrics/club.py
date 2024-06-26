from enum import Enum
from functools import partial
from os import PathLike
from typing import Optional, TypedDict
from vstools import padder, split, vs, core, mod_x, merge_clip_props
from .util import validate_format, name
from .meta import BaseUtil, MetricVideoNode


class GMSD:
    props: list[str] = ["PlaneGMSD"]
    formats: tuple[int, ...] = (
        vs.GRAYS,
        vs.RGBS,
        vs.YUV444PS
    )

    def __init__(self, plane: None | int = None, downsample: bool = True, c: float = 0.0026):
        self.plane = plane
        self.downsample = downsample
        self.c = c

    class GMSDVideoNode(MetricVideoNode):
        def __init__(self, clips: tuple[vs.VideoNode, ...], metric):
            super().__init__(clips[0], metric)
            self._gradient_map = clips[1]

        def gradient_map(self) -> vs.VideoNode:
            return self._gradient_map

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> GMSDVideoNode:
        from muvsfunc import GMSD as _GMSD

        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)

        measure = _GMSD(
            reference,
            distorted,
            self.plane,
            self.downsample,
            self.c,
            True  # type: ignore
        )  # type: ignore

        measure = (
            core.std.CopyFrameProps(distorted, measure, self.props),
            measure
        )

        return self.GMSDVideoNode(measure, self)


class SSIM:
    props: list[str] = ["PlaneSSIM"]
    formats: tuple[int, ...] = (
        vs.GRAY8,
        vs.GRAY16
    )

    def __init__(
        self,
        plane: Optional[int] = None,
        downsample: bool = True,
        k1: float = 0.01,
        k2: float = 0.03,
        dynamic_range: int = 1
    ):
        self.plane = plane
        self.down_scale = downsample
        self.dynamic_range = dynamic_range
        self.k1 = k1
        self.k2 = k2

    class SSIMVideoNode(MetricVideoNode):
        def __init__(self, clips: tuple[vs.VideoNode, ...], metric):
            super().__init__(clips[0], metric)
            self._map = clips[1]

        def map(self) -> vs.VideoNode:
            return self._map

    def calculate(
        self,
        reference: vs.VideoNode,
        distorted: vs.VideoNode
    ) -> SSIMVideoNode | vs.VideoNode:
        from muvsfunc import SSIM as _SSIM

        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)

        measure = _SSIM(
            reference,
            distorted,
            None,
            False,  # type: ignore
            self.k1,
            self.k2,
            self.dynamic_range,  # type: ignore
            show_map=True
        )  # type: ignore

        measure = (
            core.std.CopyFrameProps(
                distorted,
                measure,
                self.props
            ), measure
        )

        return self.SSIMVideoNode(measure, self)

class MDSI:
    props: list[str] = ["FrameMDSI"]
    formats: tuple[int, ...] = (
        vs.RGB24,
        vs.RGB48,
        vs.RGBS
    )

    def __init__(self, alpha: float = 0.6):
        self.alpha = alpha

    class MDSIVideoNode(MetricVideoNode):
        def __init__(self, clips: tuple[vs.VideoNode, ...], metric):
            super().__init__(clips[0], metric)
            self._gs_map = clips[1]
            self._cs_map = clips[2]
            self._gcs_map = clips[3]

        def gradient_map(self) -> vs.VideoNode:
            return self._gs_map.std.RemoveFrameProps("_Matrix")

        def chromaticity_map(self) -> vs.VideoNode:
            return self._cs_map.std.RemoveFrameProps("_Matrix")

        def gradient_chromaticity_map(self) -> vs.VideoNode:
            return self._gcs_map.std.RemoveFrameProps("_Matrix")

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> MDSIVideoNode | vs.VideoNode:
        from muvsfunc import MDSI as _MDSI

        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)

        measure = _MDSI(
            reference,
            distorted,
            1.0,  # type: ignore
            self.alpha,
            show_maps=True
        )

        return self.MDSIVideoNode(measure, self) # type: ignore

@name
class PSNR:
    def __init__(
        self,
        weights: bool | list[float] = False,
        opt: int = 0,
        cache: int = 1
    ):
        """
        Initializes the PSNR object.

        Args:
            weights (bool | list[float], optional): Weights for calculating the weighted average of PSNR values.
                - If False (default), no weights are applied.
                - If True, weights are automatically determined based on the color family of the reference clip.
                - If a list of floats is provided, the weights are used as specified.
                The length of the weights list should match the number of planes in the reference clip.
            opt (int, optional): Optimization level.
                - 0: Auto-detect (default)
                - 1: AVX
                - 2: AVX2
            cache (int, optional): Whether the output should be cached or not. Disabling cache may slightly improve performance.
                If you want to access the results later, it's recommended to enable caching.
                - 0: Disable caching
                - 1: Enable caching (default)
        """
        self.weights = weights
        self._reference = None
        self.opt = opt
        self.cache = cache

        # RGB: BT.709
        # HVS: vmaf third_party/xiph/psnr_hvs.c

        self.cie = dict(
            RGB=[0.299, 0.587, 0.114],
            YCbCr=[0.7, 0.15, 0.15],
            PSNR_HVS=[0.8, 0.1, 0.1]
        )

    def _set_reference(self, reference: vs.VideoNode) -> None:
        self._reference = reference

        if self.weights == True:
            if reference.format.color_family == vs.YUV:  # type: ignore
                self.weights = self.cie['YCbCr']
            elif reference.format.color_family == vs.RGB:  # type: ignore
                self.weights = self.cie['RGB']
            else:
                self.weights = False

    def set_prop(self, n, f, props):
        fout = f.copy()
    
        psnr_values = []
        plane_weights = []
    
        for i, prop in enumerate(props):
            psnr = fout.props.get(prop)
            if psnr is not None:
                psnr_values.append(psnr)
                plane_weights.append(self.weights[i])  # type: ignore
    
        weight_sum = sum(plane_weights)
        normalized_weights = [weight / weight_sum for weight in plane_weights]
    
        fout.props['psnr'] = (
            sum(weight * psnr for weight, psnr in zip(normalized_weights, psnr_values))
            if weight_sum != 0 else None
        )

        return fout

    @property
    def props(self) -> list[str]:
        color_family = self._reference.format.color_family  # type: ignore

        props = {
            vs.YUV: ["psnr_y", "psnr_cb", "psnr_cr"],
            vs.RGB: ["psnr_r", "psnr_g", "psnr_b"],
            vs.GRAY: ["psnr_gray"],
        }.get(color_family, ["psnr_invalid"])

        if props == ["psnr_invalid"]:
            raise ValueError(f"Invalid color format: {color_family}")

        return props

    def get_props(self) -> list[str]:
        color_family = self._reference.format.color_family  # type: ignore

        props = {
            vs.YUV: ["psnr_y", "psnr_cb", "psnr_cr"],
            vs.RGB: ["psnr_r", "psnr_g", "psnr_b"],
            vs.GRAY: ["psnr_gray"],
        }.get(color_family, ["psnr_invalid"])

        if props == ["psnr_invalid"]:
            raise ValueError(f"Invalid color format: {color_family}")

        if self.weights:
            props.append('psnr')

        return props


    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode, planes: None | int | list[int] = None) -> vs.VideoNode | MetricVideoNode:
        """
        Calculates the Plane Peak Signal-to-Noise Ratio (PSNR) between two clips and stores the result in the frame properties of the output clip.

        Args:
            reference (vs.VideoNode): The reference clip.
            distorted (vs.VideoNode): The distorted clip to compare against the reference.
            planes (None | int | list[int], optional): The planes to calculate the PSNR for.
                - If None (default), PSNR is calculated for all planes.
                - If an integer is provided, PSNR is calculated for the specified plane index.
                - If a list of integers is provided, PSNR is calculated for the specified plane indices.

        Returns:
            vs.VideoNode: The output clip with the PSNR scores stored in the frame properties.
            - If no weights are specified, the frame properties 'psnr_y', 'psnr_cb', 'psnr_cr' (for YUV), 'psnr_r', 'psnr_g', 'psnr_b' (for RGB),
              or 'psnr_gray' (for GRAY) contain the PSNR values for each plane.
            - If weights are specified an additional frame property 'psnr' which contains the weighted average of the PSNR values.

        Raises:
            ValueError: If the color family of the reference clip is not supported.

        Notes:
            - Both input clips must have the same format and dimensions.
            - Both 8-16 bit integer and float sample types are allowed.
        """
        self._set_reference(reference)

        if planes is None:
            planes = list(range(reference.format.num_planes))  # type: ignore
        elif isinstance(planes, int):
            planes = [planes]

        ref = split(reference)
        dist = split(distorted)

        metric = [
            core.complane.PSNR(ref[i], dist[i], self.props[i], self.opt, self.cache)
            for i in planes
        ]

        metric = merge_clip_props(distorted, *metric)

        if self.weights:
            metric = core.std.ModifyFrame(
                clip=metric,
                clips=metric,
                selector=partial(
                    self.set_prop,
                    props=[self.props[i] for i in planes]
                )
            )

        return MetricVideoNode(metric, self)

    def __call__(self, reference: vs.VideoNode, distorted: vs.VideoNode, planes: None | int | list[int] = None) -> vs.VideoNode:
        return self.calculate(reference, distorted, planes)


class WADIQAM:
    MAX_BATCH_SIZE = 2040
    formats: tuple[int, ...] = (
        vs.RGB24,
        vs.RGB30,
        vs.RGB48,
        vs.RGBS
    )

    class Dataset(Enum):
        TID = 'tid'
        LIVE = 'live'

    class EvaluationMethod(Enum):
        PATCHWISE = 'patchwise'
        WEIGHTED = 'weighted'
        
    def __init__(
        self,
        dataset: Dataset = Dataset.TID,
        method: EvaluationMethod = EvaluationMethod.PATCHWISE,
        model_path: None | PathLike = None
    ) -> None:

        from vs_wadiqam_chainer import wadiqam_fr, wadiqam_nr
        self._wadiqam_fr = wadiqam_fr
        self._wadiqam_nr = wadiqam_nr

        self.DATASET = dataset.value
        self.EVALUATION_METHOD = method.value
        self.model_path = model_path

    def _prepare(
        self,
        reference: vs.VideoNode,
        distorted: Optional[vs.VideoNode] = None
    ) -> tuple[vs.VideoNode, vs.VideoNode] | tuple[vs.VideoNode, None]:

        if reference.width or reference.height % 32 != 0:
            # pad with black bars?
            pad = [mod_x(i, 32) for i in (reference.width, reference.height)]
            prepared_reference = reference.resize.Lanczos(width=pad[0], height=pad[1])

            if distorted is not None:
                prepared_distorted = distorted.resize.Lanczos(width=pad[0], height=pad[1])
                return prepared_reference, prepared_distorted

        return prepared_reference, None

    def calculate(
        self,
        reference: vs.VideoNode,
        distorted: Optional[vs.VideoNode] = None,
    ) -> vs.VideoNode:

        if self.model_path is None:
            raise ValueError("model_path is required for WADIQAM calculations.")

        validate_format(reference, self.formats)
        
        if distorted:
            validate_format(distorted, self.formats)

        prepared_reference, prepared_distorted = self._prepare(
            reference, distorted
            )

        if prepared_distorted is not None:
            measure = self._wadiqam_fr(
                clip1=prepared_reference,
                clip2=prepared_distorted,
                model_folder_path=self.model_path,
                dataset=self.DATASET,
                top=self.EVALUATION_METHOD,
                max_batch_size=self.MAX_BATCH_SIZE
            )
        else:
            measure = self._wadiqam_nr(
                clip=prepared_reference,
                model_folder_path=self.model_path,
                dataset=self.DATASET,
                top=self.EVALUATION_METHOD,
                max_batch_size=self.MAX_BATCH_SIZE
            )

        return measure

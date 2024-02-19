from enum import Enum
from os import PathLike
from typing import Optional
from vstools import vs, mod_x, merge_clip_props

# https://github.com/WolframRhodium/muvsfunc/issues/59
class GMSD:
    def __init__(self, plane: None | int = None, downsample: bool = True, c: float = 0.0026):
        self.plane = plane
        self.downsample = downsample
        self.c = c
        self.object: list[vs.VideoNode] = None

    def calculate(self, img1: vs.VideoNode, img2: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import GMSD as _GMSD

        self.object = _GMSD(
            img1,
            img2,
            self.plane,
            self.downsample,
            self.c,
            self.show_map
            )
        
        return self.object[0]

    def map(self):
        return self.object[1]
    
# https://github.com/WolframRhodium/muvsfunc/issues/59
class MDSI:
    def __init__(self, resolution_scale: float = 1.0, alpha: float = 0.6):
        self.down_scale = resolution_scale
        self.alpha = alpha
        self.object: list[vs.VideoNode] = None

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import MDSI as _MDSI

        self.object = _MDSI(
            reference,
            distorted,
            self.down_scale,
            self.alpha,
            show_maps=True
            )
        
        return self.object[0]
    
    def gradient_map(self) -> vs.VideoNode:
        return self.object[1]

    def chromaticity_map(self) -> vs.VideoNode:
        return self.object[2]

    def gradient_chromaticity_map(self) -> vs.VideoNode:
        return self.object[3]

# https://github.com/WolframRhodium/muvsfunc/issues/59
class SSIM_Alt:
    def __init__(
        self, plane: Optional[int] = None, downsample: bool = True,
        k1: float = 0.01, k2: float = 0.03, dynamic_range: int = 1
        ):
        self.plane = plane
        self.down_scale = downsample
        self.k1 = k1
        self.k2 = k2
        self.dynamic_range = dynamic_range
        self.object: list[vs.VideoNode] = None
        
        self.dist = None

    def calculate(
        self,
        reference: vs.VideoNode,
        distorted: vs.VideoNode
    ) -> vs.VideoNode:
        from muvsfunc import SSIM as _SSIM

        self.dist = reference
        
        self.object = _SSIM(
            reference,
            distorted,
            self.down_scale,
            self.plane,
            self.k1,
            self.k2,
            self.dynamic_range,
            show_map=False
            )
        
        return merge_clip_props(self.dist, self.object)
    
    def map(self) -> vs.VideoNode:
        return merge_clip_props(self.object, self.dist).std.RemoveFrameProps("_Matrix")


@dataclass
class PSNR_Fast():
    def calculate(
        self,
        reference: vs.VideoNode,
        distorted: vs.VideoNode
    ) -> vs.VideoNode:
        
        match reference.format.color_family:
            case vs.YUV:
                props = ("psnr_y", "psnr_cb", "psnr_cr")
            case vs.RGB:
                props = ("psnr_r", "psnr_g", "psnr_b")
            case vs.GRAY:
                props = ("psnr_gray")

        metric = [
            core.complane.PSNR(i, j, propname=k)
            for i, j, k in zip(
                split(reference), split(distorted), props
            )
        ]

        return merge_clip_props(reference, *metric)


class WADIQAM:
    MAX_BATCH_SIZE = 2040

    class Dataset(Enum):
        TID = 'tid'
        LIVE = 'live'

    class EvaluationMethod(Enum):
        PATCHWISE = 'patchwise'
        WEIGHTED = 'weighted'
        
    def __init__(
        self,
        dataset: str = Dataset.TID,
        method: str = EvaluationMethod.PATCHWISE,
        model_path: PathLike = None
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

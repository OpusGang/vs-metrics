from os import PathLike
from typing import Callable, Optional
from stgpytools import mod_x
from vstools import vs


class GMSD():
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import GMSD as _GMSD
        return _GMSD(reference, distorted)


class MDSI():
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import MDSI as _MDSI
        return _MDSI(reference, distorted)


class WADIQAM:
    MODULO_BASE = 32
    DATASET = 'tid'
    EVALUATION_METHOD = 'patchwise'
    MAX_BATCH_SIZE = 2040

    def __init__(self) -> None:
        from vs_wadiqam_chainer import wadiqam_fr, wadiqam_nr
        self._wadiqam_fr = wadiqam_fr
        self._wadiqam_nr = wadiqam_nr

    def _prepare(
        self,
        reference: vs.VideoNode,
        distorted: Optional[vs.VideoNode] = None
    ) -> tuple[vs.VideoNode, Optional[vs.VideoNode]]:

        rw = [mod_x(i, self.MODULO_BASE) for i in (reference.width, reference.height)]
        prepared_reference = reference.resize.Lanczos(width=rw[0], height=rw[1])

        if distorted is not None:
            prepared_distorted = distorted.resize.Lanczos(width=rw[0], height=rw[1])
            return prepared_reference, prepared_distorted

        return prepared_reference, None

    def calculate(
        self,
        reference: vs.VideoNode,
        distorted: Optional[vs.VideoNode] = None,
        model_path: PathLike = None
    ) -> vs.VideoNode:

        if model_path is None:
            raise ValueError("model_path is required for WADIQAM calculations.")

        prepared_reference, prepared_distorted = self._prepare(
            reference, distorted
            )

        if prepared_distorted is not None:
            measure = self._wadiqam_fr(
                clip1=prepared_reference,
                clip2=prepared_distorted,
                model_folder_path=model_path,
                dataset=self.DATASET,
                top=self.EVALUATION_METHOD,
                max_batch_size=self.MAX_BATCH_SIZE
            )
        else:
            measure = self._wadiqam_nr(
                clip=prepared_reference,
                model_folder_path=model_path,
                dataset=self.DATASET,
                top=self.EVALUATION_METHOD,
                max_batch_size=self.MAX_BATCH_SIZE
            )

        return measure

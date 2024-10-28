from typing import Optional
from vstools import mod_x, vs
from enum import Enum
from os import PathLike

from ..meta import MetricBase

class WADIQAM(MetricBase):
    formats: list[int] = [
        vs.RGB24,
        vs.RGB30,
        vs.RGB48,
        vs.RGBS
    ]

    class Dataset(Enum):
        TID = 'tid'
        LIVE = 'live'

    class EvaluationMethod(Enum):
        PATCHWISE = 'patchwise'
        WEIGHTED = 'weighted'

    MAX_BATCH_SIZE = 2040

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

        self.validate_format(reference)
        
        if distorted:
            self.validate_format(distorted)

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
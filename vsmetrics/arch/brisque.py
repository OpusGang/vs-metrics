from vstools import inject_self, vs
from vsmetrics.meta import MetricBase
import numpy as np
import os


MODEL_DIR: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "models")


class BRISQUE(MetricBase):
    props: list[str] = ["BRISQUE"]
    formats: list[int] = [
        vs.GRAYS,
    ]

    def __init__(self):
        import cv2
        self.model = f'{MODEL_DIR}\\brisque\\brisque_model_live.yml'
        self.range = f'{MODEL_DIR}\\brisque\\brisque_range_live.yml'
        self.filter = cv2.quality.QualityBRISQUE_create(self.model, self.range)  # type: ignore

    @inject_self
    def calculate(self, reference: vs.VideoNode) -> vs.VideoNode:
        self.validate_format(reference)

        self.output_props = self.props[0]

        clip = reference.std.ModifyFrame(reference, self._process_frame)
        self._register_metadata(clip)
        return clip

    def _process_frame(self, n: int, f: vs.VideoFrame) -> vs.VideoFrame:
        fout = f.copy()

        arr = np.asarray(f[0])
        sharpness_score = self._brisque(arr)
        fout.props[self.output_props] = float(sharpness_score)

        return fout

    def _brisque(self, frame):
        frame = (frame * 255).astype(np.uint8)
        brisque_score = self.filter.compute(frame)
        return brisque_score[0]

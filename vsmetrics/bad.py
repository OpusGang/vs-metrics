from os import PathLike
from vstools import vs


class GMSD():
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import GMSD as _GMSD
        return _GMSD(reference, distorted)


class MDSI():
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        from muvsfunc import MDSI as _MDSI
        return _MDSI(reference, distorted)


class WADIQAM():
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode, model_path: PathLike = None) -> vs.VideoNode:
        from vs_wadiqam_chainer import wadiqam_fr
        from vstools import mod_x
        
        if model_path is None:
            raise ValueError("model_path is required for WADIQAM")

        rw = [mod_x(i, 32) for i in (reference.width, reference.height)]
        reference, distorted = [c.resize.Spline64(width=rw[0], height=rw[1]) for c in (reference, distorted)]

        measure = wadiqam_fr(
            clip1=reference,
            clip2=distorted,
            model_folder_path=model_path,
            dataset='tid',
            top='patchwise',
            max_batch_size=2040
        )

        return measure

class WADIQAM_NR():
    def calculate(self, reference: vs.VideoNode, model_path: PathLike = None) -> vs.VideoNode:
        from vs_wadiqam_chainer import wadiqam_nr
        from vstools import mod_x
        
        if model_path is None:
            raise ValueError("model_path is required for WADIQAM")

        rw = [mod_x(i, 32) for i in (reference.width, reference.height)]
        reference = [c.resize.Spline64(width=rw[0], height=rw[1]) for c in (reference)]

        measure = wadiqam_nr(
            clip=reference,
            model_folder_path=model_path,
            dataset='tid',
            top='patchwise',
            max_batch_size=2040
        )

        return measure

from enum import Enum
from vstools import vs, core

class Provider(Enum):
    SSIMULACRA1 = 0
    SSIMULACRA2 = 1
    SSIMULACRA2_ZIG = 2


class SSIMULACRA:
    def __init__(self, provider: Provider.SSIMULACRA2_ZIG):
        self.provider = provider

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        if self.provider == Provider.SSIMULACRA1:
            return self._SSIMULACRA1(reference, distorted)
        elif self.provider == Provider.SSIMULACRA2:
            return self._SSIMULACRA2(reference, distorted)
        elif self.provider == Provider.SSIMULACRA2_ZIG:
            return self._SSIMULACRA2_ZIG(reference, distorted)
        else:
            raise ValueError("Unknown provider")

    def _SSIMULACRA1(self, reference, distorted) -> vs.VideoNode:
        return core.julek.SSIMULACRA(reference, distorted, feature=0)

    def _SSIMULACRA2(self, reference, distorted) -> vs.VideoNode:
        return core.julek.SSIMULACRA(reference, distorted, feature=1)

    def _SSIMULACRA2_ZIG(self, reference, distorted) -> vs.VideoNode:
        return core.ssimulacra2.SSIMULACRA2(reference, distorted)


class BUTTERAUGLI:
    def calculate(
        self, reference: vs.VideoNode, distorted: vs.VideoNode,
        distmap: int = None,
        intensity_target: float = None,
        linput: float = None
    ) -> vs.VideoNode:

        return core.julek.Butteraugli(
            reference=reference,
            distorted=distorted,
            distmap=distmap,
            intensity_target=intensity_target,
            linput=linput
            )
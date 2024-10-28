from enum import Enum
from vstools import Matrix, Transfer, inject_self, vs, core
from ..meta import MetricBase

class SSIMULACRA(MetricBase):
    """Calculator for SSIMULACRA scores using different providers.
    Supported providers include:
    * SSIMULACRA1
    * SSIMULACRA2
    * SSIMULACRA2_ZIG

    Attributes:
        provider (enum): An enum value indicating the chosen provider.
    Methods:
        calculate(): Estimate the SSIMULACRA score based on the selected provider.
    """

    formats: list[int] = [
        vs.RGBS
    ]
    props: list[str] = ["_SSIMULACRA2"]

    class Provider(Enum):
        SSIMULACRA1 = 0
        SSIMULACRA2 = 1
        SSIMULACRA2_ZIG = 2

    class Props:
        SSIMULACRA1 = "_SSIMULACRA"
        SSIMULACRA2 = "_SSIMULACRA2"
        SSIMULACRA2_ZIG = "_SSIMULACRA2"

    METHODS = {
        Provider.SSIMULACRA1: lambda reference, distorted: core.julek.SSIMULACRA(reference, distorted, feature=1),
        Provider.SSIMULACRA2: lambda reference, distorted: core.julek.SSIMULACRA(reference, distorted, feature=0),
        Provider.SSIMULACRA2_ZIG: core.ssimulacra2.SSIMULACRA2,
    }

    def __init__(
        self,
        provider: Provider = Provider.SSIMULACRA2_ZIG,
        matrix: Matrix = Matrix.BT709,
        transfer: Transfer = Transfer.BT709
    ):

        if provider not in self.METHODS:
            raise ValueError("Unknown provider")

        self.provider = provider
        # Update props based on the selected provider
        SSIMULACRA.props = [getattr(self.Props, self.provider.name)]

    @property
    def prop(self):
        """Returns the relevant frame property based on the selected provider."""
        return getattr(self.Props, self.provider.name)

    @inject_self
    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        """Calculates SSIMULACRA score using the specified provider.
        Args:
            reference (vs.VideoNode): Reference video node.
            distorted (vs.VideoNode): Distorted video node.
        Returns:
            vs.VideoNode: Score map containing the estimated SSIMULACRA score.
        Raises:
            ValueError: If any of the inputs has an incorrect pixel format (not RGBS).
        Example usage:
            >>> calc_result = SSIMULACRA(Provider.SSIMULACRA2_ZIG).calculate(src, enc)
        Additional Notes:
            * Expects linear RGB data.
            * Supported providers: SSIMULACRA1, SSIMULACRA2, SSIMULACRA2_ZIG.
            * SSIMULACRA2_ZIG is the fastest.
        """
        method = self.METHODS[self.provider]
        
        self.validate_format(reference)
        self.validate_format(distorted)

        _reference = reference.resize.Bicubic(format=vs.RGBS)
        _distorted = distorted.resize.Bicubic(format=vs.RGBS)

        if self.provider is self.Provider.SSIMULACRA2_ZIG:
            _reference = _reference.fmtc.transfer(transs="1886", transd="linear", bits=32)
            _distorted = _distorted.fmtc.transfer(transs="1886", transd="linear", bits=32)
        else:
            _reference = _reference.fmtc.transfer(transs="linear", transd="1886", bits=32)
            _distorted = _distorted.fmtc.transfer(transs="linear", transd="1886", bits=32)

        measure = method(_reference, _distorted)

        clip = distorted.std.CopyFrameProps(measure, props=self.prop)
        self._register_metadata(clip)

        return clip
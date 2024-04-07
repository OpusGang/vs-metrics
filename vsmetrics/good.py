from dataclasses import dataclass
from enum import Enum
from os import PathLike
from vstools import Matrix, Transfer, vs, core
from .util import MetricVideoNode, validate_format

# ADD LUMA BIAS FOR DARK
class SSIMULACRA:
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

    formats: tuple[int] = (
        vs.RGBS
    ) # type: ignore

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

    @property
    def prop(self):
        """Returns the relevant frame property based on the selected provider."""
        return getattr(self.Props, self.provider.name)

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
        
        #validate_format(reference, self.formats)
        #validate_format(distorted, self.formats)

        _reference = reference.resize.Bicubic(format=vs.RGBS)
        _distorted = distorted.resize.Bicubic(format=vs.RGBS)
            
        if self.provider is self.Provider.SSIMULACRA2_ZIG:
            _reference = _reference.fmtc.transfer(transs="1886", transd="linear", bits=32)
            _distorted = _distorted.fmtc.transfer(transs="1886", transd="linear", bits=32)
        else:
            _reference = _reference.fmtc.transfer(transs="linear", transd="1886", bits=32)
            _distorted = _distorted.fmtc.transfer(transs="linear", transd="1886", bits=32)

        measure = method(_reference, _distorted)

        return distorted.std.CopyFrameProps(measure, props=str(self.prop))

#    def render(self, reference: vs.VideoNode, distorted: vs.VideoNode, filename: PathLike = "log.txt") -> None:
#
#        self.calculate()
#
#        clip_async_render(_cambi, outfile=None, progress="calculating CAMBI")

        


#@dataclass
class BUTTERAUGLI:
    formats: tuple[int, ...] = (
        vs.RGB24,
        vs.RGB48,
        vs.RGBS
    )

    props: list[str] = [
        '_FrameButteraugli'
    ]

    """Quality metric for lossy image and video compression.

    Attributes:
        intensity_target: Viewing conditions screen nits.
    """
    intensity_target: float = 80.0
    
    def calculate(
        self, reference: vs.VideoNode, distorted: vs.VideoNode, linear: bool = False
    ) -> vs.VideoNode | MetricVideoNode:
        """Estimates the psychovisual similarity between two clips.

        Args:
            reference (vs.VideoNode): Clip used as the reference. Must be in RGB 8/16/32-bit and match the dimension of 'distorted'.
            distorted (vs.VideoNode): Clip used for comparison against 'reference'. Must be in RGB 8/16/32-bit and match the dimension of 'reference'.
            linear (bool): True if the input clips have linear transfer functions. Otherwise, assumes sRGB color space and converts to linear transfer internally.

        Returns:
            vs.VideoNode: Output clip with the calculated psychovisual similarities stored as frame properties ('_FrameButteraugli').

        Raises:
            ValueError: If either 'reference' or 'distorted' is not in RGB 8/16/32-bit or their dimensions don't match.

        Notes:
            * Larger values indicate greater difference between the two clips.
            * The default viewing condition is 80 cd/m^2 (nits), which corresponds to a typical modern display device. You can adjust this setting via the 'intensity_target' attribute.
            * Input clips with nonlinear transfer functions (like gamma correction) will automatically be transformed into linear transfer before calculating the metrics.
            * Set 'linear' to True if your input clips already have linear transfer functions.
        """
        self.butteraugli_obj = core.julek.Butteraugli(
            reference=reference,
            distorted=distorted,
            intensity_target=self.intensity_target,
            linput=linear,
            distmap=True
        )
        
        clip = distorted.std.CopyFrameProps(prop_src=self.butteraugli_obj, props="_FrameButteraugli")
        return MetricVideoNode(clip, self)
    
    def mask(self) -> vs.VideoNode:
        """Returns the heatmap representing the differences between the two clips.

        Returns:
            vs.VideoNode: Heatmap clip representing the differences between the two clips.

        Notes:
            * This method should be called after the 'calculate' method has been called.
        """
        return self.butteraugli_obj
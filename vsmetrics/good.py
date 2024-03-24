from dataclasses import dataclass
from enum import Enum
from vstools import vs, core
from .util import validate_format

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

    class Provider(Enum):
        SSIMULACRA1 = 0
        SSIMULACRA2 = 1
        SSIMULACRA2_ZIG = 2

    formats: tuple[int] = (
        vs.RGBS
    ) # type: ignore

    METHODS = {
        Provider.SSIMULACRA1: lambda reference, distorted: core.julek.SSIMULACRA(reference, distorted, feature=0),
        Provider.SSIMULACRA2: lambda reference, distorted: core.julek.SSIMULACRA(reference, distorted, feature=1),
        Provider.SSIMULACRA2_ZIG: core.ssimulacra2.SSIMULACRA2,
    }

    def __init__(self, provider: Provider):

        if provider not in self.METHODS:
            raise ValueError("Unknown provider")

        self.provider = provider

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode:
        """Estimates SSIMULACRA score using the specified provider.
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
        
        validate_format(reference, self.formats)
        validate_format(distorted, self.formats)

        #for input in (reference, distorted):
        #    if input.format.id != vs.RGBS:
        #        raise ValueError(f"Expected {vs.RGBS} but got {input.format.name}")

        #reference = reference.resize.Bicubic(format=vs.RGBS, matrix_in=Matrix.BT709)
        #distorted = distorted.resize.Bicubic(format=vs.RGBS, matrix_in=Matrix.BT709)

        #reference = reference.fmtc.transfer(transs="srgb", transd="linear", bits=32)
        #distorted = distorted.fmtc.transfer(transs="srgb", transd="linear", bits=32)

        #reference, distorted = [
        #    clip.resize.Bicubic(
        #        format=vs.RGBS,
        #        transfer_in=self.transfer,
        #        transfer=Transfer.LINEAR,
        #        dither_type=DitherType.NONE
        #        ) for clip in (reference, distorted)
        #]

        measure = method(reference, distorted)

        #measure = measure.std.RemoveFrameProps(props=['_Matrix', '_Transfer'])
        #merge = merge_clip_props(reference, measure)

        return measure


@dataclass
class BUTTERAUGLI:
    """Quality metric for lossy image and video compression.

    Attributes:
        distmap: Whether to return heatmap instead of distorted clip.
        intensity_target: Viewing conditions screen nits.
        linput: True if the input clips have linear transfer functions. Otherwise, assumes sRGB color space and converts to linear transfer internally.
    """
    distmap: int = False
    intensity_target: float = 80.0
    linput: bool = False
    
    def calculate(
        self, reference: vs.VideoNode, distorted: vs.VideoNode
    ) -> vs.VideoNode:
        """Estimates the psychovisual similarity between two clips.

        Args:
            reference (vs.VideoNode): Clip used as the reference. Must be in RGB 8/16/32-bit and match the dimension of 'distorted'.
            distorted (vs.VideoNode): Clip used for comparison against 'reference'. Must be in RGB 8/16/32-bit and match the dimension of 'reference'.

        Returns:
            vs.VideoNode: Output clip with the calculated psychovisual similarities stored as frame properties ('_FrameButteraugli').
            vs.VideoNode: Alternatively, if 'distmap' is set to True, returns a heatmap representing the differences between the two clips.

        Raises:
            ValueError: If either 'reference' or 'distorted' is not in RGB 8/16/32-bit or their dimensions don't match.

        Notes:
            * Larger values indicate greater difference between the two clips.
            * The default viewing condition is 80 cd/m^2 (nits), which corresponds to a typical modern display device. You can adjust this setting via the 'intensity_target' attribute.
            * Input clips with nonlinear transfer functions (like gamma correction) will automatically be transformed into linear transfer before calculating the metrics.
            * Set 'linput' to True if your input clips already have linear transfer functions.
            """
        return core.julek.Butteraugli(
            reference=reference,
            distorted=distorted,
            distmap=self.distmap,
            intensity_target=self.intensity_target,
            linput=self.linput
            )
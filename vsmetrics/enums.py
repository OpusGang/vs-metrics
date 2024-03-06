
from enum import Enum

class MatrixFMTC(Enum):
    """String enums representing various matrix types for color space conversions."""
    
    # Predefined matrix for conversions to and from R'G'B'. The direction is deduced from the specified input and output colorspaces.
    BT601 = '601'      # ITU-R BT.601 / ITU-R BT.470-2 / SMPTE 170M. For Standard Definition content.
    BT709 = '709'      # ITU-R BT.709. For High Definition content.
    BT2020 = '2020'   # ITU-R BT.2020 and ITU-R BT.2100, non constant luminance mode. For UHDTV content.
    BT2100 = '2100'   # ITU-R BT.2020 and ITU-R BT.2100, non constant luminance mode. For UHDTV content.
    BT240 = '240'     # SMPTE 240M
    FCC = 'FCC'       # FCC Title 47
    
    YCoCg = 'YCoCg'   # YCoCg
    YCgCo = 'YCgCo'   # Y'Co’Cg’
    YDzDx = 'YDzDx'   # Y’D’ZD’X, SMPTE ST 2085
    RGB = 'RGB'       # R’G’B’, Identity, no cross-plane calculations.
    
    # Source and destination matrices for YUV. Use both when you want to do a conversion between BT.601 and BT.709.
    LMS = 'LMS'        # Intermediate colorspace for ICTCP transforms. The LMS colorspace is conveyed on RGB planes.
    ICtCp_PQ = 'ICtCp_PQ'  # ITU-R BT.2100-2 ICTCP with perceptual quantization (PQ).
    ICtCp_HLG = 'ICtCp_HLG'  # ITU-R BT.2100-2 ICTCP with hybrid log-gamma transfer function (HLG).


class PrimariesFMTC(Enum):
    BT709 = ((0.64, 0.33), (0.3, 0.6), (0.15, 0.06), (0.3127, 0.329))
    FCC = ((0.67, 0.33), (0.21, 0.71), (0.14, 0.08), (0.31, 0.316))
    NTSCJ = ((0.67, 0.33), (0.21, 0.71), (0.14, 0.08), (0.2848, 0.2932))
    BT470BG = ((0.64, 0.33), (0.29, 0.6), (0.15, 0.06), (0.3127, 0.329))
    SMPTE240M = ((0.63, 0.34), (0.31, 0.595), (0.155, 0.07), (0.3127, 0.329))
    GENERIC_FILM = ((0.681, 0.319), (0.243, 0.692), (0.145, 0.049), (0.31, 0.316))
    BT2020 = ((0.70792, 0.29203), (0.17024, 0.79652), (0.13137, 0.04588), (0.31271, 0.32902))
    P3DCI = ((0.68, 0.32), (0.265, 0.69), (0.15, 0.06), (0.314, 0.351))
    P3D65 = ((0.68, 0.32), (0.265, 0.69), (0.15, 0.06), (0.3127, 0.329))
    EBU3213E = ((0.63, 0.34), (0.295, 0.605), (0.155, 0.077), (0.3127, 0.329))
    SCRGB = ((0.64, 0.33), (0.3, 0.6), (0.15, 0.06), (0.31271, 0.32902))
    ADOBE_RGB_98 = ((0.64, 0.33), (0.21, 0.71), (0.15, 0.06), (0.31271, 0.32902))
    ADOBE_RGB_WIDE = ((0.73469, 0.26531), (0.11416, 0.82621), (0.15664, 0.0177), (0.34567, 0.3585))
    APPLE_RGB = ((0.625, 0.34), (0.28, 0.595), (0.155, 0.07), (0.31271, 0.32902))
    ROMM = ((0.7347, 0.2653), (0.1596, 0.8404), (0.0366, 0.0001), (0.34567, 0.3585))
    CIERGB = ((0.7347, 0.2653), (0.2738, 0.7174), (0.1666, 0.0089), (0.3333333333333333, 0.3333333333333333))
    CIEXYZ = ((1.0, 0.0), (0.0, 1.0), (0.0, 0.0), (0.3333333333333333, 0.3333333333333333))
    ACES = ((0.7347, 0.2653), (0.0, 1.0), (0.0001, -0.077), (0.32168, 0.33767))
    ACESAP1 = ((0.713, 0.293), (0.165, 0.83), (0.128, 0.044), (0.32168, 0.33767))
    SGAMUT = ((0.73, 0.28), (0.14, 0.855), (0.1, -0.05), (0.3127, 0.329))
    SGAMUT3CINE = ((0.766, 0.275), (0.225, 0.8), (0.089, -0.087), (0.3127, 0.329))
    ALEXA = ((0.684, 0.313), (0.221, 0.848), (0.0861, -0.102), (0.3127, 0.329))
    VGAMUT = ((0.73, 0.28), (0.165, 0.84), (0.1, -0.03), (0.3127, 0.329))
    P3D60 = ((0.68, 0.32), (0.265, 0.69), (0.15, 0.06), (0.32168, 0.33767))
    P22 = ((0.625, 0.34), (0.28, 0.595), (0.155, 0.07), (0.28315, 0.29711))
    FREESCALE = ((0.7347, 0.2653), (0.14, 0.86), (0.1, -0.02985), (0.31272, 0.32903))
    DAVINCI = ((0.8, 0.313), (0.1682, 0.9877), (0.079, -0.1155), (0.3127, 0.329))
    DRAGONCOLOR = ((0.75304, 0.32783), (0.29957, 0.7007), (0.07964, -0.05494), (0.32168, 0.33767))
    DRAGONCOLOR2 = ((0.75304, 0.32783), (0.29957, 0.7007), (0.14501, 0.0511), (0.32168, 0.33767))
    REDCOLOR = ((0.69975, 0.32905), (0.30426, 0.62364), (0.13491, 0.03472), (0.32168, 0.33767))
    REDCOLOR2 = ((0.87868, 0.32496), (0.30089, 0.67905), (0.0954, -0.02938), (0.32168, 0.33767))
    REDCOLOR3 = ((0.70118, 0.32901), (0.3006, 0.68379), (0.10815, -0.00869), (0.32168, 0.33767))
    REDCOLOR4 = ((0.70118, 0.32901), (0.3006, 0.68379), (0.14533, 0.05162), (0.32168, 0.33767))
    REDWIDE = ((0.780308, 0.304253), (0.121595, 1.493994), (0.095612, -0.084589), (0.3217, 0.329))
    P3P = ((0.74, 0.27), (0.22, 0.78), (0.09, -0.09), (0.314, 0.351))
    CINEGAM = ((0.74, 0.27), (0.17, 1.14), (0.08, -0.1), (0.3127, 0.329))
    AWG4 = ((0.7347, 0.2653), (0.1424, 0.8576), (0.0991, -0.0308), (0.3127, 0.329))

    def __init__(self, r, g, b, w):
        self.r = r
        self.g = g
        self.b = b
        self.w = w

    def coordinates(self):
        return {
            "R": self.r,
            "G": self.g,
            "B": self.b,
            "W": self.w
        }

class TransferFMTC(Enum):
    pass


class ColormapTypes(Enum):
    AUTUMN = 0
    BONE = 1
    JET = 2
    WINTER = 3
    RAINBOW = 4
    OCEAN = 5
    SUMMER = 6
    SPRING = 7
    COOL = 8
    HSV = 9
    PINK = 10
    HOT = 11
    PARULA = 12
    MAGMA = 13
    INFERNO = 14
    PLASMA = 15
    VIRIDIS = 16
    CIVIDIS = 17
    TWILIGHT = 18
    TWILIGHT_SHIFTED = 19
    TURBO = 20
    DEEPGREEN = 21
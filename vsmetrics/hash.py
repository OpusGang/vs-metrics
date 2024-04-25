import cv2
import numpy as np
from vstools import vs, core
from .meta import MetricVideoNode, validate_format

class Hash_3117:
    """
    31 + 17 ID system
    by DZgas
    """
    props: list[str] = ["Hash_3117"]
    formats: tuple[int, ...] = (
        vs.GRAYS
    ) # type: ignore

    def calculate(self, reference: vs.VideoNode, distorted: vs.VideoNode) -> vs.VideoNode | MetricVideoNode:

        validate_format(reference, formats=self.formats)
        validate_format(distorted, formats=self.formats)
        
        clip = core.std.ModifyFrame(clip=reference, clips=[reference, distorted], selector=self.perceptual_hash_3117)
        clip = core.std.CopyFrameProps(distorted, clip, props=self.props)

        return MetricVideoNode(clip, self)

    def perceptual_hash_3117(self, n: int, f: list[vs.VideoFrame]) -> vs.VideoFrame:
        f1, f2 = f

        def calculate_hash(image):
            image_v = cv2.resize(image, (31, 31), interpolation=cv2.INTER_LANCZOS4)
            pixels = image_v.flatten()
            vertical_avg_pixels = [sum(pixels[i::31]) / 31 for i in range(31)]

            image_h = cv2.resize(image, (17, 17), interpolation=cv2.INTER_LANCZOS4)
            pixels = image_h.flatten()
            horizontal_avg_pixels = [sum(pixels[i * 17:(i + 1) * 17]) / 17 for i in range(17)]

            vertical_avg_pixels = self.expand_to_range(vertical_avg_pixels)
            horizontal_avg_pixels = self.expand_to_range(horizontal_avg_pixels)

            vertical_hex_values = "".join(hex(int(pixel))[2:].zfill(2) for pixel in vertical_avg_pixels)
            horizontal_hex_values = "".join(hex(int(pixel))[2:].zfill(2) for pixel in horizontal_avg_pixels)

            hash_value = vertical_hex_values + horizontal_hex_values

            return hash_value

        arr1 = np.asarray(f1).astype(np.float32)
        arr2 = np.asarray(f2).astype(np.float32)

        hash1 = calculate_hash(arr1[0])
        hash2 = calculate_hash(arr2[0])

        dec_values1 = self.hex_to_dec(hash1)
        dec_values2 = self.hex_to_dec(hash2)

        difference = self.calculate_difference(dec_values1, dec_values2)

        fout1 = f1.copy() # type: ignore
        fout1.props.Hash_3117 = int(difference)

        return fout1

    def hex_to_dec(self, hex_str) -> list[int]:
        return [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]

    def calculate_difference(self, numbers1, numbers2):
        result = 0

        for i in range(len(numbers1)):
            result += abs(numbers1[i] - numbers2[i])

        return result

    def expand_to_range(self, numbers) -> list[int]:
        min_num = min(numbers)
        max_num = max(numbers)

        if max_num - min_num == 0:
            return [round(num) for num in numbers]

        return [round(((num - min_num) / (max_num - min_num)) * 255) for num in numbers]

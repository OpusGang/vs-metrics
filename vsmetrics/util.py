from vstools import vs, core

#def format_handler(ref_fmt, dist_fmt, fmt):
#    pass
##    ref_str = f"Reference: {ref_fmt.name}" if ref_fmt.id in fmt.formats else f"\033[91mIncorrect:\033[0m {ref_fmt.name}"
##    dist_str = f"Distorted: {dist_fmt.name}" if dist_fmt.id in fmt.formats else f"\033[91mIncorrect:\033[0m {dist_fmt.name}"
##    
##    return ', '.join((ref_str, dist_str))
#
#def get_format_info(ref_fmt, dist_fmt, fmts):
#    pass
#    def add_incorrect_prefix(label, fmt):
#        return f"{label}: {'Incorrect ' if fmt.id not in fmts else ''}{fmt.name}
#    return ', '.join((add_incorrect_prefix("Reference", ref_fmt), add_incorrect_prefix("Distorted", dist_fmt)))

        #def get_format_info(ref_fmt, dist_fmt, fmts):
        #    def add_incorrect_prefix(label, fmt):
        #        return f"{label}: {'Incorrect ' if fmt.id not in fmts else ''}{fmt.name}"
        #
        #    return ', '.join((add_incorrect_prefix("Reference", ref_fmt), add_incorrect_prefix("Distorted", dist_fmt)))
        #
        #if self.safe:
        #    for input in (reference, distorted):
        #        if input.format.id not in VMAFMetric.formats:
        #            formatted_inputs = get_format_info(reference.format, distorted.format, VMAFMetric.formats)
        #            valid_formats = ", ".join([_format.name for _format in self.formats])
        #            err_msg = f"Unexpected format found.\nFormats passed: {formatted_inputs}\nExpected one of these formats: {valid_formats}"
        #            raise ValueError(err_msg)

class ReductionMode:
    class Crop:
        def __init__(self, percentage: int = 25):   
            self.percentage = percentage
            
    class Downsample:
        def __init__(self, percentage: int = 50):
            self.percentage = percentage

    class Hybrid:
        def __init__(self, chunks: int = 4):
            self.chunks = chunks

def pre_process(
    reference: vs.VideoNode,
    distorted: vs.VideoNode,
    reduce: ReductionMode = ReductionMode.Crop
    ) -> vs.VideoNode:
    
    if reduce:
        if isinstance(reduce, ReductionMode.Crop):
        
            crop_left_right = int(reference.width * (reduce.percentage / 2) / 100)
            crop_top_bottom = int(reference.height * (reduce.percentage / 2) / 100)
    
            crop_left_right, crop_top_bottom = [
                i + (4 - i % 4) % 4 for i in [crop_left_right, crop_top_bottom]
            ]
    
            reference, distorted = [
                clip.std.Crop(
                    left=crop_left_right,
                    right=crop_left_right,
                    top=crop_top_bottom,
                    bottom=crop_top_bottom
                    ) for clip in (reference, distorted)
            ]
    
        elif isinstance(reduce, ReductionMode.Downsample):
        
            new_width = reference.width - 2 * int(reference.width * (reduce.percentage / 2) / 100)
            new_height = reference.height - 2 * int(reference.height * (reduce.percentage / 2) / 100)
    
            new_width -= new_width % 4
            new_height -= new_height % 4
    
            reference, distorted = [
                clip.resize.Lanczos(new_width, new_height)
                for clip in (reference, distorted)
            ]

        elif isinstance(reduce, ReductionMode.Hybrid):
            chunks = reduce.chunks

            chunk_width = reference.width // chunks
            chunk_height = reference.height // chunks
            
            if chunk_width < 320 or chunk_height < 180:
                raise ValueError(f"{chunks} chunks ({chunk_width}x{chunk_height}) is probably too many for {reference.width}x{reference.height}")
        
            ref_clips = []
            dis_clips = []
        
            for y in range(0, reference.height, chunk_height):
                for x in range(0, reference.width, chunk_width):

                    right_ref = max(0, reference.width - x - chunk_width)
                    bottom_ref = max(0, reference.height - y - chunk_height)
                    right_dis = max(0, distorted.width - x - chunk_width)
                    bottom_dis = max(0, distorted.height - y - chunk_height)

                    ref_cropped_clip = reference[::chunks].std.Crop(left=x, top=y, right=right_ref, bottom=bottom_ref)
                    dis_cropped_clip = distorted[::chunks].std.Crop(left=x, top=y, right=right_dis, bottom=bottom_dis)

                    ref_clips.append(ref_cropped_clip)
                    dis_clips.append(dis_cropped_clip)
        
            reference = core.std.Interleave(ref_clips)
            distorted = core.std.Interleave(dis_clips)

            return distorted
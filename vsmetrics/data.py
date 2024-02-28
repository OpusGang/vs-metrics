# write to csv/json
# visualize data, per-scene

import os
from warnings import warn
import pandas as pd
import matplotlib.pyplot as plt
from vstools import merge_clip_props, vs, core, clip_async_render, clip_data_gather, SceneChangeMode, SceneBasedDynamicCache

class CSVHandler:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def read_csv(self):
        return pd.read_csv(self.filepath)
    
    def write_csv(
        self,
        clip: vs.VideoNode,
        overwrite: bool = False,
        scenechange: bool = True
    ):

        file_path = os.path.abspath(self.filepath)

        if os.path.exists(file_path) and not overwrite:
            print("Using existing data!!")
            return
        
        if scenechange:
            clip = clip.resize.Bilinear(640, 360)
            clip = clip.wwxd.WWXD()
            
        data = clip_async_render(
            clip, outfile=None, progress='Getting frame props...',
            callback=lambda _, f: f.props.copy(), async_requests=2 # noqa
            )

        data = pd.DataFrame(data)
        data.to_csv(self.filepath, index=False)
    
    def plot_data(self, column):
        df = self.read_csv()
        df[column].plot()
        plt.show()
    
    def fix_props(self):
        # rename props to consistent style
        ...


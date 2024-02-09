# write to csv/json
# visualize data, per-scene

import os
import pandas as pd
import matplotlib.pyplot as plt
from vstools import vs, core, clip_async_render

class CSVHandler:
    def __init__(self, filename):
        self.filename = filename
    
    def read_csv(self):
        return pd.read_csv(self.filename)
    
    def write_csv(self, clip: vs.VideoNode, overwrite: bool = False):
        if os.path.exists(self.filepath) and overwrite is False:
            raise ValueError("File exists")

        data = clip_async_render(
            clip, outfile=None, progress='Getting frame props...',
            callback=lambda _, f: f.props.copy(), async_requests=2 # noqa
            )

        data = pd.DataFrame(data)

        data.to_csv(self.filename, index=False)
    
    def plot_data(self, column):
        df = self.read_csv()
        df[column].plot()
        plt.show()
    
    def fix_props(self):
        # rename props to consistent style
        ...
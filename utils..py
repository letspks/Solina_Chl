import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

def generate_legend(image_array, cmap_name):
    if image_array is None:
        return None

    cmap = plt.get_cmap(cmap_name)
    norm = Normalize(vmin=np.min(image_array), vmax=np.max(image_array))
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # Generowanie legendy
    fig, ax = plt.subplots(figsize=(2, 8))
    fig.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
    cbar = fig.colorbar(sm, cax=ax)
    cbar.set_label("Value")

    return fig

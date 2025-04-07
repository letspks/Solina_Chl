from tkinter import Tk
from gui import MapApp

import sys
sys.path.append("C:/Users/Piotrek/Desktop/studia/SPACE TECHNOLOGIES/RSAIAIST - Remote Sensing and Image Analysis in Space Tech/Solina")

if __name__ == "__main__":
    root = Tk()
    app = MapApp(root)
    root.mainloop()

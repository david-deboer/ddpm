def get_style(name='default'):
    if name == 'default':
        return DefaultStyle()
    if name == 'pretty1':
        return Pretty1Style()


class BaseStyle:
    def set_spines(self, ax):
        if len(self.spines_visible):
            ax.spines[self.spines_visible].set_visible(True)
        if len(self.spines_invisible):
            ax.spines[self.spines_invisible].set_visible(False)

class DefaultStyle(BaseStyle):
    def __init__(self):
        self.xgrid_color = '0.6'
        self.xgrid_lw = 1
        self.xgrid_ls = ':'
        self.banner_color = None
        self.face_color = 'white'
        self.spines_visible = ['left', 'bottom', 'right', 'top']
        self.spines_invisible = []

class Pretty1Style(BaseStyle):
    def __init__(self):
        self.xgrid_color = 'white'
        self.xgrid_lw = 2
        self.xgrid_ls = '-'
        self.banner_color = 'steelblue'
        self.face_color = '0.9'
        self.spines_visible = []
        self.spines_invisible = ['left', 'bottom', 'right', 'top']
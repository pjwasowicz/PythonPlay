class WaveCanvasAdapter:
    def __init__(self, label):
        self.label = label

    def winfo_width(self):
        return max(1, self.label.width())

    def winfo_height(self):
        return max(1, self.label.height())

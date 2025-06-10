import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as mpimg
import threading
import time
import os

class AIRatioPlotter:
    def __init__(self, analyzer, interval=2, background_img_path=None):
        self.analyzer = analyzer
        self.interval = interval
        self.timestamps = []
        self.ratios = []
        self.start_time = time.time()
        self.background_img_path = background_img_path

        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'r-', linewidth=2)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("AI/Total Audio Ratio")
        self.ax.set_title("Real-Time AI Ratio Over Time")
        self.ax.grid(True)

        # Load and set background image if provided
        if background_img_path and os.path.exists(background_img_path):
            img = mpimg.imread(background_img_path)
            self.ax.imshow(img, extent=[0, 300, 0, 1], aspect='auto', alpha=0.3, zorder=-1)
        # save the plot as a png file
        self.fig.savefig("ai_ratio_plot.png", dpi=300, bbox_inches='tight')

        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._update_data)
        self.thread.daemon = True
        self.thread.start()

        self.ani = animation.FuncAnimation(self.fig, self._animate, interval=1000)

    def _update_data(self):
        while True:
            time.sleep(self.interval)
            with self.lock:
                t = time.time() - self.start_time
                ratio = self.analyzer.get_ai_ratio()
                self.timestamps.append(t)
                self.ratios.append(ratio)

    def _animate(self, frame):
        with self.lock:
            self.line.set_data(self.timestamps, self.ratios)
            if self.timestamps:
                self.ax.set_xlim(0, max(10, self.timestamps[-1]))
                # self.ax.set_ylim(0, max(1.5, max(self.ratios) + 0.1))
                self.ax.set_ylim(0, 1.0)

        return self.line,

    def show(self):
        plt.show()

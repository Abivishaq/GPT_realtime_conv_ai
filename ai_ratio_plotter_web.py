import threading
import time
from flask import Flask, jsonify, render_template
import os

class AIRatioPlotterWeb:
    def __init__(self, analyzer, interval=2, background_img_path=None, port=5000):
        self.analyzer = analyzer
        self.interval = interval
        self.timestamps = []
        self.ratios = []
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.background_img_path = background_img_path
        self.port = port

        self.app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

        self._setup_routes()

        # Start background data update thread
        self.data_thread = threading.Thread(target=self._update_data)
        self.data_thread.daemon = True
        self.data_thread.start()

        # Start Flask server in a thread
        self.server_thread = threading.Thread(target=self._start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html', background_img=self.background_img_path)

        @self.app.route('/data')
        def data():
            with self.lock:
                return jsonify({
                    "timestamps": self.timestamps[-100:],
                    "ratios": self.ratios[-100:]
                })

    def _update_data(self):
        while True:
            time.sleep(self.interval)
            with self.lock:
                t = time.time() - self.start_time
                r = self.analyzer.get_ai_ratio()
                self.timestamps.append(t)
                self.ratios.append(r)

    def _start_server(self):
        self.app.run(debug=False, port=self.port, use_reloader=False)

    def show(self):
        print(f"Server is running at http://127.0.0.1:{self.port}")

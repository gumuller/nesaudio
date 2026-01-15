"""
Spectrum analyzer widget
"""

from textual.app import ComposeResult
from textual.widget import Widget
from rich.text import Text
import numpy as np


class SpectrumWidget(Widget):
    """Visual spectrum analyzer display"""

    def __init__(self, bins: int = 32, **kwargs):
        super().__init__(**kwargs)
        self.bins = bins
        self.spectrum_data = np.zeros(bins)

    def update_spectrum(self, data: np.ndarray):
        """Update spectrum data"""
        self.spectrum_data = data
        self.refresh()

    def render(self) -> Text:
        """Render the spectrum analyzer"""
        # Create a visual representation using block characters
        height = 8  # Height in characters
        blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

        lines = []

        # Top line - peak indicators
        top_line = ""
        for value in self.spectrum_data:
            if value > 0.9:
                top_line += "█"
            elif value > 0.7:
                top_line += "▀"
            else:
                top_line += " "
        lines.append(top_line)

        # Main bars
        for row in range(height - 1, -1, -1):
            line = ""
            threshold = row / height
            for value in self.spectrum_data:
                if value >= threshold:
                    # Scale to block character
                    block_idx = min(int((value - threshold) * height), len(blocks) - 1)
                    line += blocks[min(block_idx, 7)]
                else:
                    line += " "
            lines.append(line)

        # Frequency labels (simplified)
        labels = ""
        label_positions = [0, len(self.spectrum_data) // 4, len(self.spectrum_data) // 2,
                          3 * len(self.spectrum_data) // 4, len(self.spectrum_data) - 1]
        label_texts = ["Low", "  ", "Mid", "  ", "High"]

        for i in range(len(self.spectrum_data)):
            if i in label_positions:
                idx = label_positions.index(i)
                if i == 0:
                    labels += label_texts[idx]
                elif len(labels) + len(label_texts[idx]) <= len(self.spectrum_data):
                    # Pad to position
                    while len(labels) < i:
                        labels += " "
                    labels += label_texts[idx]

        while len(labels) < len(self.spectrum_data):
            labels += " "

        lines.append(labels[:len(self.spectrum_data)])

        return Text("\n".join(lines), style="cyan bold")

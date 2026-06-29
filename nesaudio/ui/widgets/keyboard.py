"""
Virtual keyboard widget
"""

from textual.widget import Widget
from rich.text import Text


class KeyboardWidget(Widget):
    """Visual keyboard display"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pressed_keys = set()

    def render(self) -> Text:
        """Render keyboard"""
        lines = []
        lines.append("Piano Keys (QWERTY Layout)")
        lines.append("")

        # Black keys row (sharps/flats)
        black_keys = "  W E   T Y U   O P"
        black_line = ""
        for key in black_keys:
            if key != ' ' and key in self.pressed_keys:
                black_line += "[reverse]" + key + "[/reverse]"
            else:
                black_line += key
        lines.append(black_line)

        # White keys row
        white_keys = "A S D F G H J K L"
        white_line = ""
        for key in white_keys:
            if key in self.pressed_keys:
                white_line += "[reverse]" + key + "[/reverse]"
            else:
                white_line += key
        lines.append(white_line)

        lines.append("")
        lines.append("Z/X: Octave Down/Up    1-4: Select Channel")
        lines.append("F1-F6: Sound Effects   R: Record   Q: Quit")

        return Text.from_markup("\n".join(lines))

    def press_key(self, key: str):
        """Mark a key as pressed"""
        self.pressed_keys.add(key.upper())
        self.refresh()

    def release_key(self, key: str):
        """Mark a key as released"""
        self.pressed_keys.discard(key.upper())
        self.refresh()

    def clear_all(self):
        """Clear all pressed keys"""
        self.pressed_keys.clear()
        self.refresh()

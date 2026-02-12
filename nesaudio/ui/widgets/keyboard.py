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
        # Simple keyboard layout
        lines = []
        lines.append("┌─────────────────────────────────────────────┐")
        lines.append("│  Piano Keys (QWERTY Layout)                │")
        lines.append("├─────────────────────────────────────────────┤")

        # Black keys row (sharps/flats)
        black_keys = "  W E   T Y U   O P  "
        black_line = "│ "
        for i, key in enumerate(black_keys):
            if key != ' ' and key in self.pressed_keys:
                black_line += "[reverse]" + key + "[/reverse]"
            elif key != ' ':
                black_line += key
            else:
                black_line += " "
        black_line += " │"
        lines.append(black_line)

        # White keys row
        white_keys = "A S D F G H J K L"
        white_line = "│ "
        for key in white_keys:
            if key == ' ':
                white_line += " "
            elif key in self.pressed_keys:
                white_line += "[reverse] " + key + " [/reverse]"
            else:
                white_line += " " + key + " "
        white_line += "│"
        lines.append(white_line)

        lines.append("├─────────────────────────────────────────────┤")
        lines.append("│ Z/X: Octave Down/Up  │  1-4: Select Channel│")
        lines.append("│ F1-F6: Sound Effects │  R: Record  │  Q: Quit│")
        lines.append("└─────────────────────────────────────────────┘")

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

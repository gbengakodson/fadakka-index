from kivymd.app import MDApp
from kivymd.uix.label import MDLabel

class TestApp(MDApp):
    def build(self):
        return MDLabel(
            text="Fadakka Index Ready!",
            halign="center",
            theme_text_color="Primary",
            font_style="H4"
        )

if __name__ == "__main__":
    TestApp().run()
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class AutoCompleteInput(TextInput):
    def __init__(self, suggestions=[], dropdown_item_height=30, **kwargs):
        super().__init__(**kwargs)
        self.suggestions = suggestions
        self.dropdown_item_height = dropdown_item_height
        self.multiline = False
        self.dropdown = DropDown()
        self.on_selection = None  
        self.bind(text=self.on_text)
        self.bind(focus=self.on_focus)

    def on_text(self, instance, value):
        self.dropdown.dismiss()
        if not value:
            return
        matching = [s for s in self.suggestions if value.lower() in s.lower()]
        if matching:
            self.dropdown = DropDown()
            for item in matching:
                btn = Button(text=item, size_hint_y=None, height=self.dropdown_item_height)
                btn.bind(on_release=lambda btn, text=item: self.select_item(text))
                self.dropdown.add_widget(btn)
            self.dropdown.open(self)

    def select_item(self, text):
        self.text = text
        self.dropdown.dismiss()
        self.focus = False
        if self.on_selection:
            self.on_selection(text)

    def on_focus(self, instance, focused):
        if not focused:
            self.dropdown.dismiss()
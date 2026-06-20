class Scene:
    def handle_events(self, events):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def draw(self):
        raise NotImplementedError

    def on_language_changed(self):
        return None

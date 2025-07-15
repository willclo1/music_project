from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from frontend.screens.login_screen import LoginScreen
from frontend.screens.dashboard_screen import DashboardScreen
from kivy.core.window import Window

class LoginWrapper(Screen): pass


class DashboardWrapper(Screen):
    def __init__(self, user_email, screen_manager, **kwargs):
        socket = kwargs.pop("socket", None)
        super().__init__(**kwargs)
        self.dashboard_screen = DashboardScreen(user_email, screen_manager=screen_manager,socket=socket)
        self.add_widget(self.dashboard_screen)

    def set_user_email(self, email):
        self.dashboard_screen.set_user_email(email)


class PlaylistApp(MDApp):
    def build(self):
        sm = ScreenManager()

        login_screen = LoginWrapper(name="login")
        login_screen.add_widget(LoginScreen(screen_manager=sm))

        sm.add_widget(login_screen)


        return sm

if __name__ == "__main__":


    Window.size = (1280, 800)
    PlaylistApp().run()

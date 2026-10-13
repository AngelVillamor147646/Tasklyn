"""
Tasklyn — Forgot Password Screen
====================================
Reset the password using the saved recovery key.
"""
from __future__ import annotations
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from utils.helpers import TasklynSnackbar as Snackbar

Builder.load_string("""
<ForgotPasswordScreen>:
    name: 'forgot_password'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(32)
        spacing: dp(16)

        MDLabel:
            text: 'Reset Password'
            font_style: 'H4'
            bold: True
            halign: 'center'
            size_hint_y: None
            height: dp(50)

        MDLabel:
            text: "Enter your name and the recovery key you saved"
            font_style: 'Subtitle1'
            halign: 'center'
            theme_text_color: 'Secondary'
            size_hint_y: None
            height: dp(40)

        MDCard:
            orientation: 'vertical'
            padding: dp(24)
            spacing: dp(16)
            size_hint_x: None
            width: min(dp(420), root.width - dp(64))
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {'center_x': .5}
            radius: [dp(16)]
            elevation: 2
            md_bg_color: [1, 1, 1, 0.05] if app.theme_cls.theme_style == 'Dark' else [0, 0, 0, 0.02]

            MDTextField:
                id: name_field
                hint_text: 'Your name'
                icon_left: 'account'
                size_hint_y: None
                height: dp(56)
                mode: 'fill'
                radius: [dp(10)]

            MDTextField:
                id: key_field
                hint_text: 'Recovery key (XXXX-XXXX-XXXX-XXXX)'
                icon_left: 'key'
                size_hint_y: None
                height: dp(56)
                mode: 'fill'
                radius: [dp(10)]

            MDTextField:
                id: new_password_field
                hint_text: 'New password'
                helper_text: '8+ chars, uppercase, number, special character'
                helper_text_mode: 'on_focus'
                icon_left: 'lock'
                password: True
                size_hint_y: None
                height: dp(56)
                mode: 'fill'
                radius: [dp(10)]

            MDTextField:
                id: confirm_field
                hint_text: 'Confirm new password'
                icon_left: 'lock-check'
                password: True
                size_hint_y: None
                height: dp(56)
                mode: 'fill'
                radius: [dp(10)]

            MDRaisedButton:
                text: 'RESET PASSWORD'
                font_style: 'Button'
                bold: True
                size_hint_x: 1
                size_hint_y: None
                height: dp(50)
                md_bg_color: app.theme_cls.primary_color
                on_release: root.on_reset()

            MDFlatButton:
                text: 'Back to Log In'
                pos_hint: {'center_x': .5}
                size_hint_x: 1
                on_release: root.go_back()

        Widget:
            size_hint_y: 1
""")


class ForgotPasswordScreen(MDScreen):
    def on_pre_enter(self, *args):
        for field_id in ("name_field", "key_field", "new_password_field", "confirm_field"):
            self.ids[field_id].text = ""

    def on_reset(self):
        name = self.ids.name_field.text.strip()
        key = self.ids.key_field.text.strip()
        new_password = self.ids.new_password_field.text
        confirm = self.ids.confirm_field.text

        if not name or not key or not new_password:
            Snackbar(text="Please fill in all fields.", notif_type="error").open()
            return
        if new_password != confirm:
            Snackbar(text="Passwords do not match.", notif_type="error").open()
            return

        from services.auth_service import reset_password
        ok, err = reset_password(name, key, new_password)
        if ok:
            Snackbar(text="Password reset! You can log in now.", notif_type="success").open()
            self.go_back()
        else:
            Snackbar(text=err or "Could not reset password.", notif_type="error").open()

    def go_back(self):
        MDApp.get_running_app().root.current = "login"
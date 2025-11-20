import flet as ft
from client import Client
import logging


class Interface:

    def __init__(self, page: ft.Page):
        self.cliente = Client()
        self.page = page

    def main(self):

        self.page.add(
            ft.Row(
                [
                    self.get_start_connection_button()
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

    def get_start_connection_button(self):
        try:
            button = ft.IconButton(ft.Icons.START, on_click=self.start_connection)
            return button
        except Exception as e:
            logging.error(f"Exceção ao obter o botão que implementa o início da conexão com o servdidor\nLog: {e}")

    def start_connection(self, event):
        try:
            state_connection, mensagem = self.cliente.start_connection()
            if state_connection:
                pass
            else:
                logging.error("Erro ao iniciar conexão com servidor")
        except Exception as e:
            pass




if __name__ == "__main__":
    def main(page: ft.Page):
        page.title = "Cliente UDP"
        page.theme = ft.Theme(font_family="Monospace")
        page.update()
        app = Interface(page)
        app.main()
    ft.app(main, name="Cliente UDP")
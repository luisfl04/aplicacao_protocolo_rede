import flet as ft
from client import Client
import logging
from datetime import datetime


class Interface:

    def __init__(self, page: ft.Page):
        self.cliente = Client()
        self.page = page
        self.mensagens_painel = []

    def main(self):
        self.titulo = ft.Text(
            value="Cliente UDP",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_GREY_900
        )

        self.lista_mensagens = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True
        )
        
        container_mensagens = ft.Container(
            content=self.lista_mensagens,
            height=400,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            padding=15,
            bgcolor=ft.Colors.GREY_50,
            margin=ft.margin.only(top=20)
        )

        btn1 = ft.ElevatedButton(
            "Requisição GET", 
            icon=ft.Icons.DOWNLOAD, 
            on_click=""
        )
    
        btn2 = ft.ElevatedButton(
            "Requisição POST", 
            icon=ft.Icons.UPLOAD, 
            on_click=""
        )
    
        btn3 = ft.ElevatedButton(
            "Requisição DELETE", 
            icon=ft.Icons.DELETE, 
            color=ft.Colors.RED,
            on_click=""
        )

        # Botão extra para limpar o log (útil para testes)
        btn_limpar = ft.TextButton("Limpar Log", on_click=self.limpar_console)

        # Container dos botões (Row para ficarem lado a lado)
        area_botoes = ft.Container(
            content=ft.Row(
                controls=[btn1, btn2, btn3],
                alignment=ft.MainAxisAlignment.CENTER, # Centraliza os botões
                wrap=True # Permite quebrar linha se a tela for pequena
            ),
            padding=ft.padding.symmetric(vertical=10)
        )

        self.page.add(
            self.titulo,
            ft.Divider(),
            area_botoes,
            ft.Text("Console de Saída:", weight="bold"),
            container_mensagens,
            ft.Row([btn_limpar], alignment=ft.MainAxisAlignment.END)
        )


    def limpar_console(self, e):
        self.lista_mensagens.controls.clear()
        self.page.update()

    def adicionar_mensagem_container(self, texto, tipo="info"):
        """
        """

        timestamp = datetime.now().strftime("%H:%M:%S")
        
        cor_icone = ft.Colors.BLUE
        icone = ft.Icons.INFO_OUTLINE
        
        if tipo == "success":
            cor_icone = ft.Colors.GREEN
            icone = ft.Icons.CHECK_CIRCLE_OUTLINE
        elif tipo == "error":
            cor_icone = ft.Colors.RED
            icone = ft.Icons.ERROR_OUTLINE

        item = ft.Row([
            ft.Icon(icone, color=cor_icone),
            ft.Text(f"[{timestamp}] {texto}", size=14, selectable=True)
        ])

        self.lista_mensagens.controls.append(item)
        self.page.update()




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
                text = ft.Text(value="Conexão iniciada", text_align=ft.TextAlign.CENTER)
                self.mensagens_painel.append(text)
                self.page.update()
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
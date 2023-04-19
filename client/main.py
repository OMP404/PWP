import json
import customtkinter as tk
import tkinter
import requests

API_URL = "http://localhost:5000/api/"
HEADERS = {"Content-Type": "application/json"}


class App(tk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Oulu Bars API")
        self.geometry("900x600")
        self.minsize(800, 500)
        # container for all frames
        self.container = tk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # configure grid layout
        self.frames = {MainView: MainView(self.container), BarsListView: BarsListView(
            self.container), BarView: BarView(self.container)}
        self.show_frame(MainView)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def show_bar(self, bar):
        self.frames[BarView].bar = bar
        self.frames[BarView].get_bar_info()
        self.show_frame(BarView)


class MainView(tk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.grid(row=0, column=0, sticky="nsew")
        self.list_bars_button = tk.CTkButton(
            self, text="List bars", command=self.list_bars)
        self.list_bars_button.pack(fill=tk.X, pady=5, padx=10)

    def list_bars(self):
        self.show_frame(BarsListView)

    def show_frame(self, cont):
        frame = app.frames[cont]
        frame.tkraise()


class BarsListView(tk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.grid(row=0, column=0, sticky="nsew")
        self.bars = []
        self.get_bars()
        self.create_buttons()

    def get_bars(self):
        response = requests.get(f"{API_URL}bars/", timeout=5)
        if response.status_code == 200:
            self.bars = response.json()['items']
        else:
            self.parent.show_message_box("Error", "Failed to get bars")

    def create_buttons(self):
        buttons = {}
        for bar in self.bars:
            container = tk.CTkFrame(self)
            container.pack(fill=tk.X, pady=1, padx=5)
            container.grid_columnconfigure(0, weight=1)
            container.grid_columnconfigure((2, 3, 4), weight=0)
            bar_info = f"{bar['name']}, {bar['address']}"
            bar_info_box = tk.CTkLabel(container, text=bar_info)
            bar_info_box.grid(row=0, column=0, padx=5,
                              pady=5, sticky="we", columnspan=2)
            buttons[f"{bar['name']}_button"] = tk.CTkButton(
                container, text="Show bar", command=lambda bar=bar: self.show_bar(bar))
            buttons[f"{bar['name']}_button"].grid(
                row=0, column=2, padx=5, pady=5, sticky="we")
            buttons[f"{bar['name']}_edit_button"] = tk.CTkButton(
                container, text="Edit bar", command=lambda bar=bar: self.edit_bar(bar))
            buttons[f"{bar['name']}_edit_button"].grid(
                row=0, column=3, padx=5, pady=5, sticky="we")
            buttons[f"{bar['name']}_delete_button"] = tk.CTkButton(
                container, text="Delete bar", command=lambda bar=bar: self.delete_bar(bar))
            buttons[f"{bar['name']}_delete_button"].grid(
                row=0, column=4, padx=5, pady=5, sticky="we")

    def show_bar(self, bar):
        app.show_bar(bar)

    def edit_bar(self, bar):
        app.edit_window(bar)

    def delete_bar(self, bar):
        response = requests.delete(f"{API_URL}bars/{bar['name']}/", timeout=5)
        if response.status_code == 200:
            self.parent.show_message_box("Success", "Bar deleted")
            for listbar in self.bars:
                if listbar['name'] == bar['name']:
                    self.bars.remove(listbar)
        else:
            self.parent.show_message_box("Error", "Failed to delete bar")


class BarView(tk.CTkFrame):
    def __init__(self, parent, bar=None, edit=False):
        super().__init__(parent)
        self.bar = bar
        self.parent = parent
        self.edit = edit
        self.grid(row=0, column=0, sticky="nsew")
        self.tapdrinks = []
        self.cocktails = []
        # self.textbox = tk.CTkTextbox(self, font=("Roboto", 16))
        # self.textbox.pack(fill=tk.BOTH, expand=True)

    def get_bar_info(self):
        tapdrinks = requests.get(
            f"{API_URL}bars/{self.bar['name']}/tapdrinks/", timeout=5)
        cocktails = requests.get(
            f"{API_URL}bars/{self.bar['name']}/cocktails/", timeout=5)
        if tapdrinks.status_code == 200:
            jsondata = json.loads(tapdrinks.text)
            self.tapdrinks = jsondata['items']
        else:
            self.parent.show_message_box("Error", "Failed to get bar info")
        if cocktails.status_code == 200:
            jsondata = json.loads(cocktails.text)
            self.cocktails = jsondata['items']
        else:
            self.parent.show_message_box("Error", "Failed to get bar info")
        self.show_bar_info()

    def show_bar_info(self):
        for tapdrink in self.tapdrinks:
            self.create_button_frame_tapdrink(tapdrink)

        for cocktail in self.cocktails:
            self.create_button_frame_cocktail(cocktail)

    def create_button_frame_tapdrink(self, tapdrink):
        button_frame = tk.CTkFrame(self)
        button_frame.pack(fill=tk.X, pady=1, padx=5)
        button_frame.grid_columnconfigure(0, weight=1)
        # create a grid with 3 columns
        drink_infobox = tk.CTkTextbox(
            button_frame, height=8, activate_scrollbars=False)
        drink_infobox.grid(row=0, column=0, padx=5,
                           pady=5, sticky="we", columnspan=2)
        drink_infobox.insert(
            tkinter.END, f"{tapdrink['drink_type']}, {tapdrink['drink_name']} - {tapdrink['price']}€")
        button_edit = tk.CTkButton(
            button_frame, text="Edit", command=lambda tapdrink=tapdrink: self.edit_item(tapdrink), width=100)
        button_delete = tk.CTkButton(
            button_frame, text="Delete", command=lambda tapdrink=tapdrink: self.delete_item(tapdrink), width=100)
        button_edit.grid(row=0, column=2, padx=5, pady=5, sticky="we")
        button_delete.grid(row=0, column=3, padx=5, pady=5, sticky="we")

    def create_button_frame_cocktail(self, cocktail, edit=False):
        button_frame = tk.CTkFrame(self)
        button_frame.pack(fill=tk.X, pady=1, padx=5)
        button_frame.grid_columnconfigure(0, weight=1)
        # create a grid with 3 columns
        drink_infobox = tk.CTkTextbox(
            button_frame, height=8, activate_scrollbars=False)
        drink_infobox.grid(row=0, column=0, padx=5,
                           pady=5, sticky="we", columnspan=2)
        drink_infobox.insert(
            tkinter.END, f"{cocktail['cocktail_name']} - {cocktail['price']}€")
        drink_infobox.configure(state=tk.NORMAL if edit else tk.DISABLED)

        button_edit = tk.CTkButton(
            button_frame, text="Edit", command=lambda cocktail=cocktail: self.edit_item(cocktail), width=100)
        button_delete = tk.CTkButton(
            button_frame, text="Delete", command=lambda cocktail=cocktail: self.delete_item(cocktail), width=100)
        button_edit.grid(row=0, column=2, padx=5, pady=5,
                         sticky="we")
        button_delete.grid(row=0, column=3, padx=5, pady=5,
                           sticky="we")

    def edit_item(self, drink):
        '''Edit item in database'''
        if "drink_type" in drink:
            self.edit_tapdrink(drink)
        else:
            self.edit_cocktail(drink)

    def edit_tapdrink(self, tapdrink):
        dialog = tk.CTkInputDialog(
            text=f'Enter a new type for "{tapdrink["drink_name"]}":')
        new_type = dialog.get_input()
        if new_type == "":
            new_type = tapdrink["drink_type"]
        dialog = tk.CTkInputDialog(
            text=f'Enter a new name for "{tapdrink["drink_name"]}":')
        new_name = dialog.get_input()
        if new_name == "":
            new_name = tapdrink["drink_name"]
        dialog = tk.CTkInputDialog(
            text=f'Enter a new size for "{tapdrink["drink_name"]}":')
        new_size = dialog.get_input()
        if new_size == "":
            new_size = tapdrink["drink_size"]
        dialog = tk.CTkInputDialog(
            text=f'Enter a new price for "{tapdrink["drink_name"]}":')
        new_price = dialog.get_input()
        if new_price == "":
            new_price = tapdrink["price"]
        response = requests.put(f"{API_URL}bars/{tapdrink['bar_name']}/tapdrinks/{tapdrink['drink_name']}/{tapdrink['drink_size']}/",
                                json={"bar_name": tapdrink["bar_name"], "drink_type": new_type, "drink_name": new_name,
                                      "drink_size": new_size, "price": new_price},
                                headers=HEADERS,
                                timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_tapdrink in self.tapdrinks:
                if list_tapdrink["drink_name"] == tapdrink["drink_name"]:
                    list_tapdrink["drink_type"] = new_type
                    list_tapdrink["drink_name"] = new_name
                    list_tapdrink["drink_size"] = new_size
                    list_tapdrink["price"] = new_price
        else:
            print("Error")

    def edit_cocktail(self, cocktail):
        dialog = tk.CTkInputDialog(
            text=f'Enter a new name for "{cocktail["cocktail_name"]}":')
        new_name = dialog.get_input()
        if new_name == "":
            new_name = cocktail["cocktail_name"]
        dialog = tk.CTkInputDialog(
            text=f'Enter a new price for "{cocktail["cocktail_name"]}":')
        new_price = dialog.get_input()
        if new_price == "":
            new_price = cocktail["price"]
        response = requests.put(f"{API_URL}/tapdrinks/{cocktail['drink_name']}/",
                                json={"bar_name": f"{cocktail['bar_name']}",
                                      "cocktail_name": new_name,
                                      "price": new_price},
                                headers=HEADERS,
                                timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_cocktail in self.cocktails:
                if list_cocktail['cocktail_name'] == cocktail['cocktail_name']:
                    list_cocktail['cocktail_name'] = new_name
                    list_cocktail['price'] = new_price
        else:
            print("Error")

    def delete_item(self, drink):
        '''Delete item from database'''
        if "drink_type" in drink:
            self.delete_tapdrink(drink)
        else:
            self.delete_cocktail(drink)

    def delete_tapdrink(self, tapdrink):
        response = requests.delete(f"{API_URL}bars/{tapdrink['bar_name']}/tapdrinks/{tapdrink['drink_name']}/{tapdrink['drink_size']}/",
                                   timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_tapdrink in self.tapdrinks:
                if list_tapdrink["drink_name"] == tapdrink["drink_name"]:
                    self.tapdrinks.remove(list_tapdrink)
        else:
            print("Error")

    def delete_cocktail(self, cocktail):
        response = requests.delete(f"{API_URL}bars/{cocktail['bar_name']}/cocktails/{cocktail['cocktail_name']}/",
                                   timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_cocktail in self.cocktails:
                if list_cocktail["cocktail_name"] == cocktail["cocktail_name"]:
                    self.cocktails.remove(list_cocktail)
        else:
            print("Error")


if __name__ == "__main__":
    app = App()
    app.mainloop()

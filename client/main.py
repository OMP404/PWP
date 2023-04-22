import json
import customtkinter as tk
import tkinter
import requests

API_URL = "http://localhost:5000/api/"
BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}


class RootApp(tk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Oulu Bars API")
        self.geometry("900x600")
        self.minsize(800, 500)
        self.latest_frames = []
        # top bar
        self.top_bar = TopBar(self)

        # container for all frames
        self.container = tk.CTkFrame(self, corner_radius=0)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)


class TopBar(tk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, height=50, fg_color="#2c3e50", corner_radius=0)
        self.parent = parent
        self.pack(fill=tk.X, side=tk.TOP)
        self.back_button = tk.CTkButton(
            self, text="Back", command=self.back, width=10)
        self.back_button.pack(side=tk.LEFT, padx=10, pady=5)

    def back(self):
        if len(self.parent.latest_frames) > 1:
            self.parent.latest_frames.pop()
            app.show_prev_frame(self.parent.latest_frames[-1])
        else:
            app.show_prev_frame(MainView)


class App():
    def __init__(self, container, root):
        self.container = container
        self.root = root
        self.frames = {}

    def init_frames(self):
        frames = [MainView, BarsListView, AddBarView]
        for frame in frames:
            self.frames[frame] = frame(self.container, self)
        self.show_frame(MainView)

    def show_bar(self, bar):
        self.frames[BarView] = BarView(self.container, self, bar)
        self.show_frame(BarView)

    def show_edit_drink_frame(self, drink):
        self.frames[EditDrinkView] = EditDrinkView(
            self.container, self, drink, self.frames[BarView])
        self.show_frame(EditDrinkView)

    def show_frame(self, frame):
        self.root.latest_frames.append(frame)
        new_frame = self.frames[frame]
        new_frame.tkraise()

    def show_prev_frame(self, frame):
        new_frame = self.frames[frame]
        new_frame.tkraise()

    def show_message_box(self, title, message):
        popup = tk.CTkToplevel(self.root, takefocus=True)
        screen_width = int(self.root.winfo_width()/2)
        screen_height = int(self.root.winfo_height()/2)
        screen_pos_x = self.root.winfo_x()
        screen_pos_y = self.root.winfo_y()
        pos_x = screen_pos_x + int(screen_width/2)
        pos_y = screen_pos_y + int(screen_height/2)
        popup.geometry(
            f"{screen_width}x{screen_height}+{pos_x}+{pos_y}")
        popup.grab_set()
        frame_title = tk.CTkLabel(popup, text=title, font=("Arial", 20))
        frame_title.pack(fill=tk.X, pady=5, padx=10)
        text = tk.CTkLabel(popup, text=message, font=("Arial", 14))
        text.pack(fill=tk.X, pady=5, padx=10)
        okbutton = tk.CTkButton(popup, text="OK", command=popup.destroy)
        okbutton.pack(fill=tk.X, pady=5, padx=20)
        autoclose_label = tk.CTkLabel(
            popup, text="This window will close in 3 seconds...")
        autoclose_label.pack(fill=tk.X, pady=20, padx=10)
        popup.after(3000, popup.destroy)  # destroy after 3 seconds


class MainView(tk.CTkFrame, App):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.grid(row=0, column=0, sticky="nsew")
        # main text
        self.title = tk.CTkLabel(
            self, text="Oulu Bars API", font=("Arial", 26))
        self.title.pack(fill=tk.X, pady=50)
        self.list_bars_button = tk.CTkButton(
            self, text="List bars", command=self.list_bars)
        self.list_bars_button.pack(fill=tk.X, pady=5, padx=10)
        self.add_bar_button = tk.CTkButton(
            self, text="Add bar", command=self.add_bar)
        self.add_bar_button.pack(fill=tk.X, pady=5, padx=10)

    def list_bars(self):
        self.app.show_frame(BarsListView)

    def add_bar(self):
        self.app.show_prev_frame(AddBarView)


class AddBarView(tk.CTkFrame, App):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.parent = parent
        self.grid(row=0, column=0, sticky="nsew")
        self.title = tk.CTkLabel(
            self, text="Add a bar", font=("Arial", 24))
        self.title.pack(fill=tk.X, pady=25)
        self.name_label = tk.CTkLabel(self, text="Name", anchor="w")
        self.name_label.pack(fill=tk.X, pady=(5, 0), padx=20)
        self.name_entry = tk.CTkEntry(self, placeholder_text="Name of the bar")
        self.name_entry.pack(fill=tk.X, pady=(2, 5), padx=10)
        self.address_label = tk.CTkLabel(self, text="Address", anchor="w")
        self.address_label.pack(fill=tk.X, pady=(5, 0), padx=20)
        self.address_entry = tk.CTkEntry(self, placeholder_text="Street, City")
        self.address_entry.pack(fill=tk.X, pady=(2, 5), padx=10)
        self.buttons_frame = tk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill=tk.X, pady=5, expand=True)
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)
        self.submit_button = tk.CTkButton(
            self.buttons_frame, text="Submit", command=self.submit_bar)
        self.submit_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.cancel_button = tk.CTkButton(
            self.buttons_frame, text="Cancel", command=self.cancel_button_func)
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def submit_bar(self):
        name = self.name_entry.get()
        address = self.address_entry.get()
        if name and address:
            data = {"name": name, "address": address}
            response = requests.post(
                f"{API_URL}bars/", json=data, headers=HEADERS, timeout=5)
            if response.status_code == 201:
                self.app.show_message_box("Success", "Bar added")
                self.name_entry.delete(0, tkinter.END)
                self.address_entry.delete(0, tkinter.END)
                self.app.show_frame(MainView)
            else:
                self.app.show_message_box("Error", "Failed to add bar")
        else:
            self.app.show_message_box(
                "Error", "Name and address must be filled")

    def cancel_button_func(self):
        self.app.show_prev_frame(MainView)


class BarsListView(tk.CTkFrame, App):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.grid(row=0, column=0, sticky="nsew")
        self.bars = []
        self.get_bars()
        self.containers = {}
        self.containers['buttons'] = {}
        self.create_buttons()

    def get_bars(self):
        response = requests.get(f"{API_URL}bars/", timeout=5)
        if response.status_code == 200:
            self.bars = response.json()['items']
        else:
            self.app.show_message_box("Error", "Failed to get bars")

    def create_buttons(self):
        buttons = {}
        for bar in self.bars:
            self.containers[f"{bar['name']}_container"] = tk.CTkFrame(
                self, corner_radius=0)
            self.containers[f"{bar['name']}_container"].pack(
                fill=tk.X, pady=1, padx=0)
            self.containers[f"{bar['name']}_container"].grid_columnconfigure(
                0, weight=1)
            self.containers[f"{bar['name']}_container"].grid_columnconfigure(
                (2, 3, 4), weight=0)
            bar_info = f"{bar['name']}, {bar['address']}"
            bar_info_box = tk.CTkLabel(
                self.containers[f"{bar['name']}_container"], text=bar_info)
            bar_info_box.grid(row=0, column=0, padx=5,
                              pady=5, sticky="we", columnspan=2)
            buttons[f"{bar['name']}_button"] = tk.CTkButton(
                self.containers[f"{bar['name']}_container"], text="Show bar", command=lambda bar=bar: self.app.show_bar(bar))
            buttons[f"{bar['name']}_button"].grid(
                row=0, column=2, padx=5, pady=5, sticky="we")
            buttons[f"{bar['name']}_edit_button"] = tk.CTkButton(
                self.containers[f"{bar['name']}_container"], text="Edit bar", command=lambda bar=bar: self.edit_bar(bar))
            buttons[f"{bar['name']}_edit_button"].grid(
                row=0, column=3, padx=5, pady=5, sticky="we")
            buttons[f"{bar['name']}_delete_button"] = tk.CTkButton(
                self.containers[f"{bar['name']}_container"], text="Delete bar", command=lambda bar=bar: self.delete_bar(bar))
            buttons[f"{bar['name']}_delete_button"].grid(
                row=0, column=4, padx=5, pady=5, sticky="we")

    def edit_bar(self, _):
        self.app.show_message_box("Error", "Not implemented yet")

    def delete_bar(self, bar):
        url = bar['@controls']['self']['href']
        response = requests.delete(BASE_URL + url, timeout=5)
        # FIXME gives 404 for some bar names (does so with # in bar name)
        if response.status_code == 204:
            self.app.show_message_box("Success", "Bar deleted")
            for listbar in self.bars:
                if listbar['name'] == bar['name']:
                    self.bars.remove(listbar)
                    self.containers[f"{bar['name']}_container"].destroy()
                    del self.containers[f"{bar['name']}_container"]
                    break
        else:
            self.app.show_message_box("Error", "Failed to delete bar")


class BarView(tk.CTkFrame, App):
    def __init__(self, parent, app, bar=None, edit=False):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.bar = bar
        self.edit = edit
        self.grid(row=0, column=0, sticky="nsew")
        self.tapdrinks = []
        self.cocktails = []
        self.buttonframes = {}
        self.add_button = None
        self.get_bar_info()
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
            self.app.show_message_box("Error", "Failed to get tapdrinks info")
        if cocktails.status_code == 200:
            jsondata = json.loads(cocktails.text)
            self.cocktails = jsondata['items']
        else:
            self.app.show_message_box("Error", "Failed to get cocktails info")
        self.show_bar_info()

    def show_bar_info(self):
        if len(self.tapdrinks) == 0 and len(self.cocktails) == 0:
            no_drinks_info = tk.CTkLabel(
                self, text="No drinks found in this bar", font=("Roboto", 20))
            no_drinks_info.pack(fill=tk.X,
                                pady=10, anchor="n")
        for tapdrink in self.tapdrinks:
            self.create_button_frame_tapdrink(tapdrink)

        for cocktail in self.cocktails:
            self.create_button_frame_cocktail(cocktail)
        self.create_add_button()

    def create_button_frame_tapdrink(self, tapdrink, edit=False):
        self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"] = tk.CTkFrame(
            self, corner_radius=0)
        self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"].pack(
            fill=tk.X, pady=1, padx=0)
        self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"].grid_columnconfigure(
            0, weight=1)
        # create a grid with 3 columns
        drink_infobox = tk.CTkTextbox(
            self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"], height=8, activate_scrollbars=False)
        drink_infobox.grid(row=0, column=0, padx=5,
                           pady=5, sticky="we", columnspan=2)
        drink_infobox.insert(
            tkinter.END, f"{tapdrink['drink_type']}, {tapdrink['drink_name']}, {tapdrink['drink_size']} - {tapdrink['price']}€")
        drink_infobox.configure(state=tk.NORMAL if edit else tk.DISABLED)

        button_edit = tk.CTkButton(
            self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"], text="Edit", command=lambda tapdrink=tapdrink: self.edit_item(tapdrink), width=100)
        button_delete = tk.CTkButton(
            self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"], text="Delete", command=lambda tapdrink=tapdrink: self.delete_item(tapdrink), width=100)
        button_edit.grid(row=0, column=2, padx=5, pady=5, sticky="we")
        button_delete.grid(row=0, column=3, padx=5, pady=5, sticky="we")

    def create_button_frame_cocktail(self, cocktail, edit=False):
        self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"] = tk.CTkFrame(
            self, corner_radius=0)
        self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"].pack(
            fill=tk.X, pady=1, padx=0)
        self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"].grid_columnconfigure(
            0, weight=1)
        # create a grid with 3 columns
        drink_infobox = tk.CTkTextbox(
            self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"], height=8, activate_scrollbars=False)
        drink_infobox.grid(row=0, column=0, padx=5,
                           pady=5, sticky="we", columnspan=2)
        drink_infobox.insert(
            tkinter.END, f"{cocktail['cocktail_name']} - {cocktail['price']}€")
        drink_infobox.configure(state=tk.NORMAL if edit else tk.DISABLED)

        button_edit = tk.CTkButton(
            self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"], text="Edit", command=lambda cocktail=cocktail: self.edit_item(cocktail), width=100)
        button_delete = tk.CTkButton(
            self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"], text="Delete", command=lambda cocktail=cocktail: self.delete_item(cocktail), width=100)
        button_edit.grid(row=0, column=2, padx=5, pady=5,
                         sticky="we")
        button_delete.grid(row=0, column=3, padx=5, pady=5,
                           sticky="we")

    def create_add_button(self):
        self.add_button = tk.CTkButton(
            self, text="Add bar", command=self.add_item)
        self.add_button.pack(pady=5, anchor="n")

    def add_item(self):
        # TODO
        self.app.show_message_box("Error", "Not implemented yet")

    def edit_item(self, drink):
        '''Edit item in database'''
        self.app.show_edit_drink_frame(drink)

    def update_tapdrink(self, tapdrink, old_name):
        self.buttonframes[f"{tapdrink['bar_name']}_{old_name}"].destroy(
        )
        del self.buttonframes[f"{tapdrink['bar_name']}_{old_name}"]
        self.add_button.destroy()
        self.create_button_frame_tapdrink(tapdrink)
        self.create_add_button()

    def update_cocktail(self, cocktail, old_name):
        self.buttonframes[f"{cocktail['bar_name']}_{old_name}"].destroy(
        )
        del self.buttonframes[f"{cocktail['bar_name']}_{old_name}"]
        self.add_button.destroy()
        self.create_button_frame_cocktail(cocktail)
        self.create_add_button()

    def delete_item(self, drink):
        '''Delete item from database'''
        if "drink_type" in drink:
            self.delete_tapdrink(drink)
        else:
            self.delete_cocktail(drink)

    def delete_tapdrink(self, tapdrink):
        url = tapdrink["@controls"]["self"]["href"]
        response = requests.delete(BASE_URL + url,
                                   timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_tapdrink in self.tapdrinks:
                if list_tapdrink["drink_name"] == tapdrink["drink_name"]:
                    self.tapdrinks.remove(list_tapdrink)
                    self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"].destroy(
                    )
                    del self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"]
                    break
        else:
            print("Error")

    def delete_cocktail(self, cocktail):
        url = cocktail["@controls"]["self"]["href"]
        response = requests.delete(BASE_URL + url,
                                   timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_cocktail in self.cocktails:
                if list_cocktail["cocktail_name"] == cocktail["cocktail_name"]:
                    self.cocktails.remove(list_cocktail)
                    self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"].destroy(
                    )
                    del self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"]
                    break
        else:
            print("Error")


class EditDrinkView(tk.CTkFrame, App):
    def __init__(self, parent, app, drink, bar_parent):
        super().__init__(parent)
        self.app = app
        self.drink = drink
        self.parent = parent
        self.grid(row=0, column=0, sticky="nsew")
        self.bar_parent = bar_parent
        self.bar = self.drink["bar_name"]
        self.drinktype = "tapdrink" if "drink_type" in self.drink else "cocktail"
        self.title = tk.CTkLabel(
            self, text=f"Edit {self.drinktype}", font=("Arial", 24))
        self.title.pack(fill=tk.X, pady=25)
        if self.drinktype == "tapdrink":
            self.drink_type_label = tk.CTkLabel(
                self, text="Drink Type", anchor="w")
            self.drink_type_label.pack(fill=tk.X, pady=(5, 0), padx=20)
            self.drink_type_entry = tk.CTkEntry(
                self, placeholder_text="Type of the drink")
            self.drink_type_entry.pack(fill=tk.X, pady=(2, 5), padx=10)
        self.name_label = tk.CTkLabel(self, text="Drink Name", anchor="w")
        self.name_label.pack(fill=tk.X, pady=(5, 0), padx=20)
        self.name_entry = tk.CTkEntry(
            self, placeholder_text=f"Name of the {self.drinktype}")
        self.name_entry.pack(fill=tk.X, pady=(2, 5), padx=10)
        if self.drinktype == "tapdrink":
            self.size_label = tk.CTkLabel(self, text="Size", anchor="w")
            self.size_label.pack(fill=tk.X, pady=(5, 0), padx=20)
            self.size_entry = tk.CTkEntry(
                self, placeholder_text="Size of the drink")
            self.size_entry.pack(fill=tk.X, pady=(2, 5), padx=10)
        self.price_label = tk.CTkLabel(self, text="Price", anchor="w")
        self.price_label.pack(fill=tk.X, pady=(5, 0), padx=20)
        self.price_entry = tk.CTkEntry(
            self, placeholder_text="Price of the drink")
        self.price_entry.pack(fill=tk.X, pady=(2, 5), padx=10)
        self.buttons_frame = tk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill=tk.X, pady=5, expand=True)
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)
        self.submit_button = tk.CTkButton(
            self.buttons_frame, text="Submit", command=self.submit_edited_drink if self.drinktype == "tapdrink" else self.submit_edited_cocktail)
        self.submit_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.cancel_button = tk.CTkButton(
            self.buttons_frame, text="Cancel", command=self.cancel_button_func)
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def cancel_button_func(self):
        self.app.root.latest_frames.pop()
        self.app.show_prev_frame(BarView)

    def submit_edited_drink(self):
        old_name = self.drink["drink_name"]
        if self.drink_type_entry.get() == "":
            drink_type = self.drink["drink_type"]
        else:
            drink_type = self.drink_type_entry.get()
            self.drink['drink_type'] = drink_type
        if self.name_entry.get() == "":
            name = self.drink["drink_name"]
        else:
            name = self.name_entry.get()
            self.drink['drink_name'] = name
        if self.size_entry.get() == "":
            size = self.drink["drink_size"]
        else:
            size = float(self.size_entry.get())
            self.drink['drink_size'] = size
        if self.price_entry.get() == "":
            price = self.drink["price"]
        else:
            price = self.price_entry.get()
            self.drink['price'] = price
        url = self.drink["@controls"]["self"]["href"]
        response = requests.put(BASE_URL + url,
                                json={"bar_name": self.bar,
                                      "drink_type": drink_type,
                                      "drink_name": name,
                                      "drink_size": size,
                                      "price": price},
                                headers=HEADERS, timeout=5)
        if response.status_code == 204:
            self.app.show_message_box("Success", "Drink edited")
            self.drink_type_entry.delete(0, tkinter.END)
            self.name_entry.delete(0, tkinter.END)
            self.size_entry.delete(0, tkinter.END)
            self.price_entry.delete(0, tkinter.END)
            self.bar_parent.update_tapdrink(self.drink, old_name)
            self.app.show_prev_frame(BarView)
        else:
            self.app.show_message_box("Error", "Drink could not be edited")

    def submit_edited_cocktail(self):
        old_name = self.drink["cocktail_name"]
        if self.name_entry.get() == "":
            name = self.drink["cocktail_name"]
        else:
            name = self.name_entry.get()
            self.drink['cocktail_name'] = name
        if self.price_entry.get() == "":
            price = self.drink["price"]
        else:
            price = self.price_entry.get()
            self.drink['price'] = price
        url = self.drink["@controls"]["self"]["href"]
        response = requests.put(BASE_URL + url,
                                json={"bar_name": self.bar,
                                      "cocktail_name": name,
                                      "price": price},
                                headers=HEADERS, timeout=5)
        if response.status_code == 204:
            self.app.show_message_box("Success", "Cocktail edited")
            self.name_entry.delete(0, tkinter.END)
            self.price_entry.delete(0, tkinter.END)
            self.bar_parent.update_cocktail(self.drink, old_name)
            self.app.root.latest_frames.pop()
            self.app.show_prev_frame(BarView)

        else:
            self.app.show_message_box("Error", "Cocktail could not be edited")


if __name__ == "__main__":
    rootapp = RootApp()
    app = App(rootapp.container, rootapp)
    app.init_frames()
    rootapp.mainloop()

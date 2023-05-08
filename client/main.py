"""
Client for the Oulu Bars API.
"""

import json
import tkinter

import customtkinter as tk
import requests
from requests.exceptions import ConnectionError

BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api/"
HEADERS = {"Content-Type": "application/json"}


class RootApp(tk.CTk):
    """
    This class represents the root application window for the Oulu Bars API. 
    It inherits from the customtkinter.CTk class.
    """

    def __init__(self):
        '''
        Initializes the root application window, sets the title, 
        geometry and minimum size of the window. 
        Also creates the top bar and container for all frames.
        '''
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
    """
    This class represents the top bar of the application. 
    It inherits from the customtkinter.CTkFrame class.
    """

    def __init__(self, parent):
        '''
        Initializes the top bar and creates the back button for it.

        Args:
        - parent (tk.CTk): The parent (main) screen for the top bar.
        '''
        super().__init__(parent, height=50, fg_color="#2c3e50", corner_radius=0)
        self.parent = parent
        self.pack(fill=tk.X, side=tk.TOP)
        self.back_button = tk.CTkButton(
            self, text="Back", command=self.back, width=10)
        self.back_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.app = None

    def back(self):
        """
        Returns to the previous frame of the application.
        """
        if len(self.parent.latest_frames) > 1:
            self.parent.latest_frames.pop()
            self.app.show_prev_frame(self.parent.latest_frames[-1])
        else:
            self.app.show_prev_frame(MainView)


class App():
    """
    This class represents the application. 
    It manages what is to be shown on the frame.
    """

    def __init__(self, container, root):
        """
        Initializes the App object.

        Args:
        - container: the container for the frames.
        - root: the root widget of the application.
        """
        self.container = container
        self.root = root
        self.frames = {}

    def init_frames(self):
        """
        Initializes the frames of the application.
        """
        frames = [MainView, AddBarView]
        for frame in frames:
            self.frames[frame] = frame(self.container, self)
        self.show_frame(MainView)

    def show_bar(self, bar):
        """
        Creates and shows a BarView frame for a given bar.

        Args:
        - bar: the bar object to display.
        """
        self.frames[BarView] = BarView(self.container, self, bar)
        self.show_frame(BarView)

    def show_edit_drink_frame(self, drink):
        """
        Creates and shows the EditDrinkView frame for a given drink.

        Args:
        - drink: the drink object to edit.
        """
        self.frames[EditDrinkView] = EditDrinkView(
            self.container, self, drink, self.frames[BarView])
        self.show_frame(EditDrinkView)

    def show_barlist_frame(self):
        self.frames[BarsListView] = BarsListView(self.container, self)
        self.show_frame(BarsListView)

    def show_frame(self, frame):
        """
        Shows a given frame and adds it to "latest_frames" list (=stack).

        Args:
        - frame: the frame to show.
        """
        self.root.latest_frames.append(frame)
        new_frame = self.frames[frame]
        new_frame.tkraise()

    def show_prev_frame(self, frame):
        """
        Shows the previous frame.

        Args:
        - frame: the previous frame to show.
        """
        new_frame = self.frames[frame]
        new_frame.tkraise()

    def show_message_box(self, title, message):
        """
        Shows a popup window with a given title and message.

        Args:
        - title: the title of the popup window.
        - message: the message to display.
        """
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

    def show_error(self, response):
        """
        Uses class methods to show an error popup window.

        Args:
        - response: the response from the server.
        """
        title = f"Error: code {response.status_code}"
        error, reason = self.load_error_message(response)
        self.show_error_box(title, error, reason)

    def show_error_box(self, title, error, reason):
        """
        Shows a popup window with a title, error and reason,
        with more detailed information boxes for the error and reason.

        Args:
        - title: the title of the popup window.
        - error: the error to display.
        - reason: the reason for the error.
        """
        popup = tk.CTkToplevel(self.root, takefocus=True)
        popup.title = "Error"
        screen_width = int(self.root.winfo_width()/2)
        screen_height = int(self.root.winfo_height()*0.75)
        screen_pos_x = self.root.winfo_x()
        screen_pos_y = self.root.winfo_y()
        pos_x = screen_pos_x + int(screen_width/2)
        pos_y = screen_pos_y + int(screen_height*0.25)
        popup.geometry(
            f"{screen_width}x{screen_height}+{pos_x}+{pos_y}")
        popup.grab_set()
        frame_title = tk.CTkLabel(popup, text=title, font=("Arial", 20))
        frame_title.pack(fill=tk.X, pady=5, padx=10)
        error_label = tk.CTkLabel(popup, text="Error:", font=("Arial", 14))
        error_label.pack(padx=10, anchor=tk.W)
        text_error = tk.CTkLabel(
            popup, text=error, font=("Arial", 14), fg_color="black",
            corner_radius=5, justify=tk.LEFT)
        text_error.pack(fill=tk.X, pady=5, padx=20,
                        ipadx=2, ipady=10, anchor=tk.W)
        reason_label = tk.CTkLabel(popup, text="Reason:", font=("Arial", 14))
        reason_label.pack(padx=10, anchor=tk.W)
        text_reason = tk.CTkLabel(
            popup, text=reason, font=("Arial", 14), fg_color="black",
            corner_radius=5, justify=tk.LEFT)
        text_reason.pack(fill=tk.X, pady=5, padx=20,
                         ipadx=2, ipady=10, anchor=tk.W)
        okbutton = tk.CTkButton(popup, text="OK", command=popup.destroy)
        okbutton.pack(fill=tk.X, pady=5, padx=20)

    def load_error_message(self, response):
        """
        Gets the error message and reason from a given response.

        Args:
        - response: the response to get the error message and reason from.

        Returns:
        - response_error: the error message.
        - reason: the reason for the error.
        """
        try:
            errors = json.loads(response.text)['@error']
        except json.JSONDecodeError:
            return "Not found", "The requested resource was not found."
        response_error = errors['@message']
        reasons = errors['@messages']
        return response_error, reasons[0]


class MainView(tk.CTkFrame, App):
    """
    This class represents the main "menu" of the application.
    """

    def __init__(self, parent, app):
        """
        Initializes the main view with 2 buttons.

        Args:
        - parent: the parent (main frame) of the frame.
        - app: the main application object.
        """
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
        """
        Changes the frame to the BarsListView.
        """
        self.app.show_barlist_frame()

    def add_bar(self):
        """
        Changes the frame to the AddBarView.
        """
        self.app.show_prev_frame(AddBarView)


class AddBarView(tk.CTkFrame, App):
    """
    This class represents the frame for adding a bar.
    """

    def __init__(self, parent, app):
        """
        Initializes the AddBarView with entry fields.

        Args:
        - parent: the parent (main frame) of the frame.
        - app: the main application object.
        """
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
        """
        For submitting a new bar with the API.
        """
        name = self.name_entry.get().strip()
        address = self.address_entry.get().strip()
        if name and address:
            data = {"name": name, "address": address}
            try:
                response = requests.post(
                    f"{API_URL}bars/", json=data, headers=HEADERS, timeout=5)
            except ConnectionError:
                self.app.show_message_box(
                    "Error", "Could not connect to the server")
            else:
                if response.status_code == 201:
                    self.app.show_message_box("Success", "Bar added")
                    self.name_entry.delete(0, tkinter.END)
                    self.address_entry.delete(0, tkinter.END)
                    self.app.show_frame(MainView)
                else:
                    self.app.show_error(response)
        else:
            self.app.show_message_box(
                "Error", "Name and address must be filled")

    def cancel_button_func(self):
        """
        For canceling the adding of a new bar.
        """
        self.app.show_prev_frame(MainView)


class BarsListView(tk.CTkFrame, App):
    """
    This class represents the frame for listing bars.
    """

    def __init__(self, parent: tk.CTkFrame, app: App):
        """
        Initializes the BarsListView with a list of bars.

        Args:
        - parent: the parent (main frame) of the frame.
        - app: the main application object.
        """
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
        """
        Uses requests to get all available bars from the API.
        """
        try:
            response = requests.get(f"{API_URL}bars/", timeout=5)
        except ConnectionError:
            self.app.show_message_box(
                "Error", "Could not connect to the server")
        else:
            if response.status_code == 200:
                self.bars = response.json()['items']
            else:
                self.app.show_error(response)

    def create_buttons(self):
        """
        Creates buttons for each bar (edit, delete, view)
        """
        buttons = {}
        if self.bars:
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
                    self.containers[f"{bar['name']}_container"],
                    text="Show bar", command=lambda bar=bar: self.app.show_bar(bar))
                buttons[f"{bar['name']}_button"].grid(
                    row=0, column=2, padx=5, pady=5, sticky="we")
                buttons[f"{bar['name']}_edit_button"] = tk.CTkButton(
                    self.containers[f"{bar['name']}_container"],
                    text="Edit bar", command=lambda bar=bar: self.edit_bar(bar))
                buttons[f"{bar['name']}_edit_button"].grid(
                    row=0, column=3, padx=5, pady=5, sticky="we")
                buttons[f"{bar['name']}_delete_button"] = tk.CTkButton(
                    self.containers[f"{bar['name']}_container"],
                    text="Delete bar", command=lambda bar=bar: self.delete_bar(bar))
                buttons[f"{bar['name']}_delete_button"].grid(
                    row=0, column=4, padx=5, pady=5, sticky="we")
        else:
            self.containers[f"no_bars_title"] = tk.CTkLabel(
                self, text="No bars available")
            self.containers[f"no_bars_title"].pack(fill=tk.X, pady=5, padx=5)

    def edit_bar(self, _):
        """
        Edits a bar, not implemented yet.
        """
        self.app.show_message_box("Error", "Not implemented yet")

    def delete_bar(self, bar):
        """
        Deletes a bar from the database using the API.

        Args:
        - bar: the bar to be deleted.
        """
        url = bar['@controls']['self']['href']
        response = requests.delete(BASE_URL + url, timeout=5)
        if response.status_code == 204:
            self.app.show_message_box("Success", "Bar deleted")
            for listbar in self.bars:
                if listbar['name'] == bar['name']:
                    self.bars.remove(listbar)
                    self.containers[f"{bar['name']}_container"].destroy()
                    del self.containers[f"{bar['name']}_container"]
                    break
        else:
            self.app.show_error(response)


class BarView(tk.CTkFrame, App):
    """
    This class represents the frame for viewing a specific bar.
    """

    def __init__(self, parent: tk.CTkFrame, app: App, bar: dict = None, edit=False):
        """
        Initializes the BarView with a specific bar.

        Args:
        - parent: the parent (main frame) of the frame.
        - app: the main application object.
        - bar: the bar to be viewed.
        - edit: whether the bar info fields should be editable.
        """
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

    def get_bar_info(self):
        """
        Uses requests to get all available tapdrinks and cocktails from the API.
        """
        tapdrinks = requests.get(
            f"{API_URL}bars/{self.bar['name']}/tapdrinks/", timeout=5)
        cocktails = requests.get(
            f"{API_URL}bars/{self.bar['name']}/cocktails/", timeout=5)
        if tapdrinks.status_code == 200:
            jsondata = json.loads(tapdrinks.text)
            self.tapdrinks = jsondata['items']
        else:
            self.app.show_error(tapdrinks)
        if cocktails.status_code == 200:
            jsondata = json.loads(cocktails.text)
            self.cocktails = jsondata['items']
        else:
            self.app.show_error(cocktails)
        self.show_bar_info()

    def show_bar_info(self):
        """"
        Displays the drinks in the bar.
        """
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
        """
        Creates a button frame with buttons for a tapdrink.

        Args:
        - tapdrink: the tapdrink to be displayed.
        - edit: whether info fields should be editable.
        """
        self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"] = tk.CTkFrame(
            self, corner_radius=0)
        self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"].pack(
            fill=tk.X, pady=1, padx=0)
        self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"].grid_columnconfigure(
            0, weight=1)
        # create a grid with 3 columns
        drink_infobox = tk.CTkTextbox(
            self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"],
            height=8, activate_scrollbars=False)
        drink_infobox.grid(row=0, column=0, padx=5,
                           pady=5, sticky="we", columnspan=2)
        drink_infobox.insert(
            tkinter.END,
            f"{tapdrink['drink_type']}, {tapdrink['drink_name']}, {tapdrink['drink_size']} - {tapdrink['price']}€")
        drink_infobox.configure(state=tk.NORMAL if edit else tk.DISABLED)

        button_edit = tk.CTkButton(
            self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"],
            text="Edit",
            command=lambda tapdrink=tapdrink: self.edit_item(tapdrink),
            width=100)
        button_delete = tk.CTkButton(
            self.buttonframes[f"{tapdrink['bar_name']}_{tapdrink['drink_name']}"],
            text="Delete",
            command=lambda tapdrink=tapdrink: self.delete_item(tapdrink),
            width=100)
        button_edit.grid(row=0, column=2, padx=5, pady=5, sticky="we")
        button_delete.grid(row=0, column=3, padx=5, pady=5, sticky="we")

    def create_button_frame_cocktail(self, cocktail, edit=False):
        """
        Creates a button frame with buttons for a cocktail.

        Args:
        - cocktail: the cocktail to be displayed.
        - edit: whether info fields should be editable.
        """
        self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"] = \
            tk.CTkFrame(self, corner_radius=0)
        self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"].pack(
            fill=tk.X, pady=1, padx=0)
        self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"]\
            .grid_columnconfigure(0, weight=1)
        # create a grid with 3 columns
        drink_infobox = tk.CTkTextbox(
            self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"],
            height=8, activate_scrollbars=False)
        drink_infobox.grid(row=0, column=0, padx=5,
                           pady=5, sticky="we", columnspan=2)
        drink_infobox.insert(
            tkinter.END, f"{cocktail['cocktail_name']} - {cocktail['price']}€")
        drink_infobox.configure(state=tk.NORMAL if edit else tk.DISABLED)

        button_edit = tk.CTkButton(
            self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"],
            text="Edit",
            command=lambda cocktail=cocktail: self.edit_item(cocktail),
            width=100)
        button_delete = tk.CTkButton(
            self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"],
            text="Delete",
            command=lambda cocktail=cocktail: self.delete_item(cocktail),
            width=100)
        button_edit.grid(row=0, column=2, padx=5, pady=5, sticky="we")
        button_delete.grid(row=0, column=3, padx=5, pady=5, sticky="we")

    def create_add_button(self):
        """
        Add button to add a new drink.
        """
        self.add_button = tk.CTkButton(
            self, text="Add drink", command=self.add_item)
        self.add_button.pack(pady=5, anchor="n")

    def add_item(self):
        """
        Function for adding a new drink, not implemented yet.
        """
        self.app.show_message_box("Error", "Not implemented yet")

    def edit_item(self, drink):
        '''
        Opens the edit drink frame.

        Args:
        - drink: the drink to be edited.
        '''
        self.app.show_edit_drink_frame(drink)

    def update_tapdrink(self, tapdrink, old_name):
        """
        Updates the tapdrink in the GUI.

        Args:
        - tapdrink: the tapdrink to be updated.
        - old_name: the old name of the tapdrink.
        """
        self.buttonframes[f"{tapdrink['bar_name']}_{old_name}"].destroy(
        )
        del self.buttonframes[f"{tapdrink['bar_name']}_{old_name}"]
        self.add_button.destroy()
        self.create_button_frame_tapdrink(tapdrink)
        self.create_add_button()

    def update_cocktail(self, cocktail, old_name):
        """
        Updates the cocktail in the GUI.

        Args:
        - cocktail: the cocktail to be updated.
        - old_name: the old name of the cocktail.
        """
        self.buttonframes[f"{cocktail['bar_name']}_{old_name}"].destroy(
        )
        del self.buttonframes[f"{cocktail['bar_name']}_{old_name}"]
        self.add_button.destroy()
        self.create_button_frame_cocktail(cocktail)
        self.create_add_button()

    def delete_item(self, drink):
        """
        Forwards the delete request to the correct function.

        Args:
        - drink: the drink to be deleted.
        """
        if "drink_type" in drink:
            self.delete_tapdrink(drink)
        else:
            self.delete_cocktail(drink)

    def delete_tapdrink(self, tapdrink):
        """
        Deletes a tapdrink from the GUI and database using
        a DELETE request.

        Args:
        - tapdrink: the tapdrink to be deleted.
        """
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
            self.app.show_error(response)

    def delete_cocktail(self, cocktail):
        """
        Deletes a cocktail from the GUI and database using
        a DELETE request.

        Args:
        - cocktail: the cocktail to be deleted.
        """
        url = cocktail["@controls"]["self"]["href"]
        response = requests.delete(BASE_URL + url,
                                   timeout=5)
        if response.status_code == 204:
            print("Success")
            for list_cocktail in self.cocktails:
                if list_cocktail["cocktail_name"] == cocktail["cocktail_name"]:
                    self.cocktails.remove(list_cocktail)
                    self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"]\
                        .destroy()
                    del self.buttonframes[f"{cocktail['bar_name']}_{cocktail['cocktail_name']}"]
                    break
        else:
            self.app.show_error(response)


class EditDrinkView(tk.CTkFrame, App):
    """
    This class represents the frame for editing a drink.
    """

    def __init__(self, parent: tk.CTkFrame, app: App, drink: dict, bar_parent: BarView):
        """
        Initializes the frame.

        rgs:
        - parent: the parent (main frame) of the frame.
        - app: the main application object.
        - drink: the drink to be edited.
        - bar_parent: the bar parent (bar frame) of the frame.
        """
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
            self.buttons_frame, text="Submit",
            command=self.submit_edited_drink if self.drinktype == "tapdrink"
            else self.submit_edited_cocktail)
        self.submit_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.cancel_button = tk.CTkButton(
            self.buttons_frame, text="Cancel", command=self.cancel_button_func)
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def cancel_button_func(self):
        """
        Cancels the editing of a drink and returns to the bar view.
        """
        self.app.root.latest_frames.pop()
        self.app.show_prev_frame(BarView)

    def submit_edited_drink(self):
        """
        Submits the edited drink to the database using a PUT request.
        """
        old_name = self.drink["drink_name"]
        drink_type_entry = self.drink_type_entry.get().strip()
        if drink_type_entry == "":
            drink_type = self.drink["drink_type"]
        else:
            drink_type = drink_type_entry
            self.drink['drink_type'] = drink_type
        name_entry = self.name_entry.get().strip()
        if name_entry == "":
            name = self.drink["drink_name"]
        else:
            name = name_entry
            self.drink['drink_name'] = name
        size_entry = self.size_entry.get().strip()
        if size_entry == "":
            size = self.drink["drink_size"]
        else:
            try:
                size = float(size_entry)
            except ValueError:
                self.app.show_message_box(
                    "Input Error", "Size must be a number")
                return
            self.drink['drink_size'] = size
        price_entry = self.price_entry.get().strip()
        if price_entry == "":
            price = self.drink["price"]
        else:
            try:
                price = float(price_entry)
            except ValueError:
                self.app.show_message_box(
                    "Input Error", "Price must be a number")
                return
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
            self.app.show_error(response)

    def submit_edited_cocktail(self):
        """
        Submits the edited cocktail to the database using a PUT request.
        """
        old_name = self.drink["cocktail_name"]
        name_entry = self.name_entry.get().strip()
        if name_entry == "":
            name = self.drink["cocktail_name"]
        else:
            name = name_entry
            self.drink['cocktail_name'] = name
        price_entry = self.price_entry.get().strip()
        if price_entry == "":
            price = self.drink["price"]
        else:
            try:
                price = float(price_entry)
            except ValueError:
                self.app.show_message_box(
                    "Error", "Price must be a number")
                return
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
            self.app.show_error(response)


if __name__ == "__main__":
    rootapp = RootApp()
    main_app = App(rootapp.container, rootapp)
    rootapp.top_bar.app = main_app
    main_app.init_frames()
    rootapp.mainloop()

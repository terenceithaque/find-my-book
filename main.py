# Programme qui permet à l'utilisateur de rechercer un titre de livre ou un nom d'auteur, et afficher sur une carte les librairies qui ont le livre cherché
import tkinter as tk
from tkinter import ttk
from geopy.geocoders import Nominatim
import folium
import requests
import json
from folium.plugins import MarkerCluster
from folium import IFrame
import webview
import keyboard
#from streamlit_folium import folium_static







class BookFinder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="book_finder")

    def rechercher_livre(self, requete, listbox):
        reponse = requests.get(f"https://openlibrary.org/search.json?q={requete}")

        if reponse.status_code == 200:
            donnee = reponse.json()
        else:
            raise Exception("Impossible de retrouver les livres")

        self.livres = donnee["docs"]

        if not self.livres: # S'il n'y a pas de résultat correspondant à la requête de l'utilisateur
            listbox.insert(tk.END, "Aucun résultat pour {}".format(requete))
            return
            

        return[(livre['title'], livre.get('author_name', ['N/A'])[0], # Take first author
                 livre.get('first_publish_year', 'N/A')) for livre in self.livres]

    def obtenir_local_livre(self, index_livre):
        livre_selectionne = self.livres[index_livre]
        librairies = []

        for librairie in livre_selectionne.get("publish_place", []):
            location = self.geolocator.geocode(librairie)
            print(location)
            if location:
                librairies.append({
                    'name' : librairie,
                    'lat' : location.latitude,
                    'lon' : location.longitude
                })

        return librairies

    def display_libraries_on_map(self, index_livre):
        librairies = self.obtenir_local_livre(index_livre)

        if librairies:
            toplevel = tk.Toplevel()
            toplevel.title("Librairies physiques")
            toplevel.geometry("800x600")

            frame = tk.Frame(toplevel)
            frame.pack(fill="both", expand=True)

            map = folium.Map(location = [librairies[0]['lat'], librairies[0]['lon']], zoom_start=10)

            

            for librairie in librairies:
                folium.Marker(
                    location= [librairie['lat'], librairie['lon']],
                    popup = librairie['name']
                ).add_to(map)

             

            map.save("map.html")
            print("Carte enregistrée")
            webview.create_window("Map",
                                  html=map.get_root().render(),
                                width=600, height=800)
            
            webview.start()


            frame.pack()

            toplevel.mainloop()




class Tab:
    "Onglet de recherche"
    def __init__(self, master, book_finder):
        self.frame = ttk.Frame(master)
        self.book_finder = book_finder

        self.input_label = tk.Label(self.frame, text= "Entrez un titre de livre:")
        self.input_label.pack()

        self.input_entry = tk.Entry(self.frame)
        self.input_entry.pack()

        self.search_button = tk.Button(self.frame, text="Rechercher", command = self.search_books)
        self.search_button.pack()

        self.books_listbox = tk.Listbox(self.frame)
        self.books_listbox.pack(padx=10, pady=10, fill="both", expand=True)

        self.books_listbox.bind("<<ListboxSelect>>", self.display_libraries)

    def search_books(self):
        query = self.input_entry.get()
        try:
            books = self.book_finder.rechercher_livre(query, self.books_listbox)
        except Exception as e:
            print(e)
            return
        self.books_listbox.delete(0, tk.END)
        for book in books:
            self.books_listbox.insert(tk.END, book) 

    def display_libraries(self, event):
        selected_index = self.books_listbox.curselection()
        if selected_index:
            index_livre = selected_index[0]
            self.book_finder.display_libraries_on_map(index_livre)             

        


    


class Application(tk.Tk):
    def __init__(self, book_finder):
      tk.Tk.__init__(self)
      self.book_finder = book_finder

      self.title("Find my Book - moteur de recherche pour les livres")
      self.geometry("500x500")

      self.notebook = ttk.Notebook(self)
      self.notebook.pack(fill="both", expand=True)

      self.add_new_tab()

      self.barre_menu = tk.Menu(self)
      self.menu_fichier = tk.Menu(self.barre_menu)
      self.menu_fichier.add_command(label = "Nouvel onglet de recherche  Ctrl + T", command= self.add_new_tab)
      keyboard.add_hotkey("Ctrl + T", self.add_new_tab)
      self.menu_fichier.add_command(label = "Quitter l'application Ctrl + Q", command=self.quit)
      keyboard.add_hotkey("Ctrl + Q", self.quit)
      self.barre_menu.add_cascade(label = "Fichier", menu=self.menu_fichier)
      self.config(menu=self.barre_menu)


      self.bind("<Left>", self.prev_tab)
      self.bind("<Right>", self.next_tab)


    def add_new_tab(self):
        new_tab = Tab(self.notebook, self.book_finder)
        self.notebook.add(new_tab.frame, text="Onglet" + str(len(self.notebook.tabs()))) 

    def prev_tab(self, event=None):
        if self.notebook.index("current") == 0:
            self.notebook.select(len(self.notebook.tabs())-1)
        else:
            self.notebook.select(self.notebook.index("current")-1)

    def next_tab(self, event = None):
        if self.notebook.index("current") == len(self.notebook.tabs()) - 1:
            self.notebook.select(0)
        else:
            self.notebook.select(self.notebook.index("current") + 1)                   




book_finder = BookFinder()
app = Application(book_finder)
app.mainloop()



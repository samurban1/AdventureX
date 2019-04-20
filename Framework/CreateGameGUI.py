"""GUI to easily create game."""

from tkinter import *
import tkinter.messagebox, tkinter.ttk as ttk


class Display:

	def __init__(self):
		self.root = Tk()
		self.root.title('Create Adventure')

		self.tabControl = ttk.Notebook(self.root)

		self.locTab = ttk.Frame(self.tabControl)
		self.objTab = ttk.Frame(self.tabControl)
		self.cmdTab = ttk.Frame(self.tabControl)

		self.tabControl.add(self.locTab, text='Locations')
		self.tabControl.add(self.objTab, text='Objects')
		self.tabControl.add(self.cmdTab, text='Commands')

		self.tabControl.pack(expand=1, fill=BOTH)

		self.create_location_stuff()

		self.root.mainloop()

	def add_entry(self, tab, title, enter_text, row, column, event_function=None, sticky=W+E+N+S, anchor='w',):
		"""Adds an entry box and a title for it."""
		self.__setattr__(title, Entry(getattr(self, tab)))
		getattr(self, title).grid(row=row, column=column, padx=5, pady=5, sticky=sticky)
		getattr(self, title).bind("<Return>", eval(event_function))

		self.__setattr__(title+'Title', Label(getattr(self, tab), text=enter_text, anchor=anchor, padx=5))
		getattr(self, title+'Title').grid(row=row, column=column-1, padx=5, pady=5, sticky=sticky)

	def create_location_stuff(self):
		"""Creates location stuff."""
		row_counter = 0
		loc_entries = [('LocNum', 'Location Number:', ), ('name', 'name:'), ('references', 'references:'), ('canEnter', 'can_enter:')]
		for title, text, func in loc_entries:
			self.add_entry(tab='locTab', title=title, enter_text=text, row=row_counter, column=1, event_function=)
			row_counter += 1

	def entry_handler(self, event):
		self.__setattr__()





display = Display()



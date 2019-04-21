"""GUI to easily create game."""

from tkinter import *
import tkinter.messagebox, tkinter.ttk as ttk
from pyautogui import press
from ttkthemes import ThemedTk
from functools import partial


class Display:

	def __init__(self):
		self.root = ThemedTk(theme="elegance")
		self.root.title('Create Adventure')

		self.tabControl = ttk.Notebook(self.root)

		# Create 3 tabs for: locations, objects, and commands
		self.locTab = ttk.Frame(self.tabControl)
		self.objTab = ttk.Frame(self.tabControl)
		self.cmdTab = ttk.Frame(self.tabControl)

		# Add tabs to ttk.Notebook
		self.tabControl.add(self.locTab, text='Locations')
		self.tabControl.add(self.objTab, text='Objects')
		self.tabControl.add(self.cmdTab, text='Commands')

		self.tabControl.pack(expand=1, fill=BOTH)

		self.row_counter = 0  # keep track of the rows
		self.column_counter = -1
		self.LOCATIONS = {}
		self.OBJECTS = {}
		self.ACTORS = {}
		self.COMMANDS = {}
		self.cur_itemID = None
		self.cur_DICT = 'LOCATIONS'

		self.create_location_stuff()

		self.root.mainloop()

	def add_entry(self, tab_obj, var_name, label_text, column, sticky=W+E+N+S, anchor='w', header=False):
		"""Adds an entry box and a var_name for it."""

		if header:
			setattr(self, var_name+'Title', Label(tab_obj, text=label_text, anchor=anchor, padx=5, font='Helvetica 12 bold'))  # add a label with the
		# text that was passed in and called it the var_name passed in with 'Title' added at the end.
		else:
			setattr(self, var_name + 'Title', Label(tab_obj, text=label_text, anchor=anchor, padx=5))
		getattr(self, var_name+'Title').grid(row=self.row_counter, column=column, padx=5, pady=5, sticky=sticky)

		setattr(self, var_name, Entry(tab_obj))  # set attribute with name: var_name to an Entry object in the tab provided
		getattr(self, var_name).grid(row=self.row_counter, column=column+1, padx=5, pady=5, sticky=sticky)  # grid it

		def entry_handler(event):  # bound to the <Return> key

			item_ID = self.cur_itemID  # this will be either a location number, object name, or actor name
			dictionary = getattr(self, self.cur_DICT)  # use cur_DICT string to get the attribute by the name of the string
			print('dictionaryyy in add_entry:', dictionary)
			print('item IDDDD:', item_ID)

			if dictionary is self.LOCATIONS:
				string = getattr(self, var_name).get()  # get the text from tbe entry box. 
				if var_name == 'references':
					references = [reference.strip() for reference in string.split(',')]  # split by command and strip whitespaces
					dictionary[item_ID]['references'] = references  # put it in references
				elif var_name == 'long_nar':
					dictionary[item_ID]['NARRATIVES'] = {'long': string}  # set the long narrative key to the string. If the user
					# decides that this narrative set will have exceptions, this string will end up being put in the 'general' key.
					#
					# dictionary[item_ID]['NARRATIVES']['long']['exceptions'] = string
				for move in ['N', 'E', 'S', 'W']:
					if var_name == move:
						dictionary[item_ID]['MOVES'][var_name] = string
						break

				else:
					dictionary[item_ID][var_name] = string

			print('entry text:', getattr(self, var_name).get())

			# dictionary[item_ID][var_name] = getattr(self, var_name).get()
			print('dictionary above tab:', dictionary)
			#
			# setattr(self, var_name+'_attr', getattr(self, var_name).get())  # set attribute called whatever the entry name is
			# # to whatever the user typed into entry box.
			# print(getattr(self, var_name+'_attr'))

			press('tab')
			# getattr(self, var_name).delete(0, END)

		getattr(self, var_name).bind("<Return>", entry_handler)  # bind to entry_handler function

		self.row_counter += 1

	def add_label(self, tab_obj, var_name, text, column, two_rows=True, header=(False, False)):
		"""Adds label and grids it."""
		row = self.row_counter+1 if two_rows else self.row_counter
		if header[0]:
			if header[1]:
				setattr(self, var_name, Label(tab_obj, text=text, anchor='w', padx=5, pady=5, font='Helvetica 13 bold'))
			else:
				setattr(self, var_name, Label(tab_obj, text=text, anchor='w', padx=5, pady=5, font='Helvetica 10 bold'))
		else:
			setattr(self, var_name, Label(tab_obj, text=text, anchor='w', padx=5, pady=5))
		getattr(self, var_name).grid(row=row, column=column, padx=5, pady=5, sticky=W)
		if two_rows:
			self.row_counter += 2  # you add two because
		else:
			self.row_counter += 1

	def add_checkboxes(self, tab_obj, var_name, text, column):
		"""Adds checkboxes and associated entry fields."""

		def add_exception():

			getattr(self, entry_name).delete(0, END)

		def checkbox_handler():
			"""Enables/disables entries/buttons."""
			if getattr(self, entry_name).cget('state') == NORMAL:
				getattr(self, entry_name).insert(0, 'DISABLED')
				for item in [entry_name, button_name, text_name]:
					try:
						getattr(self, item).config(state=DISABLED)
					except Exception as e:
						print(e)
						continue

			else:
				for item in [entry_name, button_name]:
					try:
						getattr(self, item).config(state=NORMAL)
					except Exception as e:
						print(e)
						continue
				getattr(self, entry_name).delete(0, END)

			variable = getattr(self, bool_name).get()
			print('check click bool for', bool_name, ':', variable)
			dictionary = getattr(self, self.cur_DICT)
			if dictionary is self.LOCATIONS:
				for exception_name in ['long_exception_chkBox', 'short_exception_chkBox']:
					if var_name == exception_name and variable:
						sub_dict = exception_name.replace('_exception_chkBox', '')
						nar = dictionary[self.cur_itemID]['NARRATIVES'][sub_dict]
						dictionary[self.cur_itemID]['NARRATIVES'][sub_dict] = {'general': nar, 'exceptions': [[{'if': []}]]}
						break

		def exception_entry_handler(event):

			def string2value(item):
				try:
					return int(item)
				except ValueError:
					try:
						if item == 'True':
							return True
						elif item == 'False':
							return False
						else:
							raise ValueError
					except ValueError:
						return item

			string = getattr(self, entry_name).get()
			exception_set = [item.strip() for item in string.split(',')]
			for i in range(len(exception_set)):
				exception_set[i] = string2value(exception_set[i])

			dictionary = getattr(self, self.cur_DICT)
			item_ID = self.cur_itemID
			if dictionary is self.LOCATIONS:
				if 'long' in entry_name:  # if we are dealing with narratives
					print(dictionary[item_ID]['NARRATIVES']['long']['exceptions'])
					# dictionary[item_ID]['NARRATIVES']['long']['exceptions'].append({'if': exception_set})
		# dictionary[item_ID]['NARRATIVES']['long']['exceptions'].append()

		# elif var_name == 'long_exception_text':

		bool_name = var_name.replace('_chkBox', '')
		entry_name = var_name.replace('chkBox', 'entry')
		button_name = var_name.replace('chkBox', 'add_btn')
		label_name = var_name.replace('chkBox', 'label')
		text_name = var_name.replace('chkBox', 'text')

		setattr(self, bool_name, BooleanVar())

		setattr(self, var_name, Checkbutton(tab_obj, text=text, padx=5,
												variable=getattr(self, bool_name),
												command=checkbox_handler))

		getattr(self, var_name).grid(row=self.row_counter, column=column, padx=5, pady=5, sticky=W)

		if 'exception' in var_name:
			self.add_label(tab_obj, label_name, 'Exception:', column=column)

		setattr(self, entry_name, Entry(tab_obj))
		getattr(self, entry_name).grid(row=self.row_counter, column=column, padx=5, pady=5, sticky=W)
		getattr(self, entry_name).insert(0, 'DISABLED')
		getattr(self, entry_name).config(state=DISABLED)
		getattr(self, entry_name).bind('<Return>', exception_entry_handler)

		if 'exception' in var_name:
			print("'exception' in var_name, which is:", var_name)
			setattr(self, button_name, Button(tab_obj, text='Add Another Exception', state=DISABLED, padx=6, pady=6,
																		command=add_exception))
			getattr(self, button_name).grid(row=self.row_counter, column=column+1, padx=5, pady=5, sticky=W)
			self.row_counter += 1

			self.add_entry(tab_obj, text_name, 'Exception Text:', column=column)
			getattr(self, text_name).config(state=DISABLED)

		self.row_counter += 1

	def create_location_stuff(self):
		"""Creates location stuff."""

		def loc_entry_handler(event):

			self.LOCATIONS = {}  # reset it to empty every time user re-enters it.
			self.cur_itemID = self.LocNum.get()
			self.LOCATIONS[self.cur_itemID] = {}
			print(self.LOCATIONS)
			print('cur_loc_num:', self.cur_itemID)
			press('tab')

		# self.add_entry(self.locTab, var_name='LocNum', label_text='Location Number:')
		# Add the location number entry box. This is not done using the add_entry method because it is needed to be done
		# before everything to set up the location dictionary with locNum as the key.

		self.LocNumWarning = Label(self.locTab, text='DO THIS FIRST! --->', anchor='e', padx=5, font='Helvetica 13 bold')
		self.LocNumWarning.grid(row=self.row_counter, column=0, padx=5, pady=5, sticky=W + E + N + S)

		self.LocNumTitle = Label(self.locTab, text='Location Number --->', anchor='w', padx=5)
		self.LocNumTitle.grid(row=self.row_counter, column=1, padx=5, pady=5, sticky=W + E + N + S)

		self.LocNum = Entry(self.locTab)
		self.LocNum.grid(row=self.row_counter, column=2, padx=5, pady=5, sticky=W+E+N+S)
		self.LocNum.bind("<Return>", loc_entry_handler)

		self.row_counter += 3

		ttk.Separator(self.locTab, orient=HORIZONTAL).grid(row=self.row_counter, sticky=NSEW, rowspan=1, columnspan=3)
		self.row_counter += 1

		loc_entries = [('name', 'Name:'), ('references', 'References:'), ('can_enter', 'Can enter:')]
		for var_name, text in loc_entries:
			self.add_entry(self.locTab, var_name=var_name, label_text=text, column=0)

		ttk.Separator(self.locTab, orient=HORIZONTAL).grid(row=self.row_counter, sticky=NSEW, rowspan=1, columnspan=4)

		self.add_label(self.locTab, var_name='narratives_label', text='NARRATIVES', column=0, header=(True, True))

		self.add_entry(self.locTab, var_name='long_nar', label_text='LONG:', column=0, header=True)

		checkboxes = [('long_exception_chkBox', 'Long Exceptions'), ('short_nar_chkBox', 'Short:')]
		for var_name, text in checkboxes:
			print(var_name, text)
			self.add_checkboxes(getattr(self, 'locTab'), var_name, text, column=0)

		self.add_entry(self.locTab, var_name='short_nar', label_text='SHORT:', column=0, header=True)

		self.add_checkboxes(getattr(self, 'locTab'), 'short_exception_chkBox', 'Short Exceptions', column=0)

		self.row_counter = 8

		self.add_entry(self.locTab, 'objects', 'OBJECTS', column=2, header=True)
		print('under objects line:', self.row_counter)

		self.add_label(self.locTab, 'moves', 'MOVES', column=2, two_rows=False, header=(True, True))
		print('under moves line:', self.row_counter)

		move_entries = [('N', 'North:'), ('E', 'East:'), ('S', 'South:'), ('W', 'West:')]
		for var_name, text in move_entries:
			self.add_entry(self.locTab, var_name=var_name, label_text=text, column=2)

		print(self.narratives_label.grid_info()['row'])



display = Display()



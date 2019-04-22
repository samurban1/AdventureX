"""GUI to easily create game."""

from tkinter import *
import tkinter.messagebox, tkinter.ttk as ttk
from pyautogui import press, hotkey
from ttkthemes import ThemedTk
import yaml, random, yamlordereddictloader
from collections import OrderedDict


class Display:

	def __init__(self):
		themes = ["arc", "blue", "elegance"]
		self.root = ThemedTk(theme=random.choice(themes))
		self.root.title('Create Adventure')
		# self.center(self.root)

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

		self.tabControl.bind("<<NotebookTabChanged>>", self.change_cur_DICT)

		self.objTab.bind("<Visibility>", self.create_object_stuff)  # this is only for the first time it opens the Objects tab

		self.row_counter = 0  # to keep track of the rows
		self.LOCATIONS = {}
		self.OBJECTS = {}
		self.ACTORS = {}
		self.COMMANDS = {}
		self.cur_itemID = None
		self.cur_DICT = 'LOCATIONS'

		self.create_location_stuff()
		print(self.tabControl.tab(self.tabControl.select(), "text"))

		self.root.mainloop()

	def change_cur_DICT(self, event):
		"""Updates the current dictionary."""
		curTab = self.tabControl.tab(self.tabControl.select(), "text")
		print('current tab:', curTab)
		if curTab == 'Locations':
			self.cur_DICT = 'LOCATIONS'
			self.cur_itemID = getattr(self, 'LocNumEntry').get()
		elif curTab == 'Objects':
			self.cur_DICT = 'OBJECTS'
			self.cur_itemID = getattr(self, 'ObjNameEntry').get()
		print('current ITemID:', self.cur_itemID)
		self.tabControl.focus()

	def add_entry(self, tab_obj, var_name, label_text, column, sticky=W+E+N+S, anchor='w', header=False):
		"""Adds an entry box and a var_name for it."""

		if header:  # if it is a header, then change the font to 'xxx bold'
			setattr(self, var_name+'Title', Label(tab_obj, text=label_text, anchor=anchor, padx=5, font='Helvetica 12 bold'))  # add a label with the
		# text that was passed in and called it var_name passed in + 'Title' added at the end.
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
				print('varname in if dict is self locations:', var_name)
				string = getattr(self, var_name).get()  # get the text from tbe entry box.
				if 'references' in var_name:
					print('this is the item id in references if:', item_ID, 'and the self.id:', self.cur_itemID)
					dictionary[item_ID]['visited'] = 0
					references = [reference.strip() for reference in string.split(',')]  # split by command and strip whitespaces
					dictionary[item_ID]['references'] = references  # put it in references
					print('this is the string:', string)
					print('{}[{}]["references"] = (references:)', references)

				elif var_name == 'can_enter':
					if string == 'always':
						dictionary[item_ID][var_name] = string
					else:
						condition_sets = string.split('.')
						all_conditions = []
						for cond_set in condition_sets:
							condition = [item.strip() for item in cond_set.split(',')]
							all_conditions.append(condition)
						dictionary[item_ID][var_name] = all_conditions

				elif var_name == 'long_nar' or var_name == 'short_nar':
					if 'NARRATIVES' in dictionary[item_ID]:
						dictionary[item_ID]['NARRATIVES'].update({var_name[:-4]: string})  # set the long narrative key to the string. If the user
					# decides that this narrative set will have exceptions, this string will end up being put in the 'general' key.
					else:
						dictionary[item_ID]['NARRATIVES'] = {var_name[:-4]: string}

				elif var_name == 'long_exception_text' or var_name == 'short_exception_text':
					sub_dict = var_name.replace('_exception_text', '')
					dictionary[item_ID]['NARRATIVES'][sub_dict]['exceptions'].append([{'if': self.all_conditions,
																						'narrative': string}])
				elif var_name in ['N', 'E', 'S', 'W']:
					dictionary[item_ID]['MOVES'][var_name] = string

				else:
					print('doing the else')
					dictionary[item_ID][var_name] = string

				print('dictionary in if dict is self locations:', self.LOCATIONS)

			elif dictionary is self.OBJECTS:
				print('varname in if dict is self locations:', var_name)
				string = getattr(self, var_name).get()  # get the text from tbe entry box.
				if 'references' in var_name:
					print('this is the item id in references if:', item_ID, 'and the self.id:', self.cur_itemID)
					references = [reference.strip() for reference in string.split(',')]  # split by command and strip whitespaces
					dictionary[item_ID]['references'] = references  # put it in references
					print('this is the string:', string)
					print('{}[{}]["references"] = (references:)', references)
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

	def add_label(self, tab_obj, var_name, text, column, two_rows=True, header=(False, False), bg=None):
		"""Adds label and grids it."""
		row = self.row_counter+1 if two_rows else self.row_counter
		if header[0]:
			if header[1]:
				setattr(self, var_name, Label(tab_obj, text=text, anchor='w', padx=5, pady=5, font='Helvetica 13 bold', bg=bg))
			else:
				setattr(self, var_name, Label(tab_obj, text=text, anchor='w', padx=5, pady=5, font='Helvetica 10 bold', bg=bg))
		else:
			setattr(self, var_name, Label(tab_obj, text=text, anchor='w', padx=5, pady=5, bg=bg))
		getattr(self, var_name).grid(row=row, column=column, padx=5, pady=5, sticky=W)
		if two_rows:
			self.row_counter += 2  # you add two because
		else:
			self.row_counter += 1

	def add_button(self, tab_obj, btn_var, entry_var, text, row, column):
		"""Adds a button."""

		def exception_entry_handler(event):

			string = getattr(self, entry_var).get()
			exception_set = self.string2value(string)

			print(exception_set)
			# self.all_conditions.append(exception_set)
			# print(self.all_conditions)

			getattr(self, btn_var).invoke()

		def click_handler():
			getattr(self, entry_var).delete(0, END)

		setattr(self, btn_var, Button(tab_obj, text=text, padx=6, pady=6,
										command=click_handler, highlightbackground='#5FD052', fg='black'))
		getattr(self, btn_var).grid(row=row, column=column, padx=5, pady=5, sticky=W)

	@staticmethod
	def string2value(string):

		def to_value (item):
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

		exception_set = [item.strip() for item in string.split(',')]
		for i in range(len(exception_set)):
			exception_set[i] = to_value(exception_set[i])
		return exception_set

	def add_checkboxes(self, tab_obj, var_name, text, column):
		"""Adds checkboxes and associated entry fields."""

		def add_exception_set():
			self.all_conditions = []
			getattr(self, entry_name).delete(0, END)
			getattr(self, text_name).delete(0, END)

		def add_condition():
			getattr(self, entry_name).delete(0, END)

		def checkbox_handler():
			"""Enables/disables entries/buttons."""
			variable = getattr(self, bool_name).get()
			print('check click bool for', bool_name, ':', variable)

			if not variable:
				getattr(self, entry_name).insert(0, 'Split condset items w commas')
				for item in [entry_name, cond_button_name, text_name, except_button_name]:
					try:
						getattr(self, item).config(state=DISABLED)
					except Exception as e:
						print(e)
						continue

			else:
				for item in [entry_name, cond_button_name, text_name, except_button_name]:
					try:
						getattr(self, item).config(state=NORMAL)
					except Exception as e:
						print(e)
						continue
				getattr(self, entry_name).delete(0, END)
				getattr(self, text_name).delete(0, END)

			dictionary = getattr(self, self.cur_DICT)
			if dictionary is self.LOCATIONS:
				for exception_name in ['long_exception_chkBox', 'short_exception_chkBox']:
					if var_name == exception_name and variable:
						sub_dict = exception_name.replace('_exception_chkBox', '')
						nar = dictionary[self.cur_itemID]['NARRATIVES'][sub_dict]
						dictionary[self.cur_itemID]['NARRATIVES'][sub_dict] = {'general': nar, 'exceptions': []}
						break

		def exception_entry_handler(event):

			string = getattr(self, entry_name).get()
			exception_set = self.string2value(string)

			self.all_conditions.append(exception_set)
			print(self.all_conditions)

			getattr(self, cond_button_name).invoke()

		bool_name = var_name.replace('_chkBox', '')
		entry_name = var_name.replace('chkBox', 'entry')
		cond_button_name = var_name.replace('chkBox', 'add_condition')
		except_button_name = var_name.replace('chkBox', 'add_exception')
		label_name = var_name.replace('chkBox', 'label')
		text_name = var_name.replace('chkBox', 'text')

		self.all_conditions = []

		setattr(self, bool_name, BooleanVar())

		setattr(self, var_name, Checkbutton(tab_obj, text=text, padx=5,
												variable=getattr(self, bool_name),
												command=checkbox_handler))

		getattr(self, var_name).grid(row=self.row_counter, column=column, padx=5, pady=5, sticky=W)

		if 'exception' in var_name:
			self.add_label(tab_obj, label_name, 'Condition:', column=column)

			setattr(self, entry_name, Entry(tab_obj))
			getattr(self, entry_name).grid(row=self.row_counter, column=column, padx=5, pady=5, sticky=W)
			getattr(self, entry_name).insert(0, 'Split condset items w commas')
			getattr(self, entry_name).config(state=DISABLED)
			getattr(self, entry_name).bind('<Return>', exception_entry_handler)

			print("'exception' in var_name, which is:", var_name)
			setattr(self, cond_button_name, Button(tab_obj, text='Add Condition', state=DISABLED, padx=6, pady=6,
																		command=add_condition, highlightbackground='#5FD052', fg='black'))
			getattr(self, cond_button_name).grid(row=self.row_counter, column=column+1, padx=5, pady=5, sticky=W)
			self.row_counter += 1

			self.add_entry(tab_obj, text_name, 'Text 2 display 4 above conditions:', column=column)
			getattr(self, text_name).insert(0, 'DISABLED')
			getattr(self, text_name).config(state=DISABLED)

			self.row_counter += 1
			setattr(self, except_button_name, Button(tab_obj, text='Add Exception Set', state=DISABLED, padx=6, pady=6, fg='black',
															command=add_exception_set, width=50, highlightbackground='#61B5F5'))
			getattr(self, except_button_name).grid(row=self.row_counter, column=column, columnspan=2, padx=5, pady=5, sticky=W)

		self.row_counter += 1

	def add_clear_button(self, tab_obj, btn_name):
		"""Adds a button to clear the current dictionary, for user to be able to start over."""
		setattr(self, btn_name, Button(tab_obj, text='Clear location DICT', padx=10, pady=10, fg='white', command=self.clear_dict, highlightbackground='#ff0000'))
		getattr(self, btn_name).grid(row=0, column=3, sticky=W)

	def add_finish_button(self, tab_obj, btn_name):
		"""Adds a finish button to save the current dictionary to a file."""
		setattr(self, btn_name, Button(tab_obj, text='Save to file', padx=10, pady=10, fg='white', command=self.save, highlightbackground='#808080'))
		getattr(self, btn_name).grid(row=1, column=3, sticky=W)

	def setup(self, tab_obj, dic, warn_var, title_var, entry_var, text):

		def entry_handler(event):

			setattr(self, dic, {})
			self.cur_itemID = getattr(self, entry_var).get()
			getattr(self, dic)[self.cur_itemID] = {}
			print(getattr(self, dic))
			print('cur_itemID:', self.cur_itemID)
			press('tab')

		self.cur_DICT = dic

		setattr(self, warn_var, Label(tab_obj, text='DO THIS FIRST! --->', padx=5, font='Helvetica 13 bold',
									bg='#EC5463', fg='white'))
		getattr(self, warn_var).grid(row=self.row_counter, column=0, padx=5, pady=5, sticky=E)

		setattr(self, title_var, Label(tab_obj, text=text, anchor='w', padx=5))
		getattr(self, title_var).grid(row=self.row_counter, column=1, padx=5, pady=5, sticky=W + E + N + S)

		setattr(self, entry_var, Entry(tab_obj))
		getattr(self, entry_var).grid(row=self.row_counter, column=2, padx=5, pady=5, sticky=W + E + N + S)
		getattr(self, entry_var).bind("<Return>", entry_handler)

		self.row_counter += 3

		ttk.Separator(tab_obj, orient=HORIZONTAL).grid(row=self.row_counter, sticky=NSEW, rowspan=1, columnspan=3)
		self.row_counter += 1

	def clear_dict(self):
		"""Clears the current dictionary."""
		result = tkinter.messagebox.askyesnocancel('Delete dictionary', 'You sure you want to delete?')
		if result:
			dictionary = getattr(self, self.cur_DICT)
			dictionary[self.cur_itemID] = {}
			print(dictionary)

	def save(self):
		filename = '/Users/Sam/Documents/Shalhevet/CompSci/CompSci Work/Capstone/Github/AdventureX/Framework/Location Data.yaml'
		# with open(filename) as infile:
		# 	dictionary = yaml.load(infile)
		with open(filename, 'a') as outfile:
			# dictionary[self.cur_DICT][self.cur_itemID] = getattr(self, self.cur_DICT)
			print(getattr(self, self.cur_DICT))
			# ruamel.yaml.dump(getattr(self, self.cur_DICT), outfile, default_flow_style=False)
			dictionary = getattr(self, self.cur_DICT)
			yaml.dump({self.cur_itemID: OrderedDict(dictionary[self.cur_itemID])}, outfile, Dumper=yamlordereddictloader.Dumper, default_flow_style=None)

	def create_location_stuff(self):
		"""Creates location stuff."""

		# self.add_entry(self.locTab, var_name='LocNum', label_text='Location Number:')
		# Add the location number entry box. This is not done using the add_entry method because it is needed to be done
		# before everything to set up the location dictionary with locNum as the key.

		self.setup(self.locTab, 'LOCATIONS', 'LocNumWarning', 'LocNumTitle', 'LocNumEntry', 'Location Number --->')

		loc_entries = [('name', 'NAME:'), ('loc_references', 'REFERENCES: (split by comma)'), ('can_enter', 'CAN ENTER: (split cond_set items by commas)')]
		for var_name, text in loc_entries:
			self.add_entry(self.locTab, var_name=var_name, label_text=text, column=0)
			print('row:', self.row_counter, var_name)

		self.add_button(self.locTab, 'add_enter_cond', entry_var='can_enter', text='Add enter condition', row=self.row_counter-1, column=2)
		print('rowp:', self.row_counter)

		ttk.Separator(self.locTab, orient=HORIZONTAL).grid(row=self.row_counter, sticky=NSEW, rowspan=1, columnspan=4)

		self.add_label(self.locTab, var_name='narratives_label', text='NARRATIVES', column=0, header=(True, True), bg='#F9CE5F')

		self.add_entry(self.locTab, var_name='long_nar', label_text='LONG:', column=0, header=True)
		self.add_checkboxes(self.locTab, 'long_exception_chkBox', 'Long Exceptions', column=0)
		self.add_entry(self.locTab, var_name='short_nar', label_text='SHORT:', column=0, header=True)
		self.add_checkboxes(self.locTab, 'short_nar_exception_chkBox', 'Short Exceptions', column=0)

		self.row_counter = 8

		self.add_label(self.locTab, 'moves', 'MOVES', column=2, two_rows=False, header=(True, True), bg='#F9CE5F')
		print('under moves line:', self.row_counter)

		move_entries = [('N', 'North takes player to:'), ('E', 'East takes player to:'), ('S', 'South takes player to:'), ('W', 'West takes player to:')]
		for var_name, text in move_entries:
			self.add_entry(self.locTab, var_name=var_name, label_text=text, column=2)

		self.add_entry(self.locTab, 'objects', 'OBJECTS', column=2, header=True)
		print('under objects line:', self.row_counter)
		self.row_counter += 1
		self.add_entry(self.locTab, var_name='auto_changes', label_text='Automatic changes upon arrival: (split item_attribute_set by commas)', column=2)

		self.add_clear_button(self.locTab, 'locClearBtn')
		self.add_finish_button(self.locTab, 'locFinishBtn')

	def create_object_stuff(self, event):
		"""Creates the object stuff."""

		self.objTab.unbind("<Visibility>")
		self.row_counter = 0
		self.setup(self.objTab, 'OBJECTS', 'ObjNameWarning', 'ObjNameTitle', 'ObjNameEntry', 'Object Name --->')

		def choice_handler():
			typ = typ_choice.get()
			print('object type:', typ)

		typ_choice = StringVar(self.objTab)
		typ_choice.set('Object TYPE')

		typ_menu = OptionMenu(self.objTab, typ_choice, 'SIMPLE', 'COMPLEX', 'CONTAINER', command=choice_handler)
		typ_menu.grid(row=self.row_counter, column=0, padx=5, pady=5, sticky=W)  # positioning.

		obj_entries = [('references', 'REFERENCES: (split by comma)'), ('description', 'DESCRIPTION:'), ('weight', 'WEIGHT:'),
						('damage', 'DAMAGE:'), ('active_location', 'LOCATION:')]
		for var_name, text in obj_entries:
			self.add_entry(self.objTab, var_name=var_name, label_text=text, column=0)

		ttk.Separator(self.objTab, orient=HORIZONTAL).grid(row=self.row_counter, sticky=NSEW, rowspan=1, columnspan=4)

		self.add_clear_button(self.objTab, 'objClearBtn')
		self.add_finish_button(self.objTab, 'objFinishBtn')


display = Display()





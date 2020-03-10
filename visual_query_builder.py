import ast
import csv
import os
import db
import pymongo
import tkinter as tk
import tkinter.font as tkfont
from pprint import pformat
from bson.json_util import dumps
from context_menu import rightClick
from warning_widgets import allWarnings
from tkinter import ttk, messagebox, filedialog
from placeholders import PlaceholderEntry, PlaceholderCombobox

# Menu bar 
class menuBar(tk.Menu):
	def __init__(self, controller, *args, **kwargs):
		super().__init__(controller, *args, **kwargs, tearoff=False)
		self.controller = controller

		def show_popup_window():
			self.w=customLimitWindow(self.controller)

		def show_about_window():
			self.w=aboutWindow(self.controller)

		# Main menu bar
		menu_bar = tk.Menu(self, tearoff=0)
		menu_bar.add_command(label='Exit', command=quit)
		# Options menu
		options_menu = tk.Menu(menu_bar, tearoff=0)
		options_menu_limit_results = tk.Menu(options_menu)
		options_menu_cxn_timeout = tk.Menu(options_menu)
		self.options_menu_limit_results_var = tk.StringVar()
		self.options_menu_limit_results_var.set('No limit')
		self.options_menu_cxn_timeout_var = tk.StringVar()
		self.options_menu_cxn_timeout_var.set(3000)
		# Creating limit results menu of options menu
		for item in (10, 50, 100, 500, 'Custom', 'No limit'):
			if item == 'Custom':
				options_menu_limit_results.add_radiobutton(label=item, variable=self.options_menu_limit_results_var, command=show_popup_window)
			else:
				options_menu_limit_results.add_radiobutton(label=item, variable=self.options_menu_limit_results_var)
		# Creating connection timeout menu of options menu
		for item in (3000, 10000, 30000):
			options_menu_cxn_timeout.add_radiobutton(label=item, variable=self.options_menu_cxn_timeout_var)
		# Help menu
		help_menu = tk.Menu(menu_bar, tearoff=0)
		help_menu.add_command(label='About', command=show_about_window)
		help_menu.add_command(label='Show query string', command=self.controller.main_query_frame.show_query_str_popup)
		# Adding cascades
		self.add_cascade(label='File', menu=menu_bar)
		self.add_cascade(label='Options', menu=options_menu)
		self.add_cascade(label='Help', menu=help_menu)
		options_menu.add_cascade(label='Set results limit:', menu=options_menu_limit_results)
		options_menu.add_cascade(label='Set connection timeout (ms.):', menu=options_menu_cxn_timeout)

# Popup about window
class aboutWindow():
	def __init__(self, controller, *args, **kwargs):
		self.controller = controller
		self.top = tk.Toplevel(controller)
		self.top.wm_title('About')
		text_box = tk.Text(self.top, wrap='word')
		text_box.grid()
		dirname = os.path.dirname(__file__)
		help_file_path = os.path.join(dirname, 'help.txt')
		with open(help_file_path, 'r') as f:
			text_box.insert(tk.END, f.read())
		text_box['state'] = 'disabled'

# Popup window for setting up custom results limit
class customLimitWindow():
	def __init__(self, controller, *args, **kwargs):
		self.controller = controller
		x = self.controller.winfo_rootx()
		y = self.controller.winfo_rooty()
		self.top = tk.Toplevel(controller)
		self.top.geometry("+%d+%d" % (x + 50, y))
		self.label = tk.Label(self.top, text='Enter custom limit:')
		self.label.grid()
		self.entry = tk.Entry(self.top)
		self.entry.grid()
		self.set_limit_button = tk.Button(self.top, text='Set limit', command=self.cleanup)
		self.set_limit_button.grid()

	def cleanup(self):
		self.controller.menu_bar.options_menu_limit_results_var.set(self.entry.get())
		self.top.destroy()

class mainQueryFrame(tk.Frame):
	def __init__(self, controller, *args, **kwargs):
		super().__init__(controller, *args, **kwargs)
		self.controller = controller
		self.query_stucture_current_row = 0	# Responsible for correct query line placement in the visual query structure
		self.raw_main_query = {}	# Empty dictionary of structured raw main query of tkinter objects
		self.inner_label_frame_list = []	# Empty list of all inner label frames
		self.inner_label_frame_menu_button_list = []	# Empty list of all menu buttons of all inner label frames
		self.show_warning_state = False # Setting up show warning state to False (used in detecting empty fields in query structure)
		self.rclick = rightClick(self.controller)
		self.my_warnings = allWarnings()
		self.create_widgets()

	def create_widgets(self):
		# Left side frame
		self.left_side_frame = tk.Frame(self)
		self.left_side_frame.grid(row=0, column=0, sticky='ne')
		# Connection type
		self.connection_type_combobox = ttk.Combobox(self.left_side_frame, width=12, values=['URI', 'Local (no auth)'])
		self.connection_type_combobox.grid(row=1, column=0, padx=5)
		self.connection_type_combobox.bind('<<ComboboxSelected>>', self.connection_type_callback, add='+')
		self.connection_type_label = tk.Label(self.left_side_frame, text='Connection type:')
		self.connection_type_label.grid(row=0, column=0)
		# URI connection
		self.uri_connection_entry = PlaceholderEntry(self.left_side_frame, 'Enter URI string', width=14)
		self.uri_connection_entry.bind('<Button-3>', self.rclick.popup)
		# Local connection
		self.local_connection_username_label = tk.Label(self.left_side_frame, text='Username:')
		self.username_str_var = tk.StringVar()
		self.local_connection_username_entry = tk.Entry(self.left_side_frame, textvariable=self.username_str_var)
		# Databases
		self.databases_label = tk.Label(self.left_side_frame, text='Databases:')
		self.databases_label.grid(row=1, column=1, padx=10)
		self.databases_combobox = ttk.Combobox(self.left_side_frame, width=14)
		self.databases_combobox.grid(row=1, column=2)
		self.databases_combobox.bind('<<ComboboxSelected>>', self.update_collections_list)
		# Collections
		self.collections_label = tk.Label(self.left_side_frame, text='Collections:')
		self.collections_label.grid(row=2, column=1, padx=10)
		self.collections_combobox = ttk.Combobox(self.left_side_frame, width=14)
		self.collections_combobox.grid(row=2, column=2)
		# Query results box
		self.box_frame = tk.Frame(self.left_side_frame)
		self.box_frame.grid(row=5, column=0, rowspan=1, columnspan=4, padx=5, pady=5)
		self.canvas = tk.Canvas(self.box_frame, borderwidth=0, background="#ffffff", height=215, width=450)
		self.frame_for_canvas = tk.Frame(self.canvas, background="#ffffff")
		self.scrollbar = tk.Scrollbar(self.box_frame, orient="horizontal", command=self.canvas.xview)
		self.canvas.configure(xscrollcommand=self.scrollbar.set)
		self.scrollbar.pack(side="bottom", fill="x")
		self.canvas.pack(side="top", fill="both", expand=True)
		self.canvas.create_window((0,0), window=self.frame_for_canvas, anchor="nw")
		self.frame_for_canvas.bind("<Configure>", lambda event, canvas=self.canvas: self.on_frame_configure(self.canvas))
		self.create_query_results_box((110, 340))
		# Export results
		self.export_to_str_var = tk.StringVar(self.left_side_frame)
		self.export_to_str_var.set('Export to...')
		self.export_to_options = tk.OptionMenu(self.left_side_frame, self.export_to_str_var, 'Export to JSON', 'Export to CSV')
		self.export_to_options.grid(row=6, column=3, sticky='e')
		self.export_to_options.bind("<Configure>", self.export_to)
		# Query results count
		self.results_num = tk.StringVar()
		self.results_num.set('Results count: 0')
		self.query_results_count_number_label = tk.Label(self.left_side_frame, fg='gray40', textvariable=self.results_num)
		self.query_results_count_number_label.grid(row=6, column=0, columnspan=3, sticky='nw')
		# Separators
		self.sep_1 = ttk.Separator(self, orient=tk.VERTICAL)
		self.sep_1.grid(row=0, column=1, rowspan=5, padx=5, pady=5, sticky='ns')
		# Left side frame buttons
		self.connection_button = tk.Button(
			self.left_side_frame,
			text='Connect',
			command=lambda: [
				self.create_connection(self.selected_connection_type_option),
				self.get_databases_and_collections()
			]
		)
		self.show_all_button = tk.Button(
			self.left_side_frame,
			text='Show all',
			command=lambda: [
				self.results_finder(
					query=None,
					results_limit=self.controller.menu_bar.options_menu_limit_results_var.get()
				)
			]
		)
		self.show_all_button.grid(row=2, column=3)
		self.show_all_button['state'] = 'disabled'
		# Right side frame
		self.right_side_frame = tk.Frame(self)
		self.right_side_frame.grid(row=0, column=2, padx=4, sticky='ne')
		# Header frame of right side frame
		self.header_frame = tk.Frame(self.right_side_frame)
		self.header_frame.grid(row=0, column=0)
		# Body frame of right side frame
		self.body_frame = tk.Frame(self.right_side_frame)
		self.body_frame.grid(row=1, column=0)
		# Footer frame of right side frame
		self.footer_frame = tk.Frame(self.right_side_frame)
		self.footer_frame.grid(row=2, column=0)
		# Lower footer frame of right side frame
		self.lower_footer_frame = tk.Frame(self.right_side_frame)
		self.lower_footer_frame.grid(row=3, column=0)
		# Label of query structure
		self.query_structure_label = tk.Label(self.header_frame, text='Query structure:')
		self.query_structure_label.grid(row=0, column=0)
		# A menu button (+) for inserting new query block
		self.outer_menu_button = tk.Menubutton(self.body_frame, text='+', relief='raised')
		self.outer_menu_button.grid(row=1, column=0, sticky='ne')
		self.outer_menu_button.menu = tk.Menu(self.outer_menu_button, tearoff=0)
		self.outer_menu_button['menu'] = self.outer_menu_button.menu
		self.outer_menu_button.menu.add_command(label='New block', command=self.insert_inner_label_frame)
		# Outer logival operator
		self.outer_logical_operator = ttk.Combobox(self.body_frame, values=['$and', '$or', '$nor'], width=4)
		self.outer_logical_operator.set('$and')
		self.outer_logical_operator.bind('<FocusIn>', lambda event, var=self.outer_logical_operator: self.deselect(var))
		# Setting up raw main query as an empty list at the start
		self.raw_main_query[self.outer_logical_operator] = []
		# Outer label frame with implemented outer logical operator
		self.outer_label_frame = tk.LabelFrame(
			self.body_frame,
			labelwidget=self.outer_logical_operator,
			labelanchor='ne',
			bg='light grey',
			bd=2,
			padx=4,
			pady=4,
			relief='sunken'
		)
		self.outer_label_frame.grid(row=0, column=0, sticky='N')
		# Inserting inner label frame inside outer label frame
		self.insert_inner_label_frame()
		# Right side frame buttons
		self.execute_query_button = tk.Button(
			self.footer_frame,
			text='Execute query',
			command=lambda: [
				self.results_finder(
					query=self.generate_final_query(),
					results_limit=self.controller.menu_bar.options_menu_limit_results_var.get()
				)
			]
		)
		self.execute_query_button.pack()
		self.execute_query_button['state'] = 'disabled'
		self.query_str_button = tk.Button(self.footer_frame, text='Show query string', command=self.show_query_str_popup)	
		self.clear_all_button = tk.Button(self.footer_frame, text='Clear all', fg='red4', command=lambda:[self.clear_all()])
		self.clear_all_button.pack()
		# Binding all elements inside body frame to identify which inner menu button is pressed
		self.body_frame.bind_all("<Button-1>", lambda e: self.focus(e))
		# Styling up placeholders
		style = ttk.Style(self.body_frame)
		style.configure('Placeholder.TCombobox', foreground='#939795')
		style.configure('Placeholder.TEntry', foreground='#939795')
	
	# Callback function to grid and remove some fields by selected connection type option
	def connection_type_callback(self, event):
		self.selected_connection_type_option = self.connection_type_combobox.get()
		if self.selected_connection_type_option == 'URI':
			self.connection_button.grid_remove()
			self.uri_connection_entry.grid(row=2, column=0)
			self.connection_button.grid(row=3, column=0)
		else:
			self.uri_connection_entry.grid_remove()
			self.connection_button.grid_remove()
			self.connection_button.grid(row=2, column=0)

	# Exports results to chosen option
	def export_to(self, event):
		self.selected_export_option = self.export_to_str_var.get()
		if self.selected_export_option == 'Export to JSON':
			file_name = tk.filedialog.asksaveasfilename(initialdir='/', title="Save As", filetypes=(('json files', '*.json'), ('all files', '*.*')))
			self.export_to_str_var.set('Export to...')
			if file_name:
				f = open(file_name, 'w')
				f.write(dumps(self.results.rewind(), indent=4))
				f.close()
		elif self.selected_export_option == 'Export to CSV':
			file_name = tk.filedialog.asksaveasfilename(initialdir='/', title='Save As', filetypes=(('csv files', '*.csv'), ('all files', '*.*')))
			self.export_to_str_var.set('Export to...')
			if file_name:
				f = open(file_name, 'w')
				fields = []
				for item in self.results.rewind():
					for y in item.keys():
						fields.append(y)
				fields = list(set(fields))
				writer = csv.DictWriter(f, fieldnames=fields)
				writer.writeheader()
				for document in self.results.rewind():
					writer.writerow(document)
				f.close()

	# Set 'Show all' and 'Execute query' buttons enabled/disabled
	def set_buttons_state(self, state):
		if state:
			self.show_all_button['state'] = 'normal'
			self.execute_query_button['state'] = 'normal'
		else:
			self.show_all_button['state'] = 'disabled'
			self.execute_query_button['state'] = 'disabled'

	# Create URI/local connection by selected connection type
	def create_connection(self, connection_type):
		timeout = self.controller.menu_bar.options_menu_cxn_timeout_var.get()
		if connection_type == 'URI':
			uri = self.uri_connection_entry.get()
			connection = db.Connect.get_connection(URI=uri, timeout=timeout)
		else:
			connection = db.Connect.get_connection(timeout=timeout)
		self.connection = connection
		try:
			self.connection.server_info()
			self.connection_status = True
		except pymongo.errors.ServerSelectionTimeoutError:
			self.connection_status = False
			self.set_buttons_state(False)
			self.my_warnings.cnx_timeout_warning()

	# Get and set a lists of databases and collections after connection
	def get_databases_and_collections(self):
		if self.connection_status:
			self.databases_values = db.Explore.get_databases(self.connection)
			self.collections_values = db.Explore.get_collections(self.connection, self.databases_values[0])
			self.databases_combobox.set(self.databases_values[0])
			self.selected_database = self.databases_combobox.get()
			self.collections_combobox.set(self.collections_values[0])
			self.databases_combobox['values'] = self.databases_values
			self.collections_combobox['values'] = self.collections_values
			self.set_buttons_state(True)

	# Update collections list by selected database
	def update_collections_list(self, event):
		self.selected_database = self.databases_combobox.get()
		self.collections_values = db.Explore.get_collections(self.connection, self.selected_database)
		self.collections_combobox['values'] = self.collections_values
		self.set_buttons_state(True)
		try:
			self.collections_combobox.set(self.collections_values[0])
		except IndexError:
			self.set_buttons_state(False)
			self.collections_combobox.set('')
			self.my_warnings.no_collections_warning()

	# Measure key and value widths by iterating every single result of all results
	def measure_text_width(self, results):
		val_width = 340
		key_width = 110
		for single_result in results:
			for key, val in single_result.items():
				default_font = tkfont.nametofont('TkDefaultFont')
				key_width_measurement = default_font.measure(key)
				val_width_measurement = default_font.measure(val) + 10
				if key_width_measurement > key_width:
					key_width = key_width_measurement
				if val_width_measurement > val_width:
					val_width = val_width_measurement
		return key_width, val_width

	def insert_results_to_query_results_box(self):
		measured_widths = self.measure_text_width(self.results)
		self.query_results_box.destroy()
		self.create_query_results_box(measured_widths)
		# Placing every result into query results box
		for single_result in self.results.rewind():
			doc_id = str(single_result['_id'])
			# Visually shorting doc_id
			if len(doc_id) > 10:
				doc_id = '...' + doc_id[-10:]
			# Inserting shortened (or not) query box row name
			query_box_row_name = self.query_results_box.insert('', 0, text=doc_id)
			# Extracting key and value of a single result and placing into query box row
			for key, val in single_result.items():
				self.query_results_box.insert(query_box_row_name, 'end', text=key, values=([val]))

	def set_results_num(self, results_limit, results_counter):
		if results_limit != 'No limit':
			if results_counter > int(results_limit):
				results_str = f'Results count: {results_counter} (limited to {results_limit})'
				self.results_num.set(results_str)
			else:
				results_str = f'Results count: {results_counter}'
				self.results_num.set(results_str)
		else:
			results_str = f'Results count: {results_counter}'
			self.results_num.set(results_str)

	# Finds all results, places it into query results box, shows results count
	def results_finder(self, query, results_limit=None):
		self.selected_collection = self.collections_combobox.get()
		database = self.connection[self.selected_database]
		collection = database[self.selected_collection]
		# Creating document index if $search (a.k.a. $text) selector exists in query string
		try:
			if '$search' in str(self.generated_final_query):
				collection.drop_indexes()
				collection.create_index([(self.provided_key_000_value, 'text')])
		except AttributeError:
			pass
		# Finding all results using query (or not), results limit (or not)
		try:
			if query:
				if results_limit != 'No limit':
					self.results = collection.find(query, limit=int(results_limit))
				else:
					self.results = collection.find(query)
				results_counter = collection.count_documents(query)
			else:
				if results_limit != 'No limit':
					self.results = collection.find(limit=int(results_limit))
				else:
					self.results = collection.find()
				results_counter = collection.count_documents({})
		except pymongo.errors.PyMongoError as error:
			self.my_warnings.custom_warning(error.details['errmsg'])

		if self.show_warning_state:
			self.my_warnings.empty_field_warning()
			self.show_warning_state = False

		# Inserting results into query results box
		self.insert_results_to_query_results_box()
		# Setting up counted results number string under results box
		self.set_results_num(results_limit, results_counter)

	# Creates query results box
	def create_query_results_box(self, measured_widths):
		key_width, val_width = measured_widths
		self.query_results_box = ttk.Treeview(self.frame_for_canvas)
		self.query_results_box['columns']=('one')
		self.query_results_box.heading('#0', text=' key', anchor='w')
		self.query_results_box.heading('one', text=' value', anchor='w')
		self.query_results_box.column("#0", width=key_width, minwidth=110, stretch=True)
		self.query_results_box.column("one", width=val_width, minwidth=100, stretch=True)
		self.query_results_box.pack()

	# Configures canvas (required for implementing scrollbar)
	def on_frame_configure(self, canvas):
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	# Validates entries by checking every entry
	def validate_entries(self, key_entry, operator_entry, value_entry):
		if key_entry in ['Document key', ''] or operator_entry in ['Operator', ''] or value_entry in ['Value', '']:
			self.show_warning_state = True

	# Determine type of given val and then convert to proper type
	def determine_type(self, val):
		try:
			type_result = int(val)
		except ValueError:
			try:
				type_result = float(val)
			except ValueError:
				try:
					if val[0] == '[' and val[-1] == ']':
						type_result = ast.literal_eval(val)
					else:
						try:
							type_result = ast.literal_eval(val)
						except (ValueError, SyntaxError):
							type_result = val
				except (ValueError, IndexError):
					type_result = val
		if 'datetime' in val:
			type_result = eval(val)
		return type_result

	# Generate final query by iterating over every object of the self.raw_main_query
	def generate_final_query(self):
	    self.generated_final_query = {}
	    for key_0, val_0 in self.raw_main_query.items():
	        mid_query_list = []
	        for value_0 in val_0:
	            low_query_list = []
	            for key_00, val_00 in value_0.items():
	                mid_query_dict = {key_00.get(): low_query_list}
	                mid_query_list.append(mid_query_dict)
	                for value_00 in val_00:
	                    for key_000, val_000 in value_00.items():
	                        key_000_value = key_000.get()
	                        for key_0000, val_0000 in val_000.items():
	                        	# If key_0000.get() equals to '$search' selector then it creates self.provided_key_000_value which will be required for creating document index
	                        	if key_0000.get() == '$search':
	                        		self.provided_key_000_value = key_000.get()
	                        		key_000_value = '$text'
	                       		key_0000_value = key_0000.get()
	                       		val_0000_value = val_0000.get()
	                       		val_0000_value = self.determine_type(val_0000_value)
	                       		low_query_dict = {key_000_value: {key_0000_value: val_0000_value}}
	                       		low_query_list.append(low_query_dict)
	                       		self.validate_entries(key_000_value, key_0000_value, val_0000_value)
	    self.generated_final_query[key_0.get()] = mid_query_list
	    return self.generated_final_query

	# Insert query line (row) into visual query structure and into raw_main_query
	def insert_query_line(self, inner_label_frame):
		self.single_line_query = {}
		self.query_selectors_dict = {
			'$eq - Equal to': '$eq',
			'$gt - Greater than': '$gt',
			'$gte - Greater than or equal': '$gte',
			'$in - Matches any in array': '$in',
			'$lt - Less than': '$lt',
			'$lte - Less than or equal': '$lte',
			'$ne - Not equal': '$ne',
			'$nin - Matches to none in array': '$nin',
			'$exists - Matches specified field': '$exists',
			'$type - Selects specified type': '$type',
			'$mod - Modulo operation': '$mod',
			'$regex - Regex search': '$regex',
			'$search - Text search': '$search',
			'$all - Matches arrays by elems.': '$all',
			'$size - Matches arrays by size': '$size'
		}
		self.query_selectors_keys = [key for key in self.query_selectors_dict.keys()]

		# Select the proper value of drop-down dict
		def onSelect(event):
		    operator_entry.set((self.query_selectors_dict[operator_entry.get()]))

		# Configure operator combobox drop-down width
		def combo_configure(event):
		    combo = event.widget
		    style = ttk.Style()
		    length = max(combo.cget('values'), key=len)
		    font = tkfont.nametofont(str(combo.cget('font')))
		    width = max(0, font.measure(length.strip() + '0') - combo.winfo_width()) + 12
		    style.configure('TCombobox', postoffset=(0, 0, width, 0))
		
		# Key entry (a.k.a. 'Document key')
		key_entry = PlaceholderEntry(inner_label_frame, 'Document key')
		key_entry.grid(row=self.query_stucture_current_row, column=0)
		# Operator entry
		operator_entry = PlaceholderCombobox(inner_label_frame, 'Operator', values=self.query_selectors_keys)
		operator_entry.bind('<<ComboboxSelected>>', onSelect)
		operator_entry.bind('<ButtonPress>', combo_configure)
		operator_entry.grid(row=self.query_stucture_current_row, column=1)
		# Value entry
		val_entry = PlaceholderEntry(inner_label_frame, 'Value')
		val_entry.grid(row=self.query_stucture_current_row, column=2)
		# Incrementing query_structure_row by 1 to be able to place next query line correctly in the visual query structure
		self.query_stucture_current_row += 1
		# Constructing single line query
		self.single_line_query[key_entry] = {operator_entry: val_entry}
		# Inserting constructed single line query into raw main query
		for key, val in self.raw_main_query[self.outer_logical_operator][self.active_menu_button].items():
		    self.raw_main_query[self.outer_logical_operator][self.active_menu_button][key].append(self.single_line_query)

	# Remove query line from visual query structure and from raw main query
	def remove_query_line(self):
		for key in self.raw_main_query[self.outer_logical_operator][self.active_menu_button].keys():
			last_query_line = self.raw_main_query[self.outer_logical_operator][self.active_menu_button][key][-1]
			# Checks if the removable query line is the last one in the visual query structure
			if len(self.inner_label_frame_list) == 1 and len(self.raw_main_query[self.outer_logical_operator][self.active_menu_button][key]) == 1:
				# Extracting key and value of the last_query_line and deleting key (a.k.a. 'Document key')
				for last_query_line_key, last_query_line_val in last_query_line.items():
					last_query_line_key.delete(0, 'end')
					last_query_line_key.focus_set()
				# Extracting key and value of previous extracted last_query_line_val and deleting it
				for last_query_line_val_key, last_query_line_val_val in last_query_line_val.items():
					last_query_line_val_key.set('')
					last_query_line_val_val.delete(0, 'end')
					self.outer_logical_operator.set('$and')
					key.set('$and')
					last_query_line_val_key.focus_set()
					last_query_line_val_val.focus_set()
					self.body_frame.focus_set()
			else:
				# Extracting key and value of the last_query_line and destroying it
				for last_query_line_key, last_query_line_val in last_query_line.items():
					last_query_line_key.destroy()
				self.raw_main_query[self.outer_logical_operator][self.active_menu_button][key].pop()
				# Checks if query line is the last line in the inner label frame
				if len(self.raw_main_query[self.outer_logical_operator][self.active_menu_button][key]) == 0:
					# Destroys active inner label frame
					self.inner_label_frame_list[self.active_menu_button].destroy()
					# Deletes outer logical operator from raw_main_query
					del self.raw_main_query[self.outer_logical_operator][self.active_menu_button]
					# Deletes active inner label frame from the inner_label_frame_list
					del self.inner_label_frame_list[self.active_menu_button]
					# Deletes active inner label frame menu button from the inner_label_frame_menu_button_list
					del self.inner_label_frame_menu_button_list[self.active_menu_button]
				# Extracting key and value of previous extracted last_query_line_val and destroying it
				for last_query_line_val_key, last_query_line_val_val in last_query_line_val.items():
					last_query_line_val_key.destroy()
					last_query_line_val_val.destroy()
	
	# Insert inner label frame into visual query structure
	def insert_inner_label_frame(self):
	    self.active_menu_button = len(self.inner_label_frame_list)
	    # Setting up inner_logical_operator
	    inner_logical_operator = ttk.Combobox(self.outer_label_frame, values=['$and', '$or', '$nor'], width=4)
	    inner_logical_operator.set('$and')
	    inner_logical_operator.bind('<FocusIn>', lambda event, var=inner_logical_operator: self.deselect(var))
	    # Appending inner_logical_operator to the raw_main_query
	    self.raw_main_query[self.outer_logical_operator].append({inner_logical_operator: []})
	    # Setting up inner_label_frame
	    inner_label_frame = tk.LabelFrame(self.outer_label_frame, labelwidget=inner_logical_operator, padx=4, pady=4, relief='raised', bg='gray90')
	    inner_label_frame.grid()
	    # Inserting new query line into inner label frame
	    self.insert_query_line(inner_label_frame)
	    # Setting up inner menu button (a.k.a. '+') inside inner label frame
	    self.inner_menu_button = tk.Menubutton(inner_label_frame, text='+', relief='raised')
	    self.inner_menu_button.grid(row=100, column=2, sticky='e')
	    self.inner_menu_button.menu = tk.Menu(self.inner_menu_button, tearoff=0)
	    self.inner_menu_button['menu'] = self.inner_menu_button.menu
	    self.inner_menu_button.menu.add_command(label='New query line', command=lambda: [self.insert_query_line(inner_label_frame)])
	    self.inner_menu_button.menu.add_command(label='Remove query line', command=self.remove_query_line)
	    # Appending recently created inner label frame to it's list
	    self.inner_label_frame_list.append(inner_label_frame)
	    # Appending recently created inner label frame menu button to it's list
	    self.inner_label_frame_menu_button_list.append(self.inner_menu_button.menu)

	# Deselecting selected widget
	def deselect(self, var):
		var.selection_clear()

	# Identify where the current focus is and if it is at one of inner label frame menu buttons list - set active_menu_button to it's place number
	def focus(self, event):
		try:
			widget = self.body_frame.focus_get()
			if widget in self.inner_label_frame_menu_button_list:
				for i, single_menu_button in enumerate(self.inner_label_frame_menu_button_list):
					if widget == single_menu_button:
						self.active_menu_button = i
		except KeyError:
			pass

	# Clear all query lines
	def clear_all(self):
		self.active_menu_buttons = len(self.inner_label_frame_list)
		for self.active_menu_button in range(self.active_menu_buttons)[::-1]:
			for key, val in self.raw_main_query[self.outer_logical_operator][self.active_menu_button].items():
				for _ in range(len(self.raw_main_query[self.outer_logical_operator][self.active_menu_button][key])):
					self.remove_query_line()

	# Show query string popup window
	def show_query_str_popup(self):
		win = tk.Toplevel()
		win.wm_title('Raw query string')
		text_box = tk.Text(win, height=10, width=120)
		text = pformat(self.generate_final_query(), indent=1, width=120)
		text_box.grid()
		text_box.insert(tk.END, text)
		text_box.bind('<Button-3>', self.rclick.popup)
		self.show_warning_state = False

class MainApplication(tk.Frame):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(controller, *args, **kwargs)
        self.main_query_frame = mainQueryFrame(self)
        self.menu_bar = menuBar(self)
        tk.Tk.config(controller, menu=self.menu_bar)
        self.main_query_frame.grid(row=0, column=0, sticky='n')

def main():
	root = tk.Tk()
	root.title('Basic MongoDB query tool')
	app = MainApplication(root)
	app.grid()
	app.mainloop()

if __name__ == '__main__':
	main()
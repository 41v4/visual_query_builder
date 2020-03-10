from tkinter import ttk, messagebox, filedialog

# Different warning messages (used for exceptions handling)
class allWarnings():
	def cnx_timeout_warning(self):
		messagebox.showwarning(title='Connection timeout warning!', message='Warning: connection timed out. You can change connection timeout settings in options menu.')

	def cnx_refused_warning(self):
		messagebox.showwarning(title='Connection refused warning!', message='Warning: connection refused. Make sure you filled correct credentials.')

	def no_collections_warning(self):
		messagebox.showwarning(title='No collections warning!', message='Warning: selected database has no collections.')

	def empty_field_warning(self):
		messagebox.showwarning(title='Empty field warning!', message='Warning: looks like some fields were left empty. Make sure no fields are left empty.')

	def custom_warning(self, error_message):
		messagebox.showwarning(title='Warning!', message=error_message)
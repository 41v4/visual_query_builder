import tkinter as tk

# Right click context menu (for copying and pasting)
class rightClick():
	def __init__(self, controller):
		self.controller = controller
		# Creating context menu
		self.context_menu = tk.Menu(controller, tearoff=0)
		self.context_menu.add_command(label='Copy', command=self.copy)
		self.context_menu.add_command(label='Paste', command=self.paste)
	# Copy command
	def copy(self):
		self.controller.event_generate('<Control-c>')
	# Paste command
	def paste(self):
		self.controller.event_generate('<Control-v>')
	# Popup command which makes context_menu to 'popup'. Used for binding right mouse click on desired frame or etc.
	def popup(self, event):
		self.context_menu.tk_popup(event.x_root, event.y_root)
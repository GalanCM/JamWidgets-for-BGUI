import bgui
from bge import logic, render, events

from collections import OrderedDict

from pydebug.osd import PyDebugWidget

class JamInfobar(bgui.Frame):
	""" Infobar for JamWidgets. Currently not designed for stand-alone use. """
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.set_appearance([0.01, 0.01, 0.01, 0.5])
		self.visible = False
		self.items = OrderedDict()
		self.frozen = True

	def text(self, text, id, font=None):
		""" Add text to the infobar

			Arguments:
			text -- the text to be displayed
			id -- a numerical id for infobar. Infobar items are sorted in order of id. To overwrite/update an item, reuse the id

			Keyword Arguments
			font -- currently not used
		"""
		if font:
			font = logic.expandPath("//"+font)
		text = text.replace('\n', '')
		self.items[id] = bgui.Label(self, id, text=text, font=font, pt_size=40, pos=[0, 0], options=bgui.BGUI_DEFAULT)
		self.items[id].frozen = True
		self.items[id].visible = True

	def image(self, img, id):
		""" Add image to the infobar

			Arguments:
			img -- image filename to use (do not use logic.expandPath())
			id -- a numerical id for infobar. Infobar items are sorted in order of id. To overwrite/update an item, reuse the id
		"""
		aspect = get_image_aspect(logic.expandPath("//"+img))
		self.items[id] = bgui.image.Image(self, id, logic.expandPath("//"+img), aspect=aspect, size=[0,0.9], 
										  pos=[0,0], options=bgui.BGUI_DEFAULT | bgui.BGUI_CENTERY)
		self.items[id].frozen = True
		self.items[id].visible = True

	def remove(self, id):
		self.children[id].visible = False

	def set_appearance(self, bg_color, border_color=None):
		""" Change the background and border colors of the infobar """
		self.colors = [bg_color for i in range(4)]
		if border_color:
			self.border_color = border_color
			self.border = 2
			self.size = [0.998,0.099]
			if self.position[1] < 0.1:
				y_pos = self.position[1]+0.001
			else:
				y_pos = self.position[1]-0.001
			self.position = [ self.position[0]+0.001, y_pos ]

	def update(self):
		""" Update the formatting of the infobar """
		self.items = OrderedDict(sorted(self.items.items(), key=lambda t: t[0]))
		x_pos = 0.01
		for id, widget in self.items.items():
			if widget.visible:
				y_pos = 0
				if hasattr(widget, "text"):
					y_pos = 0.35
				widget.position = [x_pos, y_pos]

				x_pos += widget.size[0]/render.getWindowWidth() + 0.015

		if len(self.items) > 0:
			self.visible = True
		else:
			self.visible = False

class JamDialog(bgui.Frame):
	""" Simple dialog window for JamWidgets. Currently not designed for stand-alone use. """
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.visible = False
		self.pages = []
		self.after = None
		self.next_key = events.ZKEY
		self.up_key = events.UPARROWKEY
		self.down_key = events.DOWNARROWKEY
		self.options = []

	def open(self, pages, after=None):
		""" Open the dialog with content in pages

			Arguments:
			pages -- a list of strings representing each page in the dialog

			Keyword arguments
			after -- a callback to execute after the last page of the dialog. If not defined, window will close.
		"""	
		self.visible = True
		self.pages = pages
		self.text = bgui.text_block.TextBlock(self, "text", text=pages[0], size=[0.95,0.9], pt_size=28, options=bgui.BGUI_DEFAULT)
		self.top_pos = self.position[1]+self.size[1]
		self.text.position = [0.025, 0.05]
		self.after = after
		self.results = []

	def _next_page(self):
		""" Flip to the next page """
		for opt in self.children:
			if opt.isdigit() or opt == "cursor":
				del self.children[opt]
			self.options = []
		if len(self.pages) > 1:
			self.pages.pop(0)
			if isinstance(self.pages[0], str):
				self.text.text = self.pages[0]
			else:
				self.text.text = self.pages[0][0]
				last_item = list(self.text.children.values())[-1]
				height = -( self.top_pos - last_item.position[1] - (last_item.size[1]*0.6) ) / self.size[1] # self.line_height + self.line_height*2.5
				option_num = 0
				for option_text in self.pages[0][1:]:
					new_opt = bgui.text_block.TextBlock(self, str(option_num), text=option_text, size=[0.8,0.9], pt_size=28, options=bgui.BGUI_DEFAULT)
					new_opt.position = [0.05, (height)]
					last_item = list(new_opt.children.values())[-1]
					height = -( self.top_pos - last_item.position[1] - (last_item.size[1]*0.6)  )/self.size[1]
					self.options += [new_opt]
					option_num += 1
				self.cursor = bgui.Label(self, "cursor", text="•", pt_size=28, options=bgui.BGUI_DEFAULT)
				self._set_cursor(0)

		elif self.after:
			self.pages.pop(0)
			self.after(self)
		else:
			self.close()

	def _set_cursor(self, dir):
		if not hasattr(self.cursor, "selection"):
			self.cursor.selection = 0
		self.cursor.selection += dir
		self.cursor.selection %= len(self.options)
		cursor_target = list(self.options[self.cursor.selection].children.values())[0]
		self.cursor.position = [0.03, (cursor_target.position[1]-self.position[1])/self.size[1]]

	def close(self):
		""" Close (hide) the dialog """
		self.visible=False

	def input_check(self):
		""" Check for key press and flip page. The key to flip pages if set as self.next_key """
		if self.visible:
			if logic.keyboard.events[self.up_key] == 1 and 'cursor' in self.children:
				self._set_cursor(-1)
			elif logic.keyboard.events[self.down_key] == 1 and 'cursor' in self.children:
				self._set_cursor(1)
			elif logic.keyboard.events[self.next_key] == 1:
				if 'cursor' in self.children:
					self.results += [self.cursor.selection]
				self._next_page()

	def set_appearance(self, bg_color, border_color=None):
		""" Change the background and border colors of the dialog """
		self.colors = [bg_color for i in range(4)]
		if border_color:
			self.border_color = border_color
			self.border = 2

class JamUI(bgui.System):
	""" A UI containing simple widgets for use in game jams.

		self.infobar_top, self.infobar_bottom -- infobars located at the top an bottom of the screen
		self.dialog_top, self.dialog_bottom -- JRPG style dailog windows located at the top an bottom of the screen
		self.log -- an onscreen python debug log
	"""
	def __init__(self):

		bgui.System.__init__(self, None)
		
		self.infobar_top = JamInfobar(self, 'infobar_top', pos=[0,0.9], size=[1,0.1], border=0)

		self.infobar_bottom = JamInfobar(self, 'infobar_bottom', pos=[0,0], size=[1,0.1], border=0)

		self.dialog_top = JamDialog(self, 'dialog_top', pos=[0.2,0.59], size=[0.7,0.3], border=0)

		self.dialog_bottom = JamDialog(self, 'dialog_bottom', pos=[0.1,0.11], size=[0.7,0.3], border=0)

		self.log = PyDebugWidget(self)

		# testing code
		def open_top_dialog(ui):
			def callback(self):
				nonlocal ui
				self.close()
				if self.results[0] == 0:
					ui.dialog_top.open( ["Lorem ipsum dolor sit amet, consectetur adipiscing elit.", "Phasellus et justo mi. Sed eu dictum metus.\n\n Praesent adipiscing ultrices nunc ac volutpat.", " Etiam bibendum ligula at sem facilisis, vitae aliquam dolor egestas. Phasellus dictum justo dui, in laoreet urna facilisis eu.", " Aliquam magna mi, eleifend in volutpat eu, elementum a turpis. In in nibh et ipsum commodo dapibus sed sed purus.", " Pellentesque vel erat nisi. Nullam faucibus pharetra elit eu viverra. Suspendisse tincidunt, nunc vitae eleifend blandit, enim magna congue lectus, quis ornare sapien magna sed elit. In eu nisl ullamcorper, porttitor mi at, faucibus eros. In tortor felis, facilisis a volutpat eget, dignissim eget nibh."] )
			return callback

		self.infobar_top.visible = True
		self.infobar_bottom.visible = True
		self.infobar_top.image('ss.png', 0)
		self.infobar_top.text('Health 1/1', 2, font="UbuntuMono-B.ttf")
		self.infobar_top.text('Health 2/1', 2, font="UbuntuMono-B.ttf") # replace text
		self.infobar_top.text("Mana 0/0", 1)
		self.infobar_top.remove(1)
		self.infobar_bottom.image('brasero.png', 0)
		self.infobar_bottom.text('brasero.png', 1)
		self.infobar_bottom.image('ss.png', 1) # replace text with image
		self.infobar_bottom.set_appearance([0,0,0.8,0.75], border_color=[1,1,1,1])
		self.dialog_bottom.set_appearance([0,0,0.8,0.8], border_color=[1,1,1,1])
		self.dialog_bottom.open( ["Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
								  "Phasellus et justo mi. Sed eu dictum metus.\n\n Praesent adipiscing ultrices nunc ac volutpat.",
								  "Etiam bibendum ligula at sem facilisis, vitae aliquam dolor egestas. Phasellus dictum justo dui, in laoreet urna facilisis eu.",
								  "Aliquam magna mi, eleifend in volutpat eu, elementum a turpis. In in nibh et ipsum commodo dapibus sed sed purus.",
								  ["Open top\n dialog", "Yes", "No\n -thanks", "No"],
								  "Pellentesque vel erat nisi. Nullam faucibus pharetra elit eu viverra. Suspendisse tincidunt, nunc vitae eleifend blandit, enim magna congue lectus, quis ornare sapien magna sed elit. In eu nisl ullamcorper, porttitor mi at, faucibus eros. In tortor felis, facilisis a volutpat eget, dignissim eget nibh."],
								open_top_dialog(self) )
		self.dialog_top.set_appearance([0.8,0,0,0.8], border_color=[1,1,1,1])

	def run(self):
		self.dialog_top.input_check()
		self.dialog_bottom.input_check()
		self.infobar_top.update()
		self.infobar_bottom.update()
		self.log.run()
		logic.getCurrentScene().post_draw = [self.render]

def init():
	logic.getCurrentScene()['JamUI'] = JamUI()

def run():
	logic.getCurrentScene()['JamUI'].run()

### borrowed from http://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib
import struct
import imghdr

def get_image_aspect(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    fhandle = open(fname, 'rb')
    head = fhandle.read(24)
    if len(head) != 24:
        return
    if imghdr.what(fname) == 'png':
        check = struct.unpack('>i', head[4:8])[0]
        if check != 0x0d0a1a0a:
            return
        width, height = struct.unpack('>ii', head[16:24])
    elif imghdr.what(fname) == 'gif':
        width, height = struct.unpack('<HH', head[6:10])
    elif imghdr.what(fname) == 'jpeg':
        try:
            fhandle.seek(0) # Read 0xff next
            size = 2
            ftype = 0
            while not 0xc0 <= ftype <= 0xcf:
                fhandle.seek(size, 1)
                byte = fhandle.read(1)
                while ord(byte) == 0xff:
                    byte = fhandle.read(1)
                ftype = ord(byte)
                size = struct.unpack('>H', fhandle.read(2))[0] - 2
            # We are at a SOFn block
            fhandle.seek(1, 1)  # Skip `precision' byte.
            height, width = struct.unpack('>HH', fhandle.read(4))
        except Exception: #IGNORE:W0703
            return
    else:
        return
    return width/height
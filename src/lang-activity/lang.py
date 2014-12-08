#  gcompris - lang.py
#
# Copyright (C) 2010 Bruno Coudoin
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# lang activity.
import gtk
import gtk.gdk
import gcompris
import gcompris.bonus
import gcompris.skin
import gcompris.sound
import goocanvas
import pango

from gcompris import gcompris_gettext as _
from langLib import *
from langFindit import *
from langEnterText import *

class Gcompris_lang:
  """Empty gcompris python class"""

  def __init__(self, gcomprisBoard):
    # These are used to let us restart only after the bonus is displayed.
    # When the bonus is displayed, it call us first with pause(1) and then with pause(0)
    self.board_paused  = 0;
    self.gamewon       = 0;

    # Save the gcomprisBoard, it defines everything we need
    # to know from the core
    self.gcomprisBoard = gcomprisBoard

    # Needed to get key_press
    gcomprisBoard.disable_im_context = False

  def start(self):
    self.saved_policy = gcompris.sound.policy_get()
    gcompris.sound.policy_set(gcompris.sound.PLAY_AND_INTERRUPT)
    gcompris.sound.pause()

    # init config to default values
    self.config_dict = self.init_config()

    # change configured values
    self.config_dict.update(gcompris.get_board_conf())

    if self.config_dict.has_key('locale_sound'):
      gcompris.set_locale(self.config_dict['locale_sound'])

    # Set the buttons we want in the bar
    handle = gcompris.utils.load_svg("lang/repeat.svg")
    gcompris.bar_set_repeat_icon(handle)
    gcompris.bar_set(gcompris.BAR_LEVEL|gcompris.BAR_REPEAT_ICON|gcompris.BAR_CONFIG)

    # Set a background image
    gcompris.set_background(self.gcomprisBoard.canvas.get_root_item(),
                            "lang/background.svgz")

    # Create our rootitem. We put each canvas item in it so at the end we
    # only have to kill it. The canvas deletes all the items it contains
    # automaticaly.
    self.rootitem = goocanvas.Group(parent =
                                    self.gcomprisBoard.canvas.get_root_item())

    self.langLib = LangLib(gcompris.DATA_DIR + "/lang/words.xml")
    self.chapters = self.langLib.getChapters()
    self.currentExercise = None
    self.currentExerciseModes = []

    if self.gcomprisBoard.mode == "":
      gcompris.utils.dialog("ERROR, missing 'mode' in the xml menu to specify the chapter",
                            None)
      return
    self.currentChapterName = self.gcomprisBoard.mode

    # Manage levels (a level is a lesson in the lang model)
    self.gcomprisBoard.level = 1
    try:
      self.gcomprisBoard.maxlevel = \
          len ( self.chapters.getChapters()[self.currentChapterName].getLessons() )
    except:
      gcompris.utils.dialog("ERROR, missing chapter '" + self.currentChapterName + "'",
                            None)
      return

    if self.gcomprisBoard.maxlevel == 0:
      gcompris.utils.dialog(_("ERROR, we found no words in this language.") + " " +
                            _("Please consider contributing a voice set."),
                            None)
      return

    if not (gcompris.get_properties().fx):
      gcompris.utils.dialog(_("Error: This activity cannot be \
played with the\nsound effects disabled.\nGo to the configuration \
dialogue to\nenable the sound."), None)

    gcompris.bar_set_level(self.gcomprisBoard)

    readyButton = TextButton(400, 255, ' ' * 20 + _('I am Ready') + ' ' * 20,
                             self.rootitem, 0x11AA11FFL)
    readyButton.getBackground().connect("button_press_event",
                                        self.ready_event, readyButton)

    self.pause(1);


  def ready_event(self, widget, target, event, button):
    button.destroy()
    self.currentLesson = self.langLib.getLesson(self.currentChapterName,
                                                self.gcomprisBoard.level - 1)
    self.displayLesson( self.currentLesson )
    self.displayImage( self.currentLesson.getTriplets()[self.currentTripletId] )
    self.pause(0);

  def end(self):
    gcompris.set_locale( "" )
    gcompris.sound.policy_set(self.saved_policy)
    gcompris.sound.resume()
    if self.currentExercise:
      self.currentExercise.stop()
    # Remove the root item removes all the others inside it
    self.rootitem.remove()


  def ok(self):
    pass


  def repeat(self):
    if self.currentExercise:
      self.currentExercise.repeat()
    else:
      try:
        self.playVoice( self.currentLesson.getTriplets()[self.currentTripletId] )
      except:
        pass

  def init_config(self):
    default_config = { 'locale_sound' : 'NULL' }
    return default_config

  #mandatory but unused yet
  def config_stop(self):
    pass

  # Configuration function.
  def config_start(self, profile):
    # keep profile in mind
    # profile can be Py_None
    self.configuring_profile = profile

    # init with default values
    self.config_dict = self.init_config()

    # get the configured values for that profile
    self.config_dict.update(gcompris.get_conf(profile, self.gcomprisBoard))

    bconf = gcompris.configuration_window ( \
      _('Configuration\n for profile <b>%s</b>')
      % ( (profile.name if profile else _("Default") ) ),
      self.ok_callback
      )

    gcompris.combo_locales_asset(bconf, _("Select locale"),
                                 self.config_dict['locale_sound'],
                                 "voices/$LOCALE/words/red.ogg")

  # Callback when the "OK" button is clicked in configuration window
  # this get all the _changed_ values
  def ok_callback(self, table):
    if (table == None):
      return True

    for key,value in table.iteritems():
      gcompris.set_board_conf(self.configuring_profile,
                              self.gcomprisBoard, key, value)

    return True;



  def key_press(self, keyval, commit_str, preedit_str):
    if self.currentExercise:
      return self.currentExercise.key_press(keyval, commit_str, preedit_str)

    if keyval == gtk.keysyms.Left or keyval == gtk.keysyms.Up:
      self.previous_event(keyval)
    elif commit_str == " " or \
          keyval == gtk.keysyms.Right or keyval == gtk.keysyms.Down:
      self.next_event(keyval)
    elif keyval == gtk.keysyms.End:
      self.startExercise()

  def pause(self, pause):
    self.board_paused = pause

    # When the bonus is displayed, it call us first
    # with pause(1) and then with pause(0)
    # the game is won
    if(self.gamewon == 1 and pause == 0):
      self.gamewon = 0
      if not self.runExercise():
        self.next_level()

    return



  def next_level(self):
    if self.currentExercise:
      self.currentExercise.stop()
      self.currentExercise = None

    if self.gcomprisBoard.level < self.gcomprisBoard.maxlevel:
      self.set_level(self.gcomprisBoard.level + 1)
    else:
      self.set_level(self.gcomprisBoard.level)

  def set_level(self, level):
    self.gcomprisBoard.level = level;
    self.gcomprisBoard.sublevel = 1;
    gcompris.bar_set_level(self.gcomprisBoard)

    # We are not yet started
    if self.board_paused:
      return

    if self.currentExercise:
      self.currentExercise.stop()
      self.currentExercise = None

    self.currentLesson = self.langLib.getLesson(self.currentChapterName,
                                                self.gcomprisBoard.level - 1)
    self.displayLesson( self.currentLesson )
    self.displayImage( self.currentLesson.getTriplets()[self.currentTripletId] )

# -------

  def clearLesson(self):
    self.lessonroot.remove()


  def displayLesson(self, lesson):

    # Keep the triplet shown to the user to know when
    # we can move to the exercices
    self.tripletSeen = set()

    try:
      self.lessonroot.remove()
    except:
      pass

    self.currentTripletId = 0
    self.lessonroot = goocanvas.Group( parent = self.rootitem )

    goocanvas.Rect(
      parent = self.lessonroot,
      x = 20,
      y = 10,
      width = gcompris.BOARD_WIDTH - 40,
      height = 65,
      fill_color_rgba = 0xAAAAAA99L,
      stroke_color_rgba = 0x111111AAL,
      line_width = 2.0,
      radius_x = 3,
      radius_y = 3)

    goocanvas.Text(
      parent = self.lessonroot,
      x = gcompris.BOARD_WIDTH / 2,
      y = 40.0,
      text = gcompris.gcompris_gettext(lesson.name),
      font = gcompris.skin.get_font("gcompris/title"),
      fill_color = "white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER,
      width = 300
      )

    # Previous Button
    item = goocanvas.Svg( parent = self.lessonroot,
                        svg_handle = gcompris.skin.svg_get(),
                        svg_id = "#PREVIOUS",
                        )
    gcompris.utils.item_absolute_move(item,
                                      100,
                                      gcompris.BOARD_HEIGHT / 2)
    item.connect("button_press_event", self.previous_event, None)
    gcompris.utils.item_focus_init(item, None)

    # Next Button
    item = goocanvas.Svg(parent = self.lessonroot,
                       svg_handle = gcompris.skin.svg_get(),
                       svg_id = "#NEXT",
                       )
    gcompris.utils.item_absolute_move(item,
                                      gcompris.BOARD_WIDTH - 130,
                                      gcompris.BOARD_HEIGHT / 2)
    item.connect("button_press_event", self.next_event, None)
    gcompris.utils.item_focus_init(item, None)

    self.counteritem = goocanvas.Text(
      parent = self.lessonroot,
      x = gcompris.BOARD_WIDTH - 40,
      y = gcompris.BOARD_HEIGHT - 40,
      font = gcompris.skin.get_font("gcompris/board/tiny"),
      fill_color = "white",
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER
      )

    # The triplet area
    w = 400
    h = 300
    goocanvas.Rect(
      parent = self.lessonroot,
      x = (gcompris.BOARD_WIDTH - w) / 2,
      y = (gcompris.BOARD_HEIGHT - h) / 2 - 20,
      width = w,
      height = h + 50,
      fill_color_rgba = 0xCECECEAAL,
      stroke_color_rgba = 0x111111CCL,
      line_width = 2.0,
      radius_x = 3,
      radius_y = 3)
    self.imageitem = goocanvas.Image( parent = self.lessonroot )
    self.imageitem.connect("button_press_event", self.next_event, None)

    goocanvas.Rect(
      parent = self.lessonroot,
      x = (gcompris.BOARD_WIDTH - w) / 2,
      y = (gcompris.BOARD_HEIGHT - h) / 2 - 10 + h,
      width = w,
      height = 40,
      fill_color_rgba = 0x999999BBL,
      stroke_color_rgba = 0x111111AAL,
      line_width = 2.0,
      radius_x = 3,
      radius_y = 3)


    self.descriptionitem = goocanvas.Text(
      parent = self.lessonroot,
      x = gcompris.BOARD_WIDTH / 2,
      y = gcompris.BOARD_HEIGHT - 100,
      fill_color = "white",
      font = gcompris.skin.get_font("gcompris/subtitle"),
      anchor = gtk.ANCHOR_CENTER,
      alignment = pango.ALIGN_CENTER,
      width = 500
      )

  def playVoice(self, triplet):
    if triplet.voice:
      gcompris.sound.play_ogg(triplet.voice)

  def runExercise(self):
    if len(self.currentExerciseModes):
      currentMode = self.currentExerciseModes.pop()
      if currentMode[0] == "findit":
        self.currentExercise = Findit(self, self.rootitem, self.currentLesson,
                                      currentMode[1])
      else:
        self.currentExercise = EnterText(self, self.rootitem, self.currentLesson,
                                         currentMode[1])
      self.currentExercise.start()
      return True
    return False

  def startExercise(self):
    self.clearLesson()
    # We will run the exercise 3 times in different modes
    self.currentExerciseModes = [ ["findit",Findit.WITH_QUESTION|Findit.WITH_TEXT|Findit.WITH_IMAGE],
                                  ["findit", Findit.WITH_TEXT|Findit.WITH_IMAGE],
                                  ["findit", Findit.WITH_IMAGE],
                                  ["text", EnterText.WITH_TEXT|EnterText.WITH_IMAGE]
                                  ]
    self.currentExerciseModes.reverse()
    self.runExercise()

  def displayImage(self, triplet):

    if len(self.tripletSeen) == len(self.currentLesson.getTriplets()):
      self.startExercise()
      return

    # Display the next triplet
    self.tripletSeen.add(triplet)
    self.playVoice( triplet )
    self.descriptionitem.set_properties (
      text = triplet.descriptionTranslated,
      )
    self.counteritem.set_properties (
      text = str(self.currentTripletId + 1) + "/" \
        + str( len( self.currentLesson.getTriplets() ) ),
      )
    self.imageitem.props.visibility = goocanvas.ITEM_VISIBLE
    pixbuf = gcompris.utils.load_pixmap(gcompris.DATA_DIR + "/" +
                                        triplet.image)
    center_x =  pixbuf.get_width()/2
    center_y =  pixbuf.get_height()/2
    self.imageitem.set_properties(pixbuf = pixbuf,
                                  x = gcompris.BOARD_WIDTH  / 2 - center_x,
                                  y = gcompris.BOARD_HEIGHT / 2 - center_y - 18)

  def previous_event(self, event=None, target=None, item=None, dummy=None):
    self.currentTripletId -= 1
    if self.currentTripletId < 0:
      self.currentTripletId = len( self.currentLesson.getTriplets() ) - 1
    self.displayImage( self.currentLesson.getTriplets()[self.currentTripletId] )

  def next_event(self, event=None, target=None, item=None, dummy=None):
    self.currentTripletId += 1
    if self.currentTripletId >= len( self.currentLesson.getTriplets() ):
      self.currentTripletId = 0
    self.displayImage( self.currentLesson.getTriplets()[self.currentTripletId] )

  def win(self):
    self.gamewon = 1
    gcompris.bonus.display(gcompris.bonus.WIN, gcompris.bonus.FLOWER)
    self.gcomprisBoard.sublevel += 1;

  def loose(self):
    self.gamewon = 0
    gcompris.bonus.display(gcompris.bonus.LOOSE, gcompris.bonus.FLOWER)



class TextButton:

    def __init__(self, x, y, text, rootitem, color_rgba=0x666666AAL):
        '''
        Add a text button to the screen with the following parameters:
        1. x: the x position of the button
        2. y: the y position of the button
        3. text: the text of the button
        4. rootitem: the item to draw the button in
        5. color: the color of button background

        TextButton(200, 300, 'Hello World!', self, color_rgba=0x6600FFFFL)
        '''
        width = -1
        self.rootitem = goocanvas.Group(parent=rootitem, x=0, y=0)
        textbox = goocanvas.Text(
            parent = self.rootitem,
            x=x, y=y,
            width=width,
            text=text,
            font = gcompris.skin.get_font("gcompris/board/small"),
            fill_color="white",
            anchor=gtk.ANCHOR_CENTER,
            alignment=pango.ALIGN_CENTER,
            pointer_events="GOO_CANVAS_EVENTS_NONE"
            )
        TG = 15
        bounds = textbox.get_bounds()

        self.back = goocanvas.Rect(parent = self.rootitem,
                       x = bounds.x1 - TG,
                       y = bounds.y1 - TG,
                       height = bounds.y2 - bounds.y1 + TG * 2,
                       width = bounds.x2 - bounds.x1 + TG * 2,
                       stroke_color = "black",
                       fill_color_rgba = color_rgba,
                       radius_x = 3, radius_y = 3,
                       line_width = 2.0)

        self.img = goocanvas.Image(
                parent = self.rootitem,
                x = bounds.x1 - TG,
                y = bounds.y1 - TG,
                height = bounds.y2 - bounds.y1 + TG * 2,
                width = bounds.x2 - bounds.x1 + TG * 2,
                pixbuf = gcompris.utils.load_pixmap('lang/button_front.svg')
                )

        gcompris.utils.item_focus_init(self.img, None)
        textbox.raise_(self.img)

    def getBackground(self):
        return self.img

    def destroy(self):
        return self.rootitem.remove()


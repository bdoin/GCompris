#  gcompris - langEnterText.py
#
# Copyright (C) 2013 Bruno Coudoin
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
# lang activity exercice.
import gtk
import gtk.gdk
import gcompris
import gcompris.utils
import gcompris.skin
import gcompris.sound
import goocanvas
import pango
import random

from gcompris import gcompris_gettext as _
from langLib import *

class TextEntry:
    """A GooCanvas only widget to enter text"""

    def __init__(self, rootitem, x, y, text, maxSize):
      self.x = x
      self.y = y
      self.text = text
      self.maxSize = maxSize
      self.insertCaret = None
      self.item = goocanvas.Text(
        parent = rootitem,
        x = x,
        y = y,
        fill_color = "white",
        font = gcompris.skin.get_font("gcompris/subtitle"),
        text = text,
        anchor = gtk.ANCHOR_CENTER,
        alignment = pango.ALIGN_CENTER,
        width = 300
        )

    def key_press(self, keyval, commit_str, preedit_str):

      if keyval == gtk.keysyms.BackSpace:
        self.text = self.text[:-1]
        self.item.set_properties(text = self.text,)
        return True

      if keyval != 0:
        return True

      if len(self.text) < self.maxSize:
        self.text = self.text + commit_str
      self.item.set_properties(text = self.text,)

      return True

    def getText(self):
        return self.text


class EnterText:
    """An exercice that given a word asks the children to type"""
    """it with the keyboard"""

    WITH_TEXT = 0x2
    WITH_IMAGE = 0x1

    def __init__(self, lang, parentitem, lesson, mode):
        self.lang = lang
        self.lesson = lesson
        self.mode = mode
        self.triplets = list(lesson.getTriplets())
        random.shuffle(self.triplets)
        self.rootitem = goocanvas.Group( parent = parentitem )
        self.gameroot = None
        self.currentIndex = 0
        self.tripletToFind = None

    def start(self):

        if self.currentIndex >= len(self.triplets):
          self.stop()
          self.lang.win()
          return

        self.gameroot = goocanvas.Group( parent = self.rootitem )

        self.tripletToFind = self.triplets[self.currentIndex]
        self.lang.playVoice(self.tripletToFind)
        self.currentIndex += 1
        # Display the triplet to find
        if self.mode & EnterText.WITH_IMAGE:
          pixbuf = gcompris.utils.load_pixmap(gcompris.DATA_DIR + "/" +
                                              self.tripletToFind.image)

          goocanvas.Rect(
              parent = self.gameroot,
              x = gcompris.BOARD_WIDTH / 2 - pixbuf.get_width() / 2,
              y = 10,
              width = pixbuf.get_width(),
              height = pixbuf.get_height() + 50,
              fill_color_rgba = 0xCECECECCL,
              stroke_color_rgba = 0x111111CCL,
              line_width = 2.0,
              radius_x = 3,
              radius_y = 3)
          item = goocanvas.Image( parent = self.gameroot,
                                  pixbuf = pixbuf,
                                  x = gcompris.BOARD_WIDTH / 2 - pixbuf.get_width() / 2,
                                  y = 60,
                                  )

        y = 380
        backItem = goocanvas.Rect(
          parent = self.gameroot,
          fill_color_rgba = 0x999999BBL,
          line_width = 0.0)

        textItem = goocanvas.Text(
          parent = self.gameroot,
          x = gcompris.BOARD_WIDTH / 2,
          y = y,
          fill_color = "white",
          font = gcompris.skin.get_font("gcompris/subtitle"),
          anchor = gtk.ANCHOR_CENTER,
          alignment = pango.ALIGN_CENTER,
          text = _("Enter the text you hear:")
          )
        bounds = textItem.get_bounds()
        backItem.props.x = bounds.x1
        backItem.props.y = bounds.y1
        backItem.props.width = bounds.x2 - bounds.x1
        backItem.props.height = bounds.y2 - bounds.y1

        extraCharAllowed = 5
        width = (len(self.tripletToFind.descriptionTranslated) + extraCharAllowed) * 20
        goocanvas.Rect(
          parent = self.gameroot,
          x = gcompris.BOARD_WIDTH / 2 - width / 2,
          y = y + 20,
          width = width,
          height = 40,
          fill_color_rgba = 0x999999CCL,
          stroke_color_rgba = 0x111111AAL,
          line_width = 2.0,
          radius_x = 5,
          radius_y = 10)

        self.textEntry = TextEntry(self.gameroot,
                                   gcompris.BOARD_WIDTH / 2,
                                   y + 40,
                                   u"",
                                   len( self.tripletToFind.descriptionTranslated) + extraCharAllowed)

        self.errorCount = 0
        if self.mode & EnterText.WITH_TEXT:
          goocanvas.Rect(
            parent = self.gameroot,
            x = gcompris.BOARD_WIDTH / 2 - pixbuf.get_width() / 2,
            y = 10,
            width = pixbuf.get_width(),
            height = 60,
            fill_color_rgba = 0x999999BBL,
            stroke_color_rgba = 0x11111111L,
            line_width = 2.0,
            radius_x = 3,
            radius_y = 3)

          self.questionItem = goocanvas.Text(
            parent = self.gameroot,
            x = gcompris.BOARD_WIDTH / 2,
            y = 35,
            fill_color = "white",
            font = gcompris.skin.get_font("gcompris/subtitle"),
            anchor = gtk.ANCHOR_CENTER,
            alignment = pango.ALIGN_CENTER,
            width = 300
            )
          self.setQuestion(self.tripletToFind.descriptionTranslated, self.textEntry.text)

        # The OK Button
        item = goocanvas.Svg(parent = self.gameroot,
                             svg_handle = gcompris.skin.svg_get(),
                             svg_id = "#OK"
                             )
        zoom = 0.8
        item.translate( (item.get_bounds().x1 * -1)
                        + ( gcompris.BOARD_WIDTH - 200 ) / zoom,
                        (item.get_bounds().y1 * -1)
                        + (gcompris.BOARD_HEIGHT - 200) / zoom )
        item.scale(zoom, zoom)
        item.connect("button_press_event", self.ok_event)
        gcompris.utils.item_focus_init(item, None)


    # Set the question with dots like L...E
    # The number of dots depends on the errorCount
    # Return False if all spots are filled
    def setQuestion(self, descriptionTranslated, textEntry):

      text = ''
      clueGiven = False

      for i in range(0, len(descriptionTranslated)):
        if len(textEntry) > i and textEntry[i] == descriptionTranslated[i]:
            text = text + descriptionTranslated[i]
        elif not clueGiven:
            text = text + descriptionTranslated[i]
            clueGiven = True
        else:
            text = text + '.'

      self.questionItem.set_properties(text = text,)
      return True

    def stop(self):
        self.rootitem.remove()

    def checkOk(self):
      if self.tripletToFind.descriptionTranslated == self.textEntry.text:
        self.gameroot.remove()
        self.start()
      else:
        self.errorCount += 1
        if self.setQuestion(self.tripletToFind.descriptionTranslated, self.textEntry.text):
          if self.errorCount == 1:
            self.triplets.append(self.tripletToFind)
          self.repeat()
        else:
          self.lang.loose()

    def ok_event(self, widget, target, event=None):
      self.checkOk()

    def repeat(self):
      self.lang.playVoice(self.tripletToFind)

    def key_press(self, keyval, commit_str, preedit_str):

      if keyval == gtk.keysyms.KP_Enter or keyval == gtk.keysyms.Return:
        self.checkOk()
        return True

      return self.textEntry.key_press(keyval, commit_str, preedit_str)

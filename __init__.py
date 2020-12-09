# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Fit Geometry Area
Description          : Fit geometry by area attribute
Date                 : December, 2020
copyright            : (C) 2020 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Luiz Motta'
__date__ = '2020-12-09'
__copyright__ = '(C) 2020, Luiz Motta'
__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtCore import QObject, Qt, pyqtSlot
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .fitgeometrybyarea import DockWidgetFitGeometryByArea

def classFactory(iface):
  return FitGeomArea( iface )

class FitGeomArea(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.name = u"Fit Geometry Area"
        self.dock = None

    def initGui(self):
        name = "Fit Geometry by Area"
        about = "Fit Geometry by Area"
        icon = QIcon( os.path.join( os.path.dirname(__file__), 'fitgeometrybyarea.svg' ) )
        self.action = QAction( icon, name, self.iface.mainWindow() )
        self.action.setObjectName( name.replace(' ', '') )
        self.action.setWhatsThis( about )
        self.action.setStatusTip( about )
        self.action.setCheckable( True )
        self.action.triggered.connect( self.run )

        self.iface.addToolBarIcon( self.action )
        self.iface.addPluginToMenu( self.name, self.action )

        self.dock = DockWidgetFitGeometryByArea( self.iface )
        self.iface.addDockWidget( Qt.LeftDockWidgetArea , self.dock )
        self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

    def unload(self):
        self.iface.removeToolBarIcon( self.action )
        self.iface.removePluginRasterMenu( self.name, self.action)
        #self.dock.writeSetting()
        self.dock.close()
        self.dock = None
        del self.action

    @pyqtSlot(bool)
    def run(self, checked):
        if self.dock.isVisible():
            self.dock.hide()
        else:
            self.dock.show()

    @pyqtSlot(bool)
    def dockVisibilityChanged(self, visible):
        self.action.setChecked( visible )

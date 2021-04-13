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

import math

from qgis.PyQt.QtCore import (
    Qt, QObject,
    QVariant,
    QSettings,
    pyqtSlot
)
from qgis.PyQt.QtWidgets import (
    QStyle, QSizePolicy,
    QWidget, QLabel, QPushButton,
    QSpacerItem,
    QDockWidget, QGroupBox,
    QVBoxLayout, QHBoxLayout
)
from qgis.PyQt.QtGui import QTransform

from qgis.core import (
    Qgis, QgsProject,
    QgsGeometry, 
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, 
    QgsWkbTypes, QgsUnitTypes,
    QgsFieldProxyModel
)
from qgis.gui import (
  QgsFieldComboBox,
  QgsProjectionSelectionWidget
)


class DockWidgetFitGeometryByArea(QDockWidget):
    TITLE = 'Fit geometry by area'
    def __init__(self, iface):
        def getSetting():
            s = QSettings()
            k = 'crs'
            crs = s.value( self.localSetting.format( k ), None )
            if crs:
              crs = QgsCoordinateReferenceSystem( crs )
            return { 'crs': crs }

        def setSetting(params):
            s = QSettings()
            k = 'crs'
            s.setValue( self.localSetting.format( k ), params[ k ] )

        def setupUI():
            def layoutLayer(parent):
                lyt = QHBoxLayout()
                w = QLabel('Layer:')
                w.setToolTip('Need be a polygon layer')
                lyt.addWidget( w )
                w = QLabel('', parent)
                w.setMargin(1)
                self.__dict__['lbl_layer'] = w
                lyt.addWidget( w )
                s = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
                lyt.addItem( s )
                return lyt

            def layoutArea(parent):
                @pyqtSlot(QgsCoordinateReferenceSystem)
                def crsChanged(crs):
                    if crs.isGeographic():
                        self.message('Invalid CRS(need be projected)', Qgis.Critical )
                        self.crs.setCrs( self.crsCurrent )
                        return
                    s = QgsUnitTypes.encodeUnit( crs.mapUnits() )
                    self.unit.setText(f"{s}^2")
                    setSetting( { 'crs': crs.authid() } )
                    self.crsCurrent = crs

                lytThis = QVBoxLayout()
                w = QgsProjectionSelectionWidget( parent )
                self.__dict__['crs'] = w
                w.crsChanged.connect( crsChanged )
                lytThis.addWidget( w )
                # Field and Apply
                lyt = QHBoxLayout()
                lyt.addWidget( QLabel('Field:') )
                w = QgsFieldComboBox( parent )
                w.setSizeAdjustPolicy( w.AdjustToContents)
                self.__dict__['cmb_fields'] = w
                w.setFilters( QgsFieldProxyModel.Double )
                lyt.addWidget( w )
                w = QLabel('', parent)
                self.__dict__['unit'] = w
                self.crs.setCrs( self.crsCurrent ) # Populate self.unit
                lyt.addWidget( w )
                s = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )                
                lyt.addItem( s )
                w = QPushButton('Fit', parent )
                self.__dict__['btn_fit'] = w
                w.setIcon( self.iconApply )
                lyt.addWidget( w )
                lytThis.addLayout( lyt )
                # First Layer
                lyt = QHBoxLayout()
                w = QLabel('Feature:')
                w.setToolTip('First selected feature')
                lyt.addWidget( w )
                w = QLabel('', parent )
                self.__dict__['lbl_demo_feature'] = w
                lyt.addWidget( w )
                s = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )                
                lyt.addItem( s )
                lytThis.addLayout( lyt )
                return lytThis

            wgtMain = QGroupBox('Fit geometry(selected features)', self )
            self.__dict__['chk_fit'] = wgtMain
            wgtMain.setAttribute(Qt.WA_DeleteOnClose)
            wgtMain.setCheckable( True )
            wgtMain.setChecked( False )
            lytMain = QVBoxLayout()
            #
            lytMain.addLayout( layoutLayer( wgtMain ) )
            gpbArea = QGroupBox('Area',  wgtMain )
            gpbArea.setLayout( layoutArea( wgtMain ) )
            lytMain.addWidget( gpbArea )
            #
            s = QSpacerItem( 10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding )
            lytMain.addItem( s )
            wgtMain.setLayout( lytMain )
            self.setWidget( wgtMain )

        super().__init__(f"{self.TITLE}", iface.mainWindow() )
        self.msgBar = iface.messageBar()        
        title = self.TITLE.replace(' ', '_')
        self.setObjectName(f"{title}_dockwidget")
        self.iconApply = self.style().standardIcon( QStyle.SP_DialogApplyButton )
        # Set CRS
        self.localSetting = "{}/{}".format( title, '{}')
        p = getSetting()
        self.crsCurrent = p['crs'] if p['crs'] else QgsCoordinateReferenceSystem('EPSG:29101') 
        #
        setupUI()
        self.fga = FitGeometryByArea( iface, self.crsCurrent, self.message, self.setLayer, self.getField, self.setDemoFeature )
        self.chk_fit.clicked.connect( self.fga.on_chk_fit_clicked )
        self.btn_fit.clicked.connect( self.fga.on_btn_fit_clicked )
        self.cmb_fields.currentIndexChanged.connect( self.fga.on_cmb_fields_currentIndexChanged )

    def setLayer(self, layer=None):
        if layer is None:
            self.lbl_layer.setText('')
            self.lbl_demo_feature.setText('' )
            self.cmb_fields.setLayer( None )
            self.chk_fit.setChecked( False )
            return
        self.lbl_layer.setText( layer.name() )
        self.cmb_fields.setLayer( layer )
        self.cmb_fields.setCurrentIndex(0)
        crs = layer.crs()
        if not crs.isGeographic():
            self.crs.setCrs( crs )

    def getField(self):
        return self.cmb_fields.currentField()

    def setDemoFeature(self, message):
        self.lbl_demo_feature.setText( message )

    def message(self, message, level=Qgis.Info):
        funcs = {
            Qgis.Info: self.msgBar.pushInfo,
            Qgis.Warning: self.msgBar.pushWarning,
            Qgis.Critical: self.msgBar.pushCritical,
            Qgis.Success: self.msgBar.pushSuccess
        }
        if not level in funcs:
            return
        self.msgBar.popWidget()
        funcs[ level ]( self.TITLE, message )


class FitGeometryByArea(QObject):
    def __init__( self, iface, crsCurrent, message, setLayer, getField, setDemoFeature ):
        super().__init__()
        self.iface = iface
        self.crsCurrent = crsCurrent
        self.message = message
        self.setWigetlayer = setLayer
        self.getWidgetField = getField
        self.setWidgetDemoFeature = setDemoFeature

        project = QgsProject.instance()
        self.context = project.transformContext()
        self.layer = None
        self.getFitGeom, self.ct2Calc, self.ct2Layer = None, None, None

        project.layerWillBeRemoved.connect( self.on_layerWillBeRemoved )
        
    @pyqtSlot(str)
    def on_layerWillBeRemoved(self, id):
        if self.layer and self.layer.id() == id:
            self.layer = None
            self.setWigetlayer() # Clean

    @pyqtSlot(bool)
    def on_chk_fit_clicked(self, checked):
        def isPolygon(l):
            return l.type() == l.VectorLayer and l.geometryType() == QgsWkbTypes.PolygonGeometry

        def hasDoubleField(l):
            for f in l.fields().toList():
                if f.type() == QVariant.Double:
                    return True
            return False

        def clean(message=None):
            if message: self.message( message, Qgis.Warning )
            self.setWigetlayer()
            if self.layer:
                self.layer.selectionChanged.disconnect( self.on_selectionChanged )
            self.layer = None

        if checked:
            lyr = self.iface.activeLayer()
            if lyr is None:
                clean('Missing active layer.')
                return
            if not isPolygon( lyr ):
                clean(f"Invalid layer '{lyr.name()}'! Need be vector layer.")
                return
            if not hasDoubleField( lyr ):
                clean(f"Layer '{lyr.name()}' missing double field.")
                return

            self.getFitGeom = self._getFitGeom
            crsLayer = lyr.crs()
            if not crsLayer == self.crsCurrent:
                self.ct2Calc = QgsCoordinateTransform( crsLayer, self.crsCurrent, self.context )
                self.ct2Layer = QgsCoordinateTransform( self.crsCurrent, crsLayer,  self.context )
                self.getFitGeom = self._getFitGeomTransform
            self.setWigetlayer( lyr ) # Change current Field
            if lyr.selectedFeatureCount():
                self._calcAreaDemoFeature()
            lyr.selectionChanged.connect( self.on_selectionChanged )
            self.layer = lyr
        else:
            clean()

    @pyqtSlot(bool)
    def on_btn_fit_clicked(self, checked):
        if not self.layer.isEditable():
            msg = f"Layer '{self.layer.name()}' needs to be editable"
            self.message( msg, Qgis.Warning )
            return
        feats = self.layer.selectedFeatures()
        if len( feats ) == 0:
            msg = f"Need selected features in '{self.layer.name()}'"
            self.message( msg, Qgis.Warning )
            return

        name = self.getWidgetField()
        for feat in feats:
            area = feat[ name ]
            if area is None:
                continue
            fid = feat.id()
            geom = feat.geometry()
            if geom is None:
                continue
            geom = self.getFitGeom( area, geom )
            self.layer.changeGeometry( fid, geom )
        self.layer.updateExtents()
        self.layer.triggerRepaint()
        self.setWidgetDemoFeature('')

    @pyqtSlot(int)
    def on_cmb_fields_currentIndexChanged(self, index):
        if not self.layer or index == -1:
            return
        
        if not self.layer.selectedFeatureCount():
            self.setWidgetDemoFeature('')
            msg = f"Layer '{self.layer.name()}' need selected feature"
            self.message( msg, Qgis.Warning )
            return

        self._calcAreaDemoFeature()

    @pyqtSlot('QgsFeatureIds', 'QgsFeatureIds', bool)
    def on_selectionChanged(self, selected, deselected, clearAndSelect):
        if not len( selected ):
            return
        self._calcAreaDemoFeature()

    def _getFitGeom(self, area, geom):
        def getCenterXY(geom):
            center = geom.centroid().asPoint()
            return { 'x': center.x(), 'y': center.y() }

        center1 = getCenterXY( geom )
        s = math.sqrt( area / geom.area() )
        t = QTransform.fromScale( s, s )
        ok = geom.transform( t )
        center2 = getCenterXY( geom )
        dx = center1['x'] - center2['x']
        dy = center1['y'] - center2['y']
        ok = geom.translate( dx, dy )
        return geom

    def _getFitGeomTransform(self, area, geom):
        geom.transform( self.ct2Calc )
        geom = self._getFitGeom( area, geom )
        geom.transform( self.ct2Layer )
        return geom

    def _calcAreaDemoFeature(self):
        name = self.getWidgetField()
        # First Feature
        feat = self.layer.selectedFeatures()[0]
        fid, area, geom = feat.id(), feat[ name ], feat.geometry()
        if area is None:
            self.message(f"Field '{name}' is empty", Qgis.Warning )
            self.setWidgetDemoFeature('')
            return
        if geom is None:
            self.message('Geometry is empty', Qgis.Warning )
            self.setWidgetDemoFeature('')
            return

        srcArea = geom.area()
        fitArea = self.getFitGeom(area, QgsGeometry( geom ) ).area()
        perc = 100 * ( 1 - srcArea / fitArea )
        msg = f"[FID = {fid}] Geometry to Fit -> {perc:+0.6f}%"
        self.setWidgetDemoFeature( msg )



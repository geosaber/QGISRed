# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRed
                                 A QGIS plugin
 Some util tools for GISRed
                              -------------------
        begin                : 2019-03-26
        git sha              : $Format:%H$
        copyright            : (C) 2019 by REDHISP (UPV)
        email                : fmartine@hma.upv.es
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

from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup, QgsLayerTreeNode, QgsProjectBadLayerHandler

try: #QGis 3.x
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QApplication, QMenu
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
    from qgis.core import Qgis, QgsTask, QgsApplication
    #Import resources
    from . import resources3x
    # Import the code for the dialog
    from .ui.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
    from .ui.qgisred_newproject_dialog import QGISRedNewProjectDialog
    from .ui.qgisred_import_dialog import QGISRedImportDialog
    from .ui.qgisred_about_dialog import QGISRedAboutDialog
    from .ui.qgisred_results_dock import QGISRedResultsDock
    from .qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QApplication, QMenu
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
    from qgis.core import QgsMapLayerRegistry, QGis as Qgis
    #Import resources
    import resources2x
    # Import the code for the dialog
    from ui.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
    from ui.qgisred_newproject_dialog import QGISRedNewProjectDialog
    from ui.qgisred_import_dialog import QGISRedImportDialog
    from ui.qgisred_about_dialog import QGISRedAboutDialog
    from ui.qgisred_results_dock import QGISRedResultsDock
    from qgisred_utils import QGISRedUtils

# Others imports
import os
import os.path
import datetime
from time import strftime
from ctypes import*
import time
import tempfile

import threading

#MessageBar Levels
# Info 0
# Warning 1
# Critical 2
# Success 3

class QGISRed:
    """QGIS Plugin Implementation."""
    ResultDockwidget = None
    #Project variables
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    ownFiles = ["Curves", "Controls", "Patterns", "Rules", "Options", "DefaultValues"]
    TemporalFolder = "Temporal folder"

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'qgisred_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        #self.menu = self.tr(u'&QGISRed') 
        #Toolbar
        self.toolbar = self.iface.addToolBar(u'QGISRed')
        self.toolbar.setObjectName(u'QGISRed')
        #Menu
        self.qgisredmenu = QMenu("&QGISRed", self.iface.mainWindow().menuBar())
        actions = self.iface.mainWindow().menuBar().actions()
        lastAction = actions[-1]
        self.iface.mainWindow().menuBar().insertMenu(lastAction, self.qgisredmenu )

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QGISRed', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        menubar,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = QGISRedNewProjectDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            #self.iface.addPluginToMenu(self.menu,action)
            menubar.addAction(action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QGISRed/images/iconProjectManager.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Project manager'),
            callback=self.runProjectManager,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconSaveProject.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Save project'),
            callback=self.runSaveProject,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconCreateProject.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create/Edit project'),
            callback=self.runNewProject,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconImport.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Import to SHPs'),
            callback=self.runImport,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconValidate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Validate Model'),
            callback=self.runValidateModel,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconCommit.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Commit'),
            callback=self.runCommit,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconShpToInp.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Export model to INP'),
            callback=self.runExportInp,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconRunModel.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Run model && show results'),
            callback=self.runModel,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())


        #self.gisredmenuTools = self.qgisredmenu.addMenu('Sub-menu')
        #self.gisredmenuTools.setIcon(QIcon(icoFolder + 'img1.png'))

        icon_path = ':/plugins/QGISRed/images/iconAbout.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'About...'),
            callback=self.runAbout,
            menubar=self.qgisredmenu,
            parent=self.iface.mainWindow())
        
        from shutil import copyfile
        import platform
        if "64bit" in str(platform.architecture()):
            folder = "x64"
        else:
            folder = "x86"
        currentDirectory = os.path.join(os.path.dirname(__file__), "dlls")
        plataformDirectory = os.path.join(currentDirectory, folder)
        try:
            copyfile(os.path.join(plataformDirectory, "shapelib.dll"), os.path.join(currentDirectory, "shapelib.dll"))
            copyfile(os.path.join(plataformDirectory, "epanet2.dll"), os.path.join(currentDirectory, "epanet2.dll"))
            copyfile(os.path.join(plataformDirectory, "GISRed.QGisPlugins.dll"), os.path.join(currentDirectory, "GISRed.QGisPlugins.dll"))
        except:
            pass

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()
            self.iface.removeDockWidget(self.ResultDockwidget)
            self.ResultDockwidget = None
        
        for action in self.actions:
            #self.iface.removePluginMenu(self.tr(u'&QGISRed'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        if self.qgisredmenu:
            self.qgisredmenu.menuAction().setVisible(False)
        # if self.qgisredmenuTools:
            # self.qgisredmenuTools.menuAction().setVisible(False)

    def createGqpFile(self):
        gqp = os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp")
        creationDate=""
        if os.path.exists(gqp):
            f= open(gqp, "r")
            lines = f.readlines()
            if len(lines)>=1:
                creationDate = lines[0].strip("\r\n")
            f.close()
        f = open(gqp, "w+")
        if creationDate=="":
            creationDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(creationDate + '\n')
        f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        
        qgsFilename =QgsProject.instance().fileName()
        if not qgsFilename=="":
            QGISRedUtils().writeFile(f, qgsFilename)
        else:
            try: #QGis 3.x
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
            except: #QGis 2.x
                layers = self.iface.legendInterface().layers()
            #Inputs
            groupName = self.NetworkName + " Inputs"
            dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
            if dataGroup is None:
                f.write("[NoGroup]\n")
                for layer in reversed(layers):
                    QGISRedUtils().writeFile(f, layer.dataProvider().dataSourceUri().split("|")[0] + '\n')
            else:
                QGISRedUtils().writeFile(f, "[" + self.NetworkName + " Inputs]\n")
                self.writeLayersOfGroups(groupName, f, layers)
        f.close()

    def writeLayersOfGroups(self, groupName, file, layers):
        root = QgsProject.instance().layerTreeRoot()
        for layer in reversed(layers):
            parent = root.findLayer(layer.id())
            if not parent is None:
                if parent.parent().name() == groupName:
                    QGISRedUtils().writeFile(file, layer.dataProvider().dataSourceUri().split("|")[0] + '\n')

    def defineCurrentProject(self):
        self.NetworkName ="Network"
        self.ProjectDirectory = self.TemporalFolder
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            layerUri= layer.dataProvider().dataSourceUri().split("|")[0]
            for layerName in self.ownMainLayers:
                if "_" + layerName in layerUri:
                    self.ProjectDirectory = os.path.dirname(layerUri)
                    vectName = os.path.splitext(os.path.basename(layerUri))[0].split("_")
                    name =""
                    for part in vectName:
                        if part in self.ownMainLayers:
                            break
                        name = name + part + "_"
                    name = name.strip("_")
                    self.NetworkName = name
                    return

    def isOpenedProject(self):
        if self.isLayerOnEdition():
            return False
        qgsFilename =QgsProject.instance().fileName()
        if not qgsFilename=="":
            if QgsProject.instance().isDirty():
                #Guardar y continuar
                self.iface.messageBar().pushMessage("Warning", "The project has changes. Please save them before continuing.", level=1)
            else:
                #Cerrar proyecto y continuar?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened project', 'Do you want to close the current project and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers())>0:
                #Cerrar archivos y continuar?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened layers', 'Do you want to close the current layers and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def isLayerOnEdition(self):
        for layer in self.iface.mapCanvas().layers():
            if layer.isEditable():
                self.iface.messageBar().pushMessage("Warning", "Some layer is in Edit Mode. Plase, commit it before continuing.", level=1)
                return True
        return False

    def runProjectManager(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        # show the dialog
        dlg = QGISRedProjectManagerDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)

        # Run the dialog event loop
        dlg.exec_()
        # See if OK was pressed
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory
            self.createGqpFile()

    def runSaveProject(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
        else:
            self.createGqpFile()

    def runNewProject(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            if not self.isOpenedProject():
                return
        # show the dialog
        dlg = QGISRedNewProjectDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        # See if OK was pressed
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            self.createGqpFile()

    def runImport(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            if not self.isOpenedProject():
                return
        # show the dialog
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)

        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        # See if OK was pressed
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            self.createGqpFile()

    def runValidateModel(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
            return
        if self.isLayerOnEdition():
            return

        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ValidateModel.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ValidateModel.restype = c_char_p
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        b = mydll.ValidateModel(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Topology is valid", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def removeLayers(self, task, wait_time):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        raise Exception('')

    def runCommit(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runCommitProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(u'Remove layers', self.removeLayers, on_finished=self.runCommitProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runCommitProcess(self, exception=None, result=None):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CommitModel.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CommitModel.restype = c_char_p
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        b = mydll.CommitModel(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        #if version2:
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")

        #Open layers
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #if version2:
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()

        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Successful commit", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def runExportInp(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        elif not b=="Canceled":
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def runModel(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
            return
        if self.isLayerOnEdition():
            return
        
        if self.ResultDockwidget is None:
            self.ResultDockwidget = QGISRedResultsDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.ResultDockwidget)
        self.ResultDockwidget.config(self.ProjectDirectory, self.NetworkName)
        self.ResultDockwidget.show()

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec_()
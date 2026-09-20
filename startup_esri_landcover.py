# Toolbar button "Esri Land Cover Style"
# IMPORTANT: if you already have a startup.py (e.g. from the MapBiomas ID Style Toolbox),
# do NOT overwrite it — paste the contents of this file at the very bottom of your
# existing startup.py. Function and attribute names here are unique, so this button
# does not clash with the MapBiomas one.

from qgis.PyQt.QtCore import QTimer

def _add_esri_landcover_button():
    from qgis.utils import iface
    from qgis.PyQt.QtWidgets import QAction, QMessageBox
    from qgis.core import QgsApplication

    main_win = iface.mainWindow()

    existing = getattr(main_win, '_esri_landcover_btn', None)
    if existing is not None:
        iface.removeToolBarIcon(existing)
        existing.deleteLater()
        main_win._esri_landcover_btn = None

    def run_tool():
        reg = QgsApplication.processingRegistry()
        target = None
        for alg in reg.algorithms():
            if 'esri_landcover_raster_to_vector' in alg.id():
                target = alg.id()
                break
        if target:
            import processing
            processing.execAlgorithmDialog(target)
        else:
            QMessageBox.warning(
                main_win,
                'Esri Land Cover Style',
                'Script not found.\n\n'
                'Make sure esri_landcover_style_qgis_toolbox.py\n'
                'has been added to the Processing Toolbox.\n\n'
                'Processing Toolbox > Python icon > Add Script to Toolbox...'
            )

    action = QAction('Esri Land Cover Style', main_win)
    action.setToolTip(
        'Esri 10m Land Cover Raster Symbology\n'
        'Author: Defani Arman Alfitriansyah\n'
        'github.com/Defani'
    )
    action.triggered.connect(run_tool)
    iface.addToolBarIcon(action)
    main_win._esri_landcover_btn = action

QTimer.singleShot(3000, _add_esri_landcover_button)

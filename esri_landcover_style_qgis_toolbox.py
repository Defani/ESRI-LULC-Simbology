# Esri Land Cover Raster Symbology (all versions)
# Author  : Defani Arman Alfitriansyah
# GitHub  : https://github.com/Defani
# Toolbox : Esri Land Cover Custom Visualization Toolbox
#
# Data    : Esri 10m Land Cover — Impact Observatory / Esri
#   - 2017-2025, 9 classes : https://gee-community-catalog.org/projects/S2TSLULC/
#   - 2020, 10 classes     : https://gee-community-catalog.org/projects/esrilc2020/

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer, QgsProcessingParameterBand,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorDestination, QgsProcessingParameterBoolean,
    QgsVectorLayer, QgsField,
    QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsFillSymbol,
    QgsProject, QgsProcessingException, QgsProcessingUtils,
)
import processing

# ---------------------------------------------------------------------------
# Pixel-value schemes. Each scheme has:
#   label   : text shown in the dropdown
#   version : version name (written to the `lulc_ver` attribute)
#   nodata  : pixel values removed BEFORE dissolve
#   classes : [(pixel_value, Land Cover Class, Hex Code), ...] in official legend order
# ---------------------------------------------------------------------------
SCHEMES = [
    {   # 0 — S2TSLULC table, "Remapped Value" column
        'label':   '2017-2025 (9 classes) — Remapped 1-9 · GEE community catalog',
        'version': 'Esri 10m Annual LULC 2017-2025 (9 classes, remapped)',
        'nodata':  [0],
        'classes': [
            (1, 'Water',              '#1A5BAB'),
            (2, 'Trees',              '#358221'),
            (3, 'Flooded Vegetation', '#87D19E'),
            (4, 'Crops',              '#FFDB5C'),
            (5, 'Built Area',         '#ED022A'),
            (6, 'Bare Ground',        '#EDE9E4'),
            (7, 'Snow/Ice',           '#F2FAFF'),
            (8, 'Clouds',             '#C8C8C8'),
            (9, 'Rangeland',          '#C6AD8D'),
        ],
    },
    {   # 1 — S2TSLULC table, "Class Value" column
        'label':   '2017-2025 (9 classes) — Original 1,2,4,5,7,8,9,10,11 · official Esri / Impact Observatory download',
        'version': 'Esri 10m Annual LULC 2017-2025 (9 classes, original values)',
        'nodata':  [0],
        'classes': [
            (1,  'Water',              '#1A5BAB'),
            (2,  'Trees',              '#358221'),
            (4,  'Flooded Vegetation', '#87D19E'),
            (5,  'Crops',              '#FFDB5C'),
            (7,  'Built Area',         '#ED022A'),
            (8,  'Bare Ground',        '#EDE9E4'),
            (9,  'Snow/Ice',           '#F2FAFF'),
            (10, 'Clouds',             '#C8C8C8'),
            (11, 'Rangeland',          '#C6AD8D'),
        ],
    },
    {   # 2 — esrilc2020 table (Category 1 = No Data, 2-11 = classes)
        'label':   '2020 (10 classes) — GEE community catalog (values 1-11, 1 = No Data)',
        'version': 'Esri 2020 LULC (10 classes, GEE catalog values)',
        'nodata':  [0, 1],
        'classes': [
            (2,  'Water',              '#1A5BAB'),
            (3,  'Trees',              '#358221'),
            (4,  'Grass',              '#A7D282'),
            (5,  'Flooded Vegetation', '#87D19E'),
            (6,  'Crops',              '#FFDB5C'),
            (7,  'Scrub/Shrub',        '#EECFA8'),
            (8,  'Built Area',         '#ED022A'),
            (9,  'Bare Ground',        '#EDE9E4'),
            (10, 'Snow/Ice',           '#F2FAFF'),
            (11, 'Clouds',             '#C8C8C8'),
        ],
    },
    {   # 3 — original Esri 2020 class numbering (1-10)
        'label':   '2020 (10 classes) — Original 1-10 · official Esri / Impact Observatory download',
        'version': 'Esri 2020 LULC (10 classes, original values)',
        'nodata':  [0],
        'classes': [
            (1,  'Water',              '#1A5BAB'),
            (2,  'Trees',              '#358221'),
            (3,  'Grass',              '#A7D282'),
            (4,  'Flooded Vegetation', '#87D19E'),
            (5,  'Crops',              '#FFDB5C'),
            (6,  'Scrub/Shrub',        '#EECFA8'),
            (7,  'Built Area',         '#ED022A'),
            (8,  'Bare Ground',        '#EDE9E4'),
            (9,  'Snow/Ice',           '#F2FAFF'),
            (10, 'Clouds',             '#C8C8C8'),
        ],
    },
]
SCHEME_LABELS = [s['label'] for s in SCHEMES]


def _lookup(scheme_idx):
    """{pixel_value: (class_name, hex)} for the selected scheme."""
    return {v: (name, hx) for v, name, hx in SCHEMES[scheme_idx]['classes']}


def _apply_symbology(layer, scheme_idx, field='gridcode'):
    """
    Build the legend only from classes that actually exist in the data.
    Classes absent from the layer are not shown in the legend.
    """
    scheme = SCHEMES[scheme_idx]
    idx = layer.fields().indexOf(field)
    present = set()
    for val in layer.uniqueValues(idx):
        try:
            present.add(int(val))
        except (TypeError, ValueError):
            pass

    categories = []
    for value, name, hx in scheme['classes']:      # official legend order
        if value in present:
            sym = QgsFillSymbol.createSimple({'color': hx, 'outline_style': 'no'})
            categories.append(QgsRendererCategory(value, sym, name))

    known = {c[0] for c in scheme['classes']}
    if present - known:
        sym_unk = QgsFillSymbol.createSimple({'color': '#aaaaaa', 'outline_style': 'no'})
        categories.append(QgsRendererCategory('', sym_unk, 'Unknown'))

    layer.setRenderer(QgsCategorizedSymbolRenderer(field, categories))
    layer.triggerRepaint()


class _GeoJsonVectorDestination(QgsProcessingParameterVectorDestination):
    """
    Small subclass so the "Save Vector Layer As" dialog suggests .geojson
    as the default extension, without restricting other formats
    (GeoPackage .gpkg, Shapefile .shp, etc. can still be chosen manually).
    """
    def defaultFileExtension(self):
        return 'geojson'


class EsriLandCoverRasterToVectorAlgorithm(QgsProcessingAlgorithm):
    INPUT_RASTER   = 'INPUT_RASTER'
    BAND           = 'BAND'
    SCHEME         = 'SCHEME'
    OUTPUT_VECTOR  = 'OUTPUT_VECTOR'
    LOAD_TO_CANVAS = 'LOAD_TO_CANVAS'

    def tr(self, s): return QCoreApplication.translate('Processing', s)
    def createInstance(self): return EsriLandCoverRasterToVectorAlgorithm()
    def name(self):        return 'esri_landcover_raster_to_vector'
    def displayName(self): return self.tr('Esri Land Cover Raster Symbology')
    def group(self):       return self.tr('Esri Land Cover Custom Visualization Toolbox')
    def groupId(self):     return 'esri_landcover'

    def shortHelpString(self):
        return self.tr(
            "<b>Esri 10m Land Cover Raster Symbology (all versions)</b>"
            "<hr>"
            "Automated workflow:<br>"
            "1. Polygonize the raster into vector polygons<br>"
            "2. Remove NoData polygons before dissolving<br>"
            "3. Dissolve by class (gridcode)<br>"
            "4. Fill attributes from gridcode (English class names)<br>"
            "5. Apply the official Esri / Impact Observatory colors<br>"
            "6. Legend shows only the classes present in the data<br>"
            "7. Default output format is <b>GeoJSON</b> — GeoPackage (.gpkg) or "
            "Shapefile (.shp) can be chosen in the save dialog<br>"
            "<br>"
            "<b>Pick the version &amp; pixel-value scheme that matches your raster:</b><br>"
            "&bull; <b>2017-2025 (9 classes)</b> — Remapped 1-9 (GEE) or Original "
            "1,2,4,5,7,8,9,10,11.<br>"
            "&bull; <b>2020 (10 classes, Grass &amp; Scrub separate)</b> — GEE catalog "
            "(values 1-11, value 1 = No Data) or Original 1-10.<br>"
            "The same number can mean different classes in different schemes, so a wrong "
            "choice gives wrong colors and class names.<br>"
            "<hr>"
            "Data: Impact Observatory for Esri, CC BY 4.0.<br>"
            "Author : Defani Arman Alfitriansyah<br>"
            "GitHub : <a href='https://github.com/Defani'>github.com/Defani</a>")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT_RASTER, self.tr('Esri 10m Land Cover raster')))
        self.addParameter(QgsProcessingParameterBand(
            self.BAND, self.tr('Band (default Band 1)'),
            parentLayerParameterName=self.INPUT_RASTER, defaultValue=1))
        self.addParameter(QgsProcessingParameterEnum(
            self.SCHEME, self.tr('Esri Land Cover version & pixel-value scheme'),
            options=SCHEME_LABELS, defaultValue=0))
        out_param = _GeoJsonVectorDestination(
            self.OUTPUT_VECTOR,
            self.tr('Output vector polygons (default GeoJSON — GeoPackage/.gpkg or Shapefile/.shp also possible)'),
            type=QgsProcessing.TypeVectorPolygon)
        self.addParameter(out_param)
        self.addParameter(QgsProcessingParameterBoolean(
            self.LOAD_TO_CANVAS,
            self.tr('Load to canvas with Esri Land Cover symbology'), defaultValue=True))

    def processAlgorithm(self, parameters, context, feedback):
        raster     = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        band       = self.parameterAsInt(parameters, self.BAND, context)
        scheme_idx = self.parameterAsEnum(parameters, self.SCHEME, context)
        out_path   = self.parameterAsOutputLayer(parameters, self.OUTPUT_VECTOR, context)
        load       = self.parameterAsBool(parameters, self.LOAD_TO_CANVAS, context)

        if raster is None:
            raise QgsProcessingException(self.tr('Invalid raster layer.'))

        scheme = SCHEMES[scheme_idx]
        lookup = _lookup(scheme_idx)
        feedback.pushInfo('Version / scheme: ' + scheme['label'])

        feedback.setProgressText('Step 1/6 — Polygonizing raster to vector ...')
        poly = processing.run('gdal:polygonize', {
            'INPUT': raster, 'BAND': band, 'FIELD': 'gridcode',
            'EIGHT_CONNECTEDNESS': False, 'EXTRA': '', 'OUTPUT': 'TEMPORARY_OUTPUT',
        }, context=context, feedback=feedback, is_child_algorithm=True)
        if feedback.isCanceled(): return {}
        feedback.setProgress(20)

        nodata_txt = ', '.join(str(v) for v in scheme['nodata'])
        feedback.setProgressText(
            f'Step 2/6 — Removing NoData polygons (gridcode = {nodata_txt}) ...')
        # NoData polygons are removed BEFORE dissolve so the dissolved output is clean.
        clean = processing.run('native:extractbyexpression', {
            'INPUT': poly['OUTPUT'],
            'EXPRESSION': f'"gridcode" NOT IN ({nodata_txt})',
            'OUTPUT': 'TEMPORARY_OUTPUT',
        }, context=context, feedback=feedback, is_child_algorithm=True)
        if feedback.isCanceled(): return {}
        feedback.setProgress(25)

        feedback.setProgressText('Step 3/6 — Dissolving by class (gridcode) ...')
        # 'TEMPORARY_OUTPUT' for native algorithms may yield an in-memory layer
        # (not a physical file), which cannot be reopened through the 'ogr' provider.
        # Here the dissolve result is written to a real temporary GeoPackage file.
        dissolve_tmp_path = QgsProcessingUtils.generateTempFilename('dissolved.gpkg')
        dissolved = processing.run('native:dissolve', {
            'INPUT': clean['OUTPUT'], 'FIELD': ['gridcode'], 'OUTPUT': dissolve_tmp_path,
        }, context=context, feedback=feedback, is_child_algorithm=True)
        if feedback.isCanceled(): return {}
        feedback.setProgress(30)

        feedback.setProgressText('Step 4/6 — Adding attribute fields ...')
        tmp = QgsVectorLayer(dissolved['OUTPUT'], 'tmp', 'ogr')
        if not tmp.isValid():
            raise QgsProcessingException(self.tr('Dissolve failed.'))
        dp = tmp.dataProvider()
        dp.addAttributes([
            QgsField('class_en',  QVariant.String, len=80),
            QgsField('hex_color', QVariant.String, len=10),
            QgsField('lulc_ver',  QVariant.String, len=80),
        ])
        tmp.updateFields()
        feedback.setProgress(38)

        feedback.setProgressText('Step 5/6 — Filling attribute table ...')
        flds = tmp.fields()
        i = {n: flds.indexOf(n) for n in ['gridcode', 'class_en', 'hex_color', 'lulc_ver']}
        tmp.startEditing()
        n_feat = tmp.featureCount()
        step   = max(1, n_feat // 50)
        unknown = set()

        for idx, feat in enumerate(tmp.getFeatures()):
            if feedback.isCanceled():
                tmp.rollBack(); return {}
            if idx % step == 0:
                feedback.setProgress(38 + int(37 * idx / max(n_feat, 1)))
            try:   gc = int(feat[i['gridcode']])
            except (TypeError, ValueError): gc = -1
            if gc in lookup:
                c_en, hx = lookup[gc]
            else:
                unknown.add(gc)
                c_en, hx = f'Unknown({gc})', '#aaaaaa'
            fid = feat.id()
            tmp.changeAttributeValue(fid, i['class_en'],  c_en)
            tmp.changeAttributeValue(fid, i['hex_color'], hx)
            tmp.changeAttributeValue(fid, i['lulc_ver'],  scheme['version'])
        tmp.commitChanges()
        feedback.setProgress(75)

        if unknown:
            feedback.pushWarning(
                f'Gridcodes not recognized for the selected scheme: {sorted(unknown)}. '
                'Check that "Esri Land Cover version & pixel-value scheme" matches your '
                'raster (9 vs 10 classes, GEE vs Original).')

        feedback.setProgressText('Step 6/6 — Saving output ...')
        saved = processing.run('native:savefeatures', {
            'INPUT': tmp, 'OUTPUT': out_path,
        }, context=context, feedback=feedback, is_child_algorithm=True)
        final = saved['OUTPUT']
        feedback.setProgress(92)

        if load:
            lyr = QgsVectorLayer(final, 'Esri 10m Land Cover', 'ogr')
            if lyr.isValid():
                _apply_symbology(lyr, scheme_idx)
                QgsProject.instance().addMapLayer(lyr)
                feedback.pushInfo('Layer loaded to canvas with Esri Land Cover symbology')
                feedback.pushInfo('Legend shows only the classes present in the data.')
            else:
                feedback.reportError('The output layer could not be loaded to the canvas.')

        feedback.setProgress(100)
        return {self.OUTPUT_VECTOR: final}

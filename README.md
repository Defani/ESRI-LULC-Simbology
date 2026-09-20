# Esri Land Cover Style — QGIS Toolbox

A QGIS toolbox that automatically symbolizes **Esri 10m Land Cover** rasters as labeled, colored vector polygons. It supports **all versions**: the annual **2017–2025 (9 classes)** collection and the **Esri 2020 (10 classes)** map, each in both the GEE and the Original pixel-value scheme. 

> Data produced by Impact Observatory for Esri (© 2021 Esri, CC BY 4.0). This toolbox is not officially affiliated with Esri or Impact Observatory. See [`NOTICE.md`](./NOTICE.md).


https://github.com/user-attachments/assets/9711dd43-0e88-4719-919b-fc37ef878931


## Features

- Polygonize → remove NoData → dissolve by class → fill attributes → automatic symbology
- **4 version/scheme options** in a single dropdown (see the table below)
- NoData is removed **before** dissolving, so the dissolved output is clean
- Class names are always in **English** (as in the official Esri definitions)
- Dynamic legend — only classes present in the data are shown
- Default output is GeoJSON (`.gpkg` / `.shp` also possible)
- Quick-access **Esri Land Cover Style** button on the QGIS toolbar

## Tool Architecture & Workflow

### 1. Processing workflow

```mermaid
flowchart TD
    A[/"Esri 10m Land Cover raster (GeoTIFF)"/] --> B["Select version and pixel-value scheme"]
    B --> C["Step 1/6 - gdal:polygonize<br/>field = gridcode"]
    C --> D["Step 2/6 - native:extractbyexpression<br/>gridcode NOT IN NoData values"]
    D --> E["Step 3/6 - native:dissolve<br/>by gridcode, temporary GeoPackage"]
    E --> F["Step 4-5/6 - add and fill fields<br/>class_en, hex_color, lulc_ver"]
    F --> G{"Unknown gridcodes?"}
    G -- yes --> H["Warning: check version and scheme"]
    G -- no --> I
    H --> I["Step 6/6 - native:savefeatures<br/>GeoJSON / GPKG / SHP"]
    I --> J{"Load to canvas?"}
    J -- yes --> K["Categorized symbology<br/>only classes present in the data"]
    K --> L[/"Styled vector layer with dynamic legend"/]
    J -- no --> M[/"Vector file saved"/]
```

### 2. Which scheme should I pick?

```mermaid
flowchart TD
    S["Where does your raster come from?"] --> Q1{"Which product?"}
    Q1 -- "Annual 2017-2025, 9 classes" --> Q2{"Pixel values present?"}
    Q1 -- "Esri 2020, 10 classes" --> Q3{"Pixel values present?"}
    Q2 -- "1 to 9" --> O0["Option 1: 2017-2025 Remapped 1-9"]
    Q2 -- "1,2,4,5,7,8,9,10,11" --> O1["Option 2: 2017-2025 Original"]
    Q3 -- "2 to 11, value 1 = No Data" --> O2["Option 3: 2020 GEE catalog"]
    Q3 -- "1 to 10" --> O3["Option 4: 2020 Original"]
```

### 3. Components

```mermaid
flowchart LR
    subgraph Repo["Repository"]
        P["esri_landcover_style_qgis_toolbox.py"]
        T["startup_esri_landcover.py"]
        N["README.md / NOTICE.md / LICENSE"]
    end
    subgraph QGIS["QGIS"]
        PT["Processing Toolbox"]
        PR["Algorithm: esri_landcover_raster_to_vector"]
        TB["Toolbar button: Esri Land Cover Style"]
        PJ["Project canvas"]
    end
    P -- "Add Script to Toolbox" --> PT
    PT --> PR
    T -- "profile python/startup.py" --> TB
    TB -- "execAlgorithmDialog" --> PR
    PR -- "add layer and renderer" --> PJ
```

### 4. Code structure

```mermaid
classDiagram
    class EsriLandCoverRasterToVectorAlgorithm {
        +INPUT_RASTER
        +BAND
        +SCHEME
        +OUTPUT_VECTOR
        +LOAD_TO_CANVAS
        +initAlgorithm()
        +processAlgorithm()
        +shortHelpString()
    }
    class GeoJsonVectorDestination {
        +defaultFileExtension() str
    }
    class SCHEMES {
        label
        version
        nodata
        classes
    }
    class apply_symbology {
        categorized renderer
        only classes present in data
    }
    QgsProcessingAlgorithm <|-- EsriLandCoverRasterToVectorAlgorithm
    QgsProcessingParameterVectorDestination <|-- GeoJsonVectorDestination
    EsriLandCoverRasterToVectorAlgorithm ..> GeoJsonVectorDestination : output parameter
    EsriLandCoverRasterToVectorAlgorithm ..> SCHEMES : lookup, nodata, labels
    EsriLandCoverRasterToVectorAlgorithm ..> apply_symbology : when loading to canvas
```

### 5. Run sequence

```mermaid
sequenceDiagram
    actor U as User
    participant D as Processing dialog
    participant A as Algorithm
    participant G as GDAL and native algorithms
    participant C as QGIS canvas
    U->>D: choose raster, band, version, output
    D->>A: processAlgorithm(parameters)
    A->>G: gdal:polygonize
    G-->>A: polygons with gridcode
    A->>G: extractbyexpression (remove NoData)
    A->>G: dissolve by gridcode
    A->>A: fill class_en, hex_color, lulc_ver
    A->>G: savefeatures
    G-->>A: output path
    alt Load to canvas
        A->>C: add layer with categorized renderer
    end
    A-->>U: result and warnings
```

### 6. Data model

```mermaid
erDiagram
    SCHEME ||--|{ CLASS : defines
    SCHEME ||--o{ OUTPUT_LAYER : "sets lulc_ver"
    CLASS ||--o{ OUTPUT_LAYER : "fills class_en and hex_color"
    SCHEME {
        string label
        string version
        list nodata
    }
    CLASS {
        int pixel_value
        string class_name
        string hex
    }
    OUTPUT_LAYER {
        int gridcode
        string class_en
        string hex_color
        string lulc_ver
    }
```

## File Structure

```
Esri-Landcover-style-QGIS-Toolbox/
├── esri_landcover_style_qgis_toolbox.py   # Main Processing script
├── startup_esri_landcover.py              # Toolbar button (optional)
├── NOTICE.md
├── LICENSE
└── README.md
```

## Installation

1. Open the **Processing Toolbox** → click the **Python** icon → **Add Script to Toolbox...**
2. Select `esri_landcover_style_qgis_toolbox.py`. The tool appears under **Esri Land Cover Custom Visualization Toolbox**.
3. *(Optional, toolbar button)* — open your QGIS profile folder: `Settings → User Profiles → Open Active Profile Folder → python`.
   - No `startup.py` yet → copy `startup_esri_landcover.py` there and rename it to `startup.py`.
   - **You already have a `startup.py`** (e.g. from the MapBiomas toolbox) → **do not overwrite it**; paste the contents of `startup_esri_landcover.py` at the very bottom of the existing file. Both buttons can coexist.

## Usage

| Parameter | Description |
|---|---|
| Esri 10m Land Cover raster | Input raster layer |
| Band | Default Band 1 |
| **Esri Land Cover version & pixel-value scheme** | Pick one of the 4 options below, matching where your raster came from |
| Output vector polygons | Save location (default GeoJSON) |
| Load to canvas | Tick to display the result immediately with symbology |

### Version / scheme options

| Option | Use when | NoData removed |
|---|---|---|
| 2017–2025 (9 classes) — **Remapped 1–9** | Raster already remapped to 1–9, e.g. exported from GEE after applying `remap([1,2,4,5,7,8,9,10,11], [1,2,3,4,5,6,7,8,9])` | 0 |
| 2017–2025 (9 classes) — **Original 1,2,4,5,7,8,9,10,11** | Official GeoTIFF from Esri / Impact Observatory, or the raw `ESRI_Global-LULC_10m_TS` asset exported without remapping | 0 |
| 2020 (10 classes) — **GEE catalog (1–11)** | Raster from the GEE catalog `ESRI_Global-LULC_10m` (value 1 = No Data) | 0 and 1 |
| 2020 (10 classes) — **Original 1–10** | Official Esri 2020 GeoTIFF | 0 |

> **Do not pick the wrong scheme.** The same number can mean different classes across schemes (e.g. value 4 = *Flooded Vegetation* in 9-class Original, but *Crops* in 9-class Remapped and *Grass* in 2020 GEE). If a "Gridcodes not recognized" warning appears, the version is almost certainly mismatched.

## Classes & Colors

### 2017–2025, 9 classes — Remapped 1–9
| Pixel value | Land Cover Class | Hex | Color |
|:---:|---|:---:|:---:|
| 1 | Water | `#1A5BAB` | ![](https://img.shields.io/badge/■-1A5BAB?style=flat&color=1A5BAB) |
| 2 | Trees | `#358221` | ![](https://img.shields.io/badge/■-358221?style=flat&color=358221) |
| 3 | Flooded Vegetation | `#87D19E` | ![](https://img.shields.io/badge/■-87D19E?style=flat&color=87D19E) |
| 4 | Crops | `#FFDB5C` | ![](https://img.shields.io/badge/■-FFDB5C?style=flat&color=FFDB5C) |
| 5 | Built Area | `#ED022A` | ![](https://img.shields.io/badge/■-ED022A?style=flat&color=ED022A) |
| 6 | Bare Ground | `#EDE9E4` | ![](https://img.shields.io/badge/■-EDE9E4?style=flat&color=EDE9E4) |
| 7 | Snow/Ice | `#F2FAFF` | ![](https://img.shields.io/badge/■-F2FAFF?style=flat&color=F2FAFF) |
| 8 | Clouds | `#C8C8C8` | ![](https://img.shields.io/badge/■-C8C8C8?style=flat&color=C8C8C8) |
| 9 | Rangeland | `#C6AD8D` | ![](https://img.shields.io/badge/■-C6AD8D?style=flat&color=C6AD8D) |

### 2017–2025, 9 classes — Original
| Pixel value | Land Cover Class | Hex | Color |
|:---:|---|:---:|:---:|
| 1 | Water | `#1A5BAB` | ![](https://img.shields.io/badge/■-1A5BAB?style=flat&color=1A5BAB) |
| 2 | Trees | `#358221` | ![](https://img.shields.io/badge/■-358221?style=flat&color=358221) |
| 4 | Flooded Vegetation | `#87D19E` | ![](https://img.shields.io/badge/■-87D19E?style=flat&color=87D19E) |
| 5 | Crops | `#FFDB5C` | ![](https://img.shields.io/badge/■-FFDB5C?style=flat&color=FFDB5C) |
| 7 | Built Area | `#ED022A` | ![](https://img.shields.io/badge/■-ED022A?style=flat&color=ED022A) |
| 8 | Bare Ground | `#EDE9E4` | ![](https://img.shields.io/badge/■-EDE9E4?style=flat&color=EDE9E4) |
| 9 | Snow/Ice | `#F2FAFF` | ![](https://img.shields.io/badge/■-F2FAFF?style=flat&color=F2FAFF) |
| 10 | Clouds | `#C8C8C8` | ![](https://img.shields.io/badge/■-C8C8C8?style=flat&color=C8C8C8) |
| 11 | Rangeland | `#C6AD8D` | ![](https://img.shields.io/badge/■-C6AD8D?style=flat&color=C6AD8D) |

### 2020, 10 classes — GEE catalog (value 1 = No Data, removed)
| Pixel value | Land Cover Class | Hex | Color |
|:---:|---|:---:|:---:|
| 2 | Water | `#1A5BAB` | ![](https://img.shields.io/badge/■-1A5BAB?style=flat&color=1A5BAB) |
| 3 | Trees | `#358221` | ![](https://img.shields.io/badge/■-358221?style=flat&color=358221) |
| 4 | Grass | `#A7D282` | ![](https://img.shields.io/badge/■-A7D282?style=flat&color=A7D282) |
| 5 | Flooded Vegetation | `#87D19E` | ![](https://img.shields.io/badge/■-87D19E?style=flat&color=87D19E) |
| 6 | Crops | `#FFDB5C` | ![](https://img.shields.io/badge/■-FFDB5C?style=flat&color=FFDB5C) |
| 7 | Scrub/Shrub | `#EECFA8` | ![](https://img.shields.io/badge/■-EECFA8?style=flat&color=EECFA8) |
| 8 | Built Area | `#ED022A` | ![](https://img.shields.io/badge/■-ED022A?style=flat&color=ED022A) |
| 9 | Bare Ground | `#EDE9E4` | ![](https://img.shields.io/badge/■-EDE9E4?style=flat&color=EDE9E4) |
| 10 | Snow/Ice | `#F2FAFF` | ![](https://img.shields.io/badge/■-F2FAFF?style=flat&color=F2FAFF) |
| 11 | Clouds | `#C8C8C8` | ![](https://img.shields.io/badge/■-C8C8C8?style=flat&color=C8C8C8) |

### 2020, 10 classes — Original
| Pixel value | Land Cover Class | Hex | Color |
|:---:|---|:---:|:---:|
| 1 | Water | `#1A5BAB` | ![](https://img.shields.io/badge/■-1A5BAB?style=flat&color=1A5BAB) |
| 2 | Trees | `#358221` | ![](https://img.shields.io/badge/■-358221?style=flat&color=358221) |
| 3 | Grass | `#A7D282` | ![](https://img.shields.io/badge/■-A7D282?style=flat&color=A7D282) |
| 4 | Flooded Vegetation | `#87D19E` | ![](https://img.shields.io/badge/■-87D19E?style=flat&color=87D19E) |
| 5 | Crops | `#FFDB5C` | ![](https://img.shields.io/badge/■-FFDB5C?style=flat&color=FFDB5C) |
| 6 | Scrub/Shrub | `#EECFA8` | ![](https://img.shields.io/badge/■-EECFA8?style=flat&color=EECFA8) |
| 7 | Built Area | `#ED022A` | ![](https://img.shields.io/badge/■-ED022A?style=flat&color=ED022A) |
| 8 | Bare Ground | `#EDE9E4` | ![](https://img.shields.io/badge/■-EDE9E4?style=flat&color=EDE9E4) |
| 9 | Snow/Ice | `#F2FAFF` | ![](https://img.shields.io/badge/■-F2FAFF?style=flat&color=F2FAFF) |
| 10 | Clouds | `#C8C8C8` | ![](https://img.shields.io/badge/■-C8C8C8?style=flat&color=C8C8C8) |

Sources: [S2TSLULC](https://gee-community-catalog.org/projects/S2TSLULC/#class-definitions) and [esrilc2020](https://gee-community-catalog.org/projects/esrilc2020/#class-definitions). The Original 2020 numbering (1–10) follows the official class order on the esrilc2020 page.

## Output Attributes

| Field | Description |
|---|---|
| `gridcode` | Pixel value from the raster (polygonize result) |
| `class_en` | Class name (English) |
| `hex_color` | Hex color code |
| `lulc_ver` | Version & scheme selected when running the tool |

## Performance Tips

Esri 10 m rasters are very detailed. For large areas, **clip the raster to your study area first** before running the tool (polygonizing a large raster can be very slow and produce huge files).

## Requirements

QGIS 3.x with GDAL (included in the standard QGIS installation).

## Author

**Defani Arman Alfitriansyah** — [github.com/Defani](https://github.com/Defani)

## License

Code: MIT (see `LICENSE`). Data: CC BY 4.0, © Esri / Impact Observatory (see `NOTICE.md`).

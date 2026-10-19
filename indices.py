"""GaiaScope · indices.py — the index menu 🌈
Only data here, like events.py. Each equation is written ONCE with generic band
names; SENSORS translates them for each satellite.
To add an index: copy one block, change the name, formula, colours and text.
"""

# ---------- Satellites: generic band name → real band name ----------
SENSORS = {
    "Sentinel-2": {"BLUE": "B2", "GREEN": "B3", "RED": "B4",
                   "NIR": "B8", "SWIR1": "B11", "SWIR2": "B12"},
    "Landsat 8":  {"BLUE": "SR_B2", "GREEN": "SR_B3", "RED": "SR_B4",
                   "NIR": "SR_B5", "SWIR1": "SR_B6", "SWIR2": "SR_B7"},
    "Landsat 9":  {"BLUE": "SR_B2", "GREEN": "SR_B3", "RED": "SR_B4",
                   "NIR": "SR_B5", "SWIR1": "SR_B6", "SWIR2": "SR_B7"},
}

SENSOR_INFO = {
    "Sentinel-2": "Copernicus Sentinel-2 Level-2A · 10–20 m · every ~5 days · from 2017",
    "Landsat 8":  "USGS Landsat 8 Collection 2 Level-2 · 30 m · every 16 days · from 2013",
    "Landsat 9":  "USGS Landsat 9 Collection 2 Level-2 · 30 m · every 16 days · from late 2021",
}

# ---------- Colour ramps ----------
VEG   = ["#A50026", "#F46D43", "#FEE08B", "#D9EF8B", "#66BD63", "#006837"]
WATER = ["#8C510A", "#D8B365", "#F6E8C3", "#C7EAE5", "#5AB4AC", "#01665E", "#08306B"]
DRY   = ["#08306B", "#4292C6", "#C6DBEF", "#FEE0B6", "#E08214", "#7F3B08"]
BURN  = ["#1A9850", "#91CF60", "#FFFFBF", "#FC8D59", "#D73027", "#67001F"]
URBAN = ["#1A9850", "#D9EF8B", "#FFFFBF", "#FDAE61", "#D7191C", "#4D0000"]
SNOW  = ["#543005", "#BF812D", "#F6E8C3", "#E0F3F8", "#91BFDB", "#FFFFFF"]

# ---------- The indices ----------
INDICES = {
    "NDVI": {
        "name": "Normalized Difference Vegetation Index",
        "formula": "(NIR - RED) / (NIR + RED)",
        "min": -0.2, "max": 0.9, "palette": VEG,
        "about": "Healthy leaves reflect a lot of near-infrared light and absorb red light. "
                 "The more green vegetation, the higher the NDVI.",
        "reading": ["< 0: water, snow, clouds",
                    "0 – 0.2: bare soil, rock, built-up",
                    "0.2 – 0.5: sparse vegetation, crops, shrubs",
                    "> 0.5: dense, healthy vegetation"],
        "reference": "Rouse, J. W. et al. (1974). Monitoring vegetation systems in the Great Plains with ERTS. NASA SP-351.",
    },
    "EVI": {
        "name": "Enhanced Vegetation Index",
        "formula": "2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)",
        "min": -0.2, "max": 0.8, "palette": VEG,
        "about": "Like NDVI, but corrects for haze and soil background, and does not saturate "
                 "as quickly over dense forest.",
        "reading": ["< 0.1: no vegetation",
                    "0.1 – 0.3: sparse vegetation",
                    "> 0.3: dense vegetation"],
        "reference": "Huete, A. et al. (2002). Overview of the radiometric and biophysical performance "
                     "of the MODIS vegetation indices. Remote Sensing of Environment, 83, 195–213.",
    },
    "SAVI": {
        "name": "Soil Adjusted Vegetation Index",
        "formula": "1.5 * (NIR - RED) / (NIR + RED + 0.5)",
        "min": -0.2, "max": 0.8, "palette": VEG,
        "about": "NDVI with a soil correction factor (L = 0.5). Better where vegetation is sparse "
                 "and bright soil shows through, as in many Mediterranean areas.",
        "reading": ["< 0.1: bare soil",
                    "0.1 – 0.3: sparse vegetation",
                    "> 0.3: denser vegetation"],
        "reference": "Huete, A. R. (1988). A soil-adjusted vegetation index (SAVI). "
                     "Remote Sensing of Environment, 25, 295–309.",
    },
    "NDWI": {
        "name": "Normalized Difference Water Index",
        "formula": "(GREEN - NIR) / (GREEN + NIR)",
        "min": -0.6, "max": 0.6, "palette": WATER,
        "about": "Water reflects green light but absorbs near-infrared. Highlights open water "
                 "and suppresses vegetation.",
        "reading": ["> 0: open water",
                    "< 0: land and vegetation"],
        "reference": "McFeeters, S. K. (1996). The use of the Normalized Difference Water Index (NDWI) "
                     "in the delineation of open water features. IJRS, 17(7), 1425–1432.",
    },
    "MNDWI": {
        "name": "Modified Normalized Difference Water Index",
        "formula": "(GREEN - SWIR1) / (GREEN + SWIR1)",
        "min": -0.6, "max": 0.8, "palette": WATER,
        "about": "Uses shortwave infrared instead of near-infrared, so built-up areas are not "
                 "confused with water. Good for water in and near towns.",
        "reading": ["> 0: open water",
                    "< 0: land, built-up, vegetation"],
        "reference": "Xu, H. (2006). Modification of normalised difference water index (NDWI) to enhance "
                     "open water features in remotely sensed imagery. IJRS, 27(14), 3025–3033.",
    },
    "NDMI": {
        "name": "Normalized Difference Moisture Index",
        "formula": "(NIR - SWIR1) / (NIR + SWIR1)",
        "min": -0.4, "max": 0.6, "palette": list(reversed(DRY)),
        "about": "Shortwave infrared is absorbed by water inside leaves. NDMI tracks the water "
                 "content of vegetation, useful for drought and fire risk.",
        "reading": ["< 0: dry vegetation or bare soil",
                    "0 – 0.3: moderate canopy water",
                    "> 0.3: high canopy water"],
        "reference": "Wilson, E. H. & Sader, S. A. (2002). Detection of forest harvest type using multiple "
                     "dates of Landsat TM imagery. Remote Sensing of Environment, 80, 385–396. "
                     "(Concept: Gao, B. (1996), Remote Sensing of Environment, 58, 257–266.)",
    },
    "NBR": {
        "name": "Normalized Burn Ratio",
        "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
        "min": -0.5, "max": 0.8, "palette": list(reversed(BURN)),
        "about": "Healthy vegetation is bright in near-infrared and dark in SWIR2; burnt areas are "
                 "the opposite. The index behind BurnScope's dNBR.",
        "reading": ["< 0.1: burnt or bare",
                    "0.1 – 0.3: sparse or stressed vegetation",
                    "> 0.3: healthy vegetation"],
        "reference": "Key, C. H. & Benson, N. C. (2006). Landscape Assessment (LA). "
                     "USDA Forest Service, RMRS-GTR-164-CD.",
    },
    "NDBI": {
        "name": "Normalized Difference Built-up Index",
        "formula": "(SWIR1 - NIR) / (SWIR1 + NIR)",
        "min": -0.5, "max": 0.4, "palette": URBAN,
        "about": "Roofs, roads and bare surfaces reflect more shortwave infrared than near-infrared. "
                 "Highlights built-up land.",
        "reading": ["> 0: built-up or bare land",
                    "< 0: vegetation and water"],
        "reference": "Zha, Y., Gao, J. & Ni, S. (2003). Use of normalized difference built-up index in "
                     "automatically mapping urban areas from TM imagery. IJRS, 24(3), 583–594.",
    },
    "NDSI": {
        "name": "Normalized Difference Snow Index",
        "formula": "(GREEN - SWIR1) / (GREEN + SWIR1)",
        "min": -0.4, "max": 1.0, "palette": SNOW,
        "about": "Snow is bright in green light and dark in shortwave infrared. Same equation as "
                 "MNDWI, read for snow instead of water.",
        "reading": ["> 0.4: snow (commonly used threshold)",
                    "< 0.4: no snow"],
        "reference": "Hall, D. K., Riggs, G. A. & Salomonson, V. V. (1995). Development of methods for "
                     "mapping global snow cover using MODIS data. Remote Sensing of Environment, 54, 127–140.",
    },
    "BSI": {
        "name": "Bare Soil Index",
        "formula": "((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))",
        "min": -0.4, "max": 0.4,         "palette": ["#1A9850", "#91CF60", "#D9EF8B", "#FEE08B", "#D8B365", "#8C510A"],
        "about": "Combines four bands to separate bare soil from vegetation. High values show "
                 "exposed soil, e.g. ploughed fields, quarries or burnt land.",
        "reading": ["> 0: bare soil",
                    "< 0: vegetation"],
        "reference": "Rikimaru, A., Roy, P. S. & Miyatake, S. (2002). Tropical forest cover density mapping. "
                     "Tropical Ecology, 43(1), 39–47.",
    },
}

# ---------- More basic indices (same 6 bands) ----------
INDICES.update({
    "GNDVI": {
        "name": "Green Normalized Difference Vegetation Index",
        "formula": "(NIR - GREEN) / (NIR + GREEN)",
        "min": -0.2, "max": 0.9, "palette": VEG,
        "about": "NDVI with the green band instead of red. More sensitive to chlorophyll "
                 "and keeps working where NDVI saturates in dense canopies.",
        "reading": ["< 0.2: little or no vegetation",
                    "0.2 – 0.5: moderate vegetation",
                    "> 0.5: dense, chlorophyll-rich vegetation"],
        "reference": "Gitelson, A. A., Kaufman, Y. J. & Merzlyak, M. N. (1996). Use of a green channel in "
                     "remote sensing of global vegetation from EOS-MODIS. Remote Sensing of Environment, 58, 289–298.",
    },
    "OSAVI": {
        "name": "Optimized Soil Adjusted Vegetation Index",
        "formula": "(NIR - RED) / (NIR + RED + 0.16)",
        "min": -0.2, "max": 0.8, "palette": VEG,
        "about": "A version of SAVI with a fixed soil factor (0.16) that works well for most soils "
                 "without knowing how much vegetation there is.",
        "reading": ["< 0.1: bare soil",
                    "0.1 – 0.3: sparse vegetation",
                    "> 0.3: denser vegetation"],
        "reference": "Rondeaux, G., Steven, M. & Baret, F. (1996). Optimization of soil-adjusted vegetation "
                     "indices. Remote Sensing of Environment, 55, 95–107.",
    },
    "MSAVI": {
        "name": "Modified Soil Adjusted Vegetation Index",
        "formula": "(2 * NIR + 1 - sqrt((2 * NIR + 1) ** 2 - 8 * (NIR - RED))) / 2",
        "min": -0.2, "max": 0.8, "palette": VEG,
        "about": "SAVI where the soil factor adjusts itself to the amount of vegetation. "
                 "Useful early in the growing season, when soil dominates.",
        "reading": ["< 0.2: bare soil",
                    "0.2 – 0.4: young crops, sparse vegetation",
                    "> 0.4: developed vegetation"],
        "reference": "Qi, J. et al. (1994). A modified soil adjusted vegetation index. "
                     "Remote Sensing of Environment, 48, 119–126.",
    },
    "ARVI": {
        "name": "Atmospherically Resistant Vegetation Index",
        "formula": "(NIR - (2 * RED - BLUE)) / (NIR + (2 * RED - BLUE))",
        "min": -0.2, "max": 0.9, "palette": VEG,
        "about": "Uses the blue band to correct red for haze and smoke. A good choice in hazy "
                 "air, for example during wildfire season.",
        "reading": ["< 0.2: little or no vegetation",
                    "0.2 – 0.5: moderate vegetation",
                    "> 0.5: dense vegetation"],
        "reference": "Kaufman, Y. J. & Tanré, D. (1992). Atmospherically resistant vegetation index (ARVI) "
                     "for EOS-MODIS. IEEE TGRS, 30(2), 261–270.",
    },
    "VARI": {
        "name": "Visible Atmospherically Resistant Index",
        "formula": "(GREEN - RED) / (GREEN + RED - BLUE)",
        "min": -0.3, "max": 0.4, "palette": VEG,
        "about": "Uses only visible bands, so it can also be computed from ordinary RGB "
                 "cameras and drones. Estimates the green fraction of the surface.",
        "reading": ["< 0: no vegetation",
                    "0 – 0.2: some vegetation",
                    "> 0.2: green vegetation"],
        "reference": "Gitelson, A. A. et al. (2002). Novel algorithms for remote estimation of vegetation "
                     "fraction. Remote Sensing of Environment, 80, 76–87.",
    },
    "NBR2": {
        "name": "Normalized Burn Ratio 2",
        "formula": "(SWIR1 - SWIR2) / (SWIR1 + SWIR2)",
        "min": -0.1, "max": 0.4, "palette": list(reversed(DRY)),
        "about": "Uses the two shortwave infrared bands. Sensitive to water in soil and vegetation, "
                 "and helps follow recovery after fire.",
        "reading": ["Lower: drier surfaces, fresh burns",
                    "Higher: moister soil and vegetation"],
        "reference": "USGS (2017). Landsat Surface Reflectance-Derived Spectral Indices. Product Guide.",
    },
})

# ---------- Order in the menu: grouped by theme ----------
ORDER = ["NDVI", "GNDVI", "EVI", "SAVI", "OSAVI", "MSAVI", "ARVI", "VARI",   # vegetation
         "NDWI", "MNDWI", "NDMI",                                              # water
         "NBR", "NBR2",                                                        # fire
         "NDBI", "BSI", "NDSI"]                                                # land and snow
INDICES = {key: INDICES[key] for key in ORDER}

SOURCES = ("Equations follow the [Index DataBase (IDB)](https://www.indexdatabase.de/db/i.php), "
           "[Awesome Spectral Indices](https://github.com/awesome-spectral-indices/awesome-spectral-indices) "
           "and the [USGS Landsat spectral indices](https://www.usgs.gov/landsat-missions/"
           "landsat-surface-reflectance-derived-spectral-indices). Only indices that use the six "
           "bands shared by Sentinel-2 and Landsat 8/9 are included.")

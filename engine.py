"""GaiaScope · engine.py — the kitchen 🔥
All the science: Earth Engine recipes, tables and charts.
No buttons, no maps. app.py asks, engine.py cooks.
ee.Initialize() must run BEFORE this file is imported (app.py does it).
"""
import ee
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")              # draw charts in memory, never open a window
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from indices import SENSORS, INDICES


# =====================================================================
# Part 1 · Shared: land cover, colours, tables, charts, helpers
# =====================================================================

# ---------- Land cover ----------
WORLDCOVER = ee.ImageCollection("ESA/WorldCover/v200").first()

CLASSES = {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
           50: "Built-up", 60: "Bare / sparse", 70: "Snow and ice",
           80: "Permanent water", 90: "Herbaceous wetland", 95: "Mangroves",
           100: "Moss and lichen"}

LC_COLORS = {10: "#006400", 20: "#FFBB22", 30: "#FFFF4C", 40: "#F096FF",
             50: "#FA0000", 60: "#B4B4B4", 70: "#F0F0F0", 80: "#0064C8",
             90: "#0096A0", 95: "#00CF75", 100: "#FAE6A0"}

NAME_COLORS = {CLASSES[k]: v for k, v in LC_COLORS.items()}

# ---------- Burn severity (USGS dNBR classes) ----------
SEVERITY   = {1: "Low", 2: "Moderate-low", 3: "Moderate-high", 4: "High"}
SEV_COLORS = ["#FFD54F", "#FF8F00", "#D84315", "#7F0000"]


# ---------- Tables ----------
def color_cell(name):
    c = NAME_COLORS.get(name)
    return f"border-left: 14px solid {c}; padding-left: 8px" if c else ""


def lc_table(groups):
    rows = [{"Land cover": CLASSES[g["class"]], "Area (km²)": g["sum"] / 1e6} for g in groups]
    df = pd.DataFrame(rows)
    df = df[df["Area (km²)"] >= 0.05]
    if df.empty:
        return None
    df = df.sort_values("Area (km²)", ascending=False).reset_index(drop=True)
    df["Share (%)"] = df["Area (km²)"] / df["Area (km²)"].sum() * 100
    df.loc[len(df)] = ["Total", df["Area (km²)"].sum(), 100.0]
    return (df.style.format(precision=1)
                    .hide(axis="index")
                    .map(color_cell, subset=["Land cover"]))


def severity_df(groups):
    rows = [{"Land cover": CLASSES[int(g["combo"]) // 10],
             "Severity":   SEVERITY[int(g["combo"]) % 10],
             "km²":        g["sum"] / 1e6} for g in groups]
    df = pd.DataFrame(rows).pivot_table(index="Land cover", columns="Severity",
                                        values="km²", aggfunc="sum", fill_value=0)
    df = df[[s for s in SEVERITY.values() if s in df.columns]]
    df = df[df.sum(axis=1) >= 0.05]
    return df.loc[df.sum(axis=1).sort_values().index]


# ---------- Charts ----------
INK = "#8A9A97"          # grey that reads on both dark and light backgrounds


def tidy(fig, ax):
    """Transparent background + grey text, so charts suit dark AND light mode."""
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color(INK)
    ax.tick_params(colors=INK)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    legend = ax.get_legend()
    if legend is not None:
        legend.get_title().set_color(INK)
        for text in legend.get_texts():
            text.set_color(INK)
    fig.tight_layout()
    plt.close(fig)
    return fig


def lc_chart(groups, xlabel="Area (km²)"):
    rows = [(CLASSES[g["class"]], g["sum"] / 1e6, LC_COLORS[g["class"]])
            for g in groups if g["sum"] / 1e6 >= 0.05]
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r[1])          # smallest at the bottom
    names, km2, colors = zip(*rows)                   # unzip into 3 tuples
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.barh(names, km2, color=colors, edgecolor=INK, linewidth=0.5)
    ax.set_xlabel(xlabel)
    return tidy(fig, ax)


def severity_chart(df):
    colors = [SEV_COLORS[list(SEVERITY.values()).index(c)] for c in df.columns]
    fig, ax = plt.subplots(figsize=(5, 3))
    df.plot(kind="barh", stacked=True, color=colors, ax=ax, width=0.7)
    ax.set_xlabel("Burnt area (km²)")
    ax.set_ylabel("")
    ax.legend(title="Severity", frameon=False, fontsize=8, title_fontsize=8)
    return tidy(fig, ax)


# ---------- Helpers ----------
def groups_by_class(combo_groups):
    """Turn land-cover × severity groups into per-class totals."""
    by_class = {}
    for g in combo_groups:
        c = int(g["combo"]) // 10
        by_class[c] = by_class.get(c, 0) + g["sum"]
    return [{"class": c, "sum": s} for c, s in by_class.items()]


def lc_groups(mask, aoi, scale):
    """Area (m²) of a mask per WorldCover class — one reduction."""
    return (ee.Image.pixelArea().updateMask(mask)
            .addBands(WORLDCOVER.clip(aoi).rename("lc"))
            .reduceRegion(reducer=ee.Reducer.sum().group(groupField=1, groupName="class"),
                          geometry=aoi, scale=scale, maxPixels=1e10)
            .get("groups")
            .getInfo())


def edge_km2(mask, geom, scale=100):
    ring = geom.difference(geom.buffer(-500, 10), 10)
    return (ee.Image.pixelArea().updateMask(mask)
            .reduceRegion(reducer=ee.Reducer.sum(), geometry=ring, scale=scale, maxPixels=1e10)
            .get("area"))


# =====================================================================
# Part 2 · 🔥 BurnScope
# =====================================================================
def s2_clear(img):
    """Hide clouds and shadows using the Scene Classification band (SCL)."""
    scl = img.select("SCL")
    clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.updateMask(clear)    # 3 shadow · 8, 9 cloud · 10 cirrus


def s2_composite(start, end, area, max_cloud=20):
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(area)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
            .map(s2_clear)
            .median()
            .clip(area))


def nbr(img):
    return img.normalizedDifference(["B8", "B12"]).rename("NBR")


def dnbr_images(geom, before_dates, after_dates):
    before = s2_composite(*before_dates, geom)
    after  = s2_composite(*after_dates, geom)
    dnbr   = nbr(before).subtract(nbr(after)).rename("dNBR")
    return before, after, dnbr


def burnt_mask(dnbr, geom, thr):
    land = WORLDCOVER.clip(geom).neq(80)
    return dnbr.gt(thr).And(land).rename("burnt")


def fit_area(geom, before_dates, after_dates, thr, tries=4, step=5000):
    """Grow the box until the burn scar no longer touches its edge."""
    for i in range(tries):
        _, _, dnbr = dnbr_images(geom, before_dates, after_dates)
        touching = ee.Number(edge_km2(burnt_mask(dnbr, geom, thr), geom)).getInfo() or 0
        if touching < 1e5:                       # less than 0.1 km² on the edge
            return geom, i
        geom = geom.buffer(step, 10).bounds(10)
    return geom, tries


def burnscope(aoi, before_dates, after_dates, threshold=0.27):
    # 1. Images and dNBR
    before, after, dnbr = dnbr_images(aoi, before_dates, after_dates)

    # 2. Burnt mask (land only) and severity classes
    lc    = WORLDCOVER.clip(aoi)
    burnt = burnt_mask(dnbr, aoi, threshold)
    sev   = (ee.Image(1).where(dnbr.gte(0.27), 2)
                        .where(dnbr.gte(0.44), 3)
                        .where(dnbr.gte(0.66), 4)
                        .updateMask(burnt).rename("severity"))

    # 3. Numbers: ONE reduction (land cover × severity)
    area  = ee.Image.pixelArea().updateMask(burnt)
    combo = lc.toInt().multiply(10).add(sev).rename("combo")
    sev_groups = (area.addBands(combo)
                  .reduceRegion(reducer=ee.Reducer.sum().group(groupField=1, groupName="combo"),
                                geometry=aoi, scale=20, maxPixels=1e10)
                  .get("groups")
                  .getInfo())

    # 4. Per-class totals and grand total, in Python (instant)
    groups = groups_by_class(sev_groups)
    total  = sum(g["sum"] for g in groups)

    return {"before": before, "after": after, "dnbr": dnbr, "burnt": burnt, "severity": sev,
            "km2": total / 1e6,
            "groups": groups,
            "table": lc_table(groups) if groups else None,
            "sev_df": severity_df(sev_groups) if sev_groups else None}


# =====================================================================
# Part 3 · 🌊 FloodScope (Sentinel-1 radar, VV)
# =====================================================================
def s1_collection(aoi, start, end):
    return (ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .select("VV"))


def floodscope(aoi, before_dates, after_dates, vv_thr=-17):
    col_b = s1_collection(aoi, *before_dates)
    col_a = s1_collection(aoi, *after_dates)
    n_before = col_b.size().getInfo()
    n_after  = col_a.size().getInfo()
    if n_before == 0 or n_after == 0:
        raise ValueError(f"Not enough radar images (before: {n_before}, after: {n_after}). "
                         "Try wider dates.")

    # Median per period + speckle filter (50 m)
    before = col_b.median().focalMedian(50, "circle", "meters").clip(aoi)
    after  = col_a.median().focalMedian(50, "circle", "meters").clip(aoi)

    # Change detection: dark AFTER, not dark BEFORE, and not permanent water
    land = WORLDCOVER.clip(aoi).neq(80)
    mask = (after.lt(vv_thr)
            .And(before.lt(vv_thr).Not())
            .And(land)
            .selfMask()
            .rename("flood"))

    groups = lc_groups(mask, aoi, scale=20)
    total  = sum(g["sum"] for g in groups)

    return {"before": before, "after": after, "mask": mask,
            "km2": total / 1e6,
            "groups": groups,
            "table": lc_table(groups) if groups else None,
            "n_before": n_before, "n_after": n_after}


# =====================================================================
# Part 4 · ☀️ DroughtScope (Landsat 8+9, Ts/VI triangle → TVDI)
# =====================================================================
def landsat_prep(img):
    qa = img.select("QA_PIXEL")
    clear = (qa.bitwiseAnd(1 << 1).eq(0)          # dilated cloud
             .And(qa.bitwiseAnd(1 << 3).eq(0))     # cloud
             .And(qa.bitwiseAnd(1 << 4).eq(0))     # cloud shadow
             .And(qa.bitwiseAnd(1 << 5).eq(0)))    # snow
    sr   = img.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5"]).multiply(0.0000275).add(-0.2)
    ts   = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("Ts")
    ndvi = sr.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
    return ee.Image(sr.addBands([ndvi, ts]).updateMask(clear)
                    .copyProperties(img, ["system:time_start"]))


def landsat_collection(aoi, start, end, max_cloud=60):
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (l8.merge(l9)
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUD_COVER", max_cloud))
            .map(landsat_prep))


def triangle_chart(r):
    fig, ax = plt.subplots(figsize=(5, 3.4))
    ax.scatter(r["sample_ts"], r["sample_ndvi"], s=3, alpha=0.35, color=INK)
    ndvi_line = np.linspace(0.15, max(r["sample_ndvi"] or [0.8]), 50)
    ax.plot(r["a"] + r["b"] * ndvi_line, ndvi_line, color="#C2410C", lw=2, label="Dry edge")
    ax.axvline(r["ts_min"], color="#0064C8", lw=2, ls="--", label="Wet edge")
    ax.set_xlabel("Land surface temperature Ts (°C)")
    ax.set_ylabel("NDVI")
    ax.legend(frameon=False, fontsize=8)
    return tidy(fig, ax)


def droughtscope(aoi, dates, tvdi_thr=0.7, bin_width=0.05, min_count=50):
    # 1. Clear-sky median composite
    col = landsat_collection(aoi, *dates)
    n = col.size().getInfo()
    if n == 0:
        raise ValueError("No Landsat scenes for these dates. Try a wider window.")
    image = col.median().clip(aoi)
    ndvi, ts = image.select("NDVI"), image.select("Ts")

    # 2. Ts statistics per NDVI bin (p1, p99, count) — one reduction
    bins = ndvi.divide(bin_width).floor().toInt().rename("bin")
    reducer = (ee.Reducer.percentile([1, 99])
               .combine(ee.Reducer.count(), sharedInputs=True)
               .group(groupField=1, groupName="bin"))
    stats = (ts.addBands(bins)
             .reduceRegion(reducer=reducer, geometry=aoi, scale=30,
                           maxPixels=1e10, tileScale=4)
             .get("groups")
             .getInfo())
    good = [g for g in stats if g.get("count", 0) >= min_count and g.get("p99") is not None]

    # 3. Dry edge: straight line through the hottest pixels (NDVI ≥ 0.15)
    fit = [g for g in good if g["bin"] * bin_width >= 0.15]
    if len(fit) < 3:
        raise ValueError("Too few NDVI bins to fit the dry edge. Try a bigger area or wider dates.")
    x = np.array([g["bin"] * bin_width + bin_width / 2 for g in fit])
    y = np.array([g["p99"] for g in fit])
    b, a = np.polyfit(x, y, 1)              # Ts_max = a + b · NDVI
    ts_min = min(g["p1"] for g in good)     # wet edge = coolest pixels

    # 4. TVDI = (Ts − Ts_min) / (Ts_max − Ts_min), clamped to 0–1
    ts_max = ndvi.multiply(b).add(a)
    tvdi = ts.subtract(ts_min).divide(ts_max.subtract(ts_min)).clamp(0, 1).rename("TVDI")

    # 5. Dry stress mask and numbers
    land = WORLDCOVER.clip(aoi).neq(80)
    dry  = tvdi.gte(tvdi_thr).And(land).selfMask().rename("dry")
    summary = (ee.Image.pixelArea().updateMask(tvdi.mask()).rename("valid").addBands(tvdi)
               .reduceRegion(reducer=ee.Reducer.sum().combine(ee.Reducer.mean(), sharedInputs=True),
                             geometry=aoi, scale=30, maxPixels=1e10, tileScale=4)
               .getInfo())
    groups = lc_groups(dry, aoi, scale=30)
    total  = sum(g["sum"] for g in groups)
    valid  = summary.get("valid_sum") or 1

    # 6. A sample of pixels for the triangle chart
    pts = (image.select(["NDVI", "Ts"])
           .sample(region=aoi, scale=30, numPixels=3000, seed=1)
           .reduceColumns(ee.Reducer.toList(2), ["NDVI", "Ts"])
           .get("list")
           .getInfo())

    return {"image": image, "tvdi": tvdi, "dry": dry, "n": n,
            "a": a, "b": b, "ts_min": ts_min,
            "sample_ndvi": [p[0] for p in pts], "sample_ts": [p[1] for p in pts],
            "mean_tvdi": summary.get("TVDI_mean"),
            "km2": total / 1e6,
            "share": total / valid * 100,
            "groups": groups,
            "table": lc_table(groups) if groups else None}


# =====================================================================
# Part 5 · 🌈 IndexScope (spectral indices from Sentinel-2 or Landsat)
# =====================================================================
GENERIC = ["BLUE", "GREEN", "RED", "NIR", "SWIR1", "SWIR2"]


def landsat_clear(img):
    """Hide dilated cloud (bit 1), cloud (3), shadow (4) and snow (5)."""
    qa = img.select("QA_PIXEL")
    return img.updateMask(qa.bitwiseAnd(0b111010).eq(0))


def sensor_collection(sensor, aoi, start, end, max_cloud=40):
    """Cloud-free images, in reflectance (0–1), with GENERIC band names."""
    real = [SENSORS[sensor][b] for b in GENERIC]
    if sensor == "Sentinel-2":
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
               .filterBounds(aoi).filterDate(start, end)
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
               .map(s2_clear))
        return col.map(lambda img: img.select(real, GENERIC).divide(10000))
    collection_id = {"Landsat 8": "LANDSAT/LC08/C02/T1_L2",
                     "Landsat 9": "LANDSAT/LC09/C02/T1_L2"}[sensor]
    col = (ee.ImageCollection(collection_id)
           .filterBounds(aoi).filterDate(start, end)
           .filter(ee.Filter.lt("CLOUD_COVER", max_cloud))
           .map(landsat_clear))
    return col.map(lambda img: img.select(real, GENERIC).multiply(0.0000275).add(-0.2))


def pick(stats, suffix):
    """Find a value in a reduceRegion result by the end of its name (e.g. '_mean')."""
    return next((v for k, v in stats.items() if k.endswith(suffix)), None)


def index_histogram(values, spec, name):
    cmap = mcolors.LinearSegmentedColormap.from_list("index", spec["palette"])
    lo, hi = spec["min"], spec["max"]
    fig, ax = plt.subplots(figsize=(5, 3))
    _, bins, patches = ax.hist(np.clip(values, lo, hi), bins=40, range=(lo, hi))
    for patch, left in zip(patches, bins[:-1]):
        patch.set_facecolor(cmap((left - lo) / (hi - lo)))   # each bar in its map colour
    ax.set_xlabel(name)
    ax.set_ylabel("Pixels (sample)")
    return tidy(fig, ax)


def indexscope(aoi, sensor, index, start, end):
    # 1. Cloud-free median composite
    col = sensor_collection(sensor, aoi, start, end)
    n = col.size().getInfo()
    if n == 0:
        raise ValueError(f"No clear {sensor} images for these dates. Try a wider window.")
    img = col.median().clip(aoi)

    # 2. The index: the same equation for every satellite
    spec = INDICES[index]
    idx = img.expression(spec["formula"], {b: img.select(b) for b in GENERIC}).rename(index)

    # 3. Numbers: mean and percentiles in ONE reduction, plus a sample for the histogram
    uses_swir = "SWIR" in spec["formula"]                  # SWIR bands are 20 m on Sentinel-2
    if sensor == "Sentinel-2":
        scale = 20 if uses_swir else 10
    else:
        scale = 30                                          # Landsat: all bands 30 m
    reducer = ee.Reducer.mean().combine(ee.Reducer.percentile([5, 50, 95]), sharedInputs=True)
    stats = idx.reduceRegion(reducer=reducer, geometry=aoi, scale=scale,
                             maxPixels=1e10, tileScale=4).getInfo()
    values = (idx.sample(region=aoi, scale=scale, numPixels=5000, seed=1)
              .aggregate_array(index).getInfo())

    return {"image": img, "index": idx, "n": n, "scale": scale,
            "mean": pick(stats, "_mean"), "p5": pick(stats, "_p5"),
            "p50": pick(stats, "_p50"), "p95": pick(stats, "_p95"),
            "values": values}

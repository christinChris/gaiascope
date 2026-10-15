"""GaiaScope · app.py — the dining room 🍽️
Buttons, sliders, maps and tabs. It never cooks: it asks engine.py.
Run with:   solara run app.py      → open http://localhost:8765
"""
import os
import math
import threading
import ee

# 🔥 Oven first: Earth Engine must be on BEFORE the kitchen is imported
ee.Initialize(project=os.environ.get("EE_PROJECT", "ee-christilekka"))

import solara
import geemap
import ipyleaflet

import engine as eng
from events import FIRE_EVENTS, FLOOD_EVENTS
from indices import SENSORS, SENSOR_INFO, INDICES, SOURCES


# =====================================================================
# Part 1 · Shared look: basemaps and colours
# =====================================================================
BASEMAPS = {
    "Google satellite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    "Google map":       "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "Google terrain":   "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
}
OUTLINE     = {"shapeOptions": {"color": "#FFFFFF", "weight": 2, "fillOpacity": 0}}
S2_TRUE     = {"bands": ["B4", "B3", "B2"],  "min": 0, "max": 3000}
S2_FALSE    = {"bands": ["B12", "B8", "B4"], "min": 0, "max": 3000}
SEV_VIS     = {"min": 1, "max": 4, "palette": eng.SEV_COLORS}
RADAR_VIS   = {"min": -25, "max": 0}
FLOOD_COLOR = "#00B4FF"
L_TRUE      = {"bands": ["SR_B4", "SR_B3", "SR_B2"], "min": 0, "max": 0.3}
TVDI_VIS    = {"min": 0, "max": 1, "palette": ["#1A9850", "#FEE08B", "#D73027"]}
SEV_LEGEND  = {"Low (0.10–0.27)":           eng.SEV_COLORS[0],
               "Moderate-low (0.27–0.44)":  eng.SEV_COLORS[1],
               "Moderate-high (0.44–0.66)": eng.SEV_COLORS[2],
               "High (> 0.66)":             eng.SEV_COLORS[3]}


# =====================================================================
# Part 2 · Shared helpers (written once, used by all three modules)
# =====================================================================
def new_map(center, zoom):
    """A fresh map: Google basemap, white outline-only drawing tools."""
    m = geemap.Map(center=center, zoom=zoom, height="600px", toolbar_ctrl=False)
    m.draw_control.rectangle = OUTLINE
    m.draw_control.polygon = OUTLINE
    base = m.layers[0]                      # the OSM layer → turn it into Google
    base.url = BASEMAPS["Google satellite"]
    base.name = "Basemap"
    base.attribution = "Imagery © Google"
    m.add_control(ipyleaflet.LayersControl(position="topright"))   # layer on/off panel
    return m, base


def add_swipe(m, left_img, left_vis, right_img, right_vis, left_name="Before", right_name="After"):
    """Layers FIRST, then the swipe (the Colab lesson!)."""
    left  = geemap.ee_tile_layer(left_img, left_vis, left_name)
    right = geemap.ee_tile_layer(right_img, right_vis, right_name)
    m.add_layer(left)
    m.add_layer(right)
    m.add_control(ipyleaflet.SplitMapControl(left_layer=left, right_layer=right))


def add_outline(m, geom):
    """White outline of the study area, no fill."""
    line = ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(geom)]), 1, 2)
    m.addLayer(line, {"palette": ["FFFFFF"]}, "Study area")


def use_drawn_area(m, area):
    """If the user drew a box, copy it into `area` and clear the drawing."""
    roi = m.user_roi
    if roi is None:
        return False
    area.value = roi
    m.draw_control.clear()
    return True


def date_inputs(label, start, end):
    solara.Text(label, style={"font-weight": "600"})
    with solara.Row():
        solara.InputText("Start", value=start)
        solara.InputText("End", value=end)


def event_info(ev):
    solara.Markdown(f"{ev['info']}\n\n[Source ↗]({ev['source']})")


def show_table(styler):
    if styler is not None:
        solara.HTML(tag="div", unsafe_innerHTML=styler.to_html(), classes=["gaia-table"])


def map_or_stats(m, view, headline, show_stats):
    """One panel, two views: the map, or the statistics of the last result."""
    if headline:
        with solara.Row(style={"align-items": "center", "gap": "24px"}):
            solara.ToggleButtonsSingle(value=view, values=["Map", "Statistics"])
            solara.Markdown(f"### {headline}")
    if headline and view.value == "Statistics":
        show_stats()
    else:
        solara.display(m)


def show_status(text):
    if text:
        solara.Markdown(text)


def box_of(geom):
    """[west, south, east, north] of a geometry (asks Earth Engine once)."""
    ring = geom.bounds(10).coordinates().getInfo()[0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return [min(xs), min(ys), max(xs), max(ys)]


def fit_view(m, box):
    """Centre and zoom the map on a box, without asking the browser."""
    w, s, e, n = box
    m.center = ((s + n) / 2, (w + e) / 2)
    span = max(e - w, (n - s) * 1.5, 0.01)          # degrees to show
    m.zoom = max(3, min(15, int(math.log2(1100 / span))))


def in_background(status, job, *args):
    """Run slow Earth Engine work in its own thread, so the page stays alive."""
    status.value = "⏳ Working… (big areas or long periods can take a few minutes)"
    threading.Thread(target=job, args=args, daemon=True).start()


def busy(status):
    return status.value.startswith("⏳")


def event_box(ev, km=3):
    """Event bbox + a small buffer so the scar is not cut at the edge."""
    return ee.Geometry.Rectangle(ev["bbox"]).buffer(km * 1000, 10).bounds(10)




# =====================================================================
# Part 3 · 🔥 BurnScope
# =====================================================================
b_mode     = solara.reactive("Map your own")
b_event    = solara.reactive(list(FIRE_EVENTS)[-1])
b_b_start  = solara.reactive("2024-07-20")
b_b_end    = solara.reactive("2024-08-10")
b_a_start  = solara.reactive("2024-08-15")
b_a_end    = solara.reactive("2024-09-05")
b_thr      = solara.reactive(0.27)
b_area     = solara.reactive(ee.Geometry.Rectangle([23.75, 37.98, 24.10, 38.32]))
b_result   = solara.reactive(None)
b_status   = solara.reactive("")
b_basemap  = solara.reactive("Google satellite")
b_show     = solara.reactive(True)
b_version  = solara.reactive(0)        # +1 → a fresh map is built
b_view     = solara.reactive("Map")    # "Map" or "Statistics"


def burn_map():
    """Build a FRESH map, with the latest result already on it."""
    m, base = new_map(center=(38.15, 23.92), zoom=10)
    base.url = BASEMAPS[b_basemap.value]
    m.add_legend(title="Burn severity (dNBR)", legend_dict=SEV_LEGEND, position="bottomright")
    r = b_result.value
    if r is not None:
        if r["event"]:                                   # events: just the scar
            m.addLayer(r["severity"], SEV_VIS, "Burn severity")
        else:                                            # your own: swipe
            right = r["after"].visualize(**S2_FALSE)
            if b_show.value:
                right = right.blend(r["severity"].visualize(**SEV_VIS))
            add_swipe(m, r["before"], S2_TRUE, right, {},
                      "Before · true color", "After · false color + burnt")
        add_outline(m, r["area"])
        fit_view(m, r["box"])
    return m, base


@solara.component
def BurnScope():
    m, base = solara.use_memo(burn_map, [b_version.value, b_show.value])

    def run(geom, before_dates, after_dates, event):
        try:
            grown = 0
            if not event:                                # event boxes are already sized
                geom, grown = eng.fit_area(geom, before_dates, after_dates, b_thr.value, tries=2)
            r = eng.burnscope(geom, before_dates, after_dates, b_thr.value)
            r["area"], r["event"] = geom, event
            r["box"] = box_of(geom)
            sev = r["sev_df"]
            r["chart"] = eng.severity_chart(sev) if sev is not None and not sev.empty else None
            b_result.value = r
            b_view.value = "Map"
            b_version.value += 1                         # → fresh map
            if grown == 2:
                b_status.value = "⚠️ The burn scar still touches the edge. Try drawing a bigger box."
            elif grown > 0:
                b_status.value = f"✅ Done. The box grew {grown}× to fit the whole scar."
            else:
                b_status.value = "✅ Done."
        except Exception as e:
            b_status.value = f"⚠️ {e}"

    def analyze():
        use_drawn_area(m, b_area)
        in_background(b_status, run, b_area.value, (b_b_start.value, b_b_end.value),
                      (b_a_start.value, b_a_end.value), False)

    def load_event():
        ev = FIRE_EVENTS[b_event.value]
        in_background(b_status, run, event_box(ev), ev["before"], ev["after"], True)

    def clear_area():
        b_result.value = None
        b_status.value = ""
        b_version.value += 1

    def set_basemap(name):
        b_basemap.value = name
        base.url = BASEMAPS[name]

    with solara.Columns([1, 3]):
        # ---------- Left: controls ----------
        with solara.Column():
            solara.ToggleButtonsSingle(value=b_mode, values=["Map your own", "Major events"])
            if b_mode.value == "Major events":
                solara.Select("Event", value=b_event, values=list(FIRE_EVENTS))
                event_info(FIRE_EVENTS[b_event.value])
                solara.Button("Show burn scar", on_click=load_event, color="#C2410C",
                              disabled=busy(b_status))
            else:
                solara.Text("Draw a box on the map (■ tool), or keep the default area.")
                date_inputs("Before", b_b_start, b_b_end)
                date_inputs("After", b_a_start, b_a_end)
                solara.SliderFloat("dNBR threshold", value=b_thr, min=0.10, max=0.66, step=0.01)
                solara.Checkbox(label="Show burnt area on the after side", value=b_show)
                with solara.Row():
                    solara.Button("Map burnt area", on_click=analyze, color="#C2410C",
                                  disabled=busy(b_status))
                    solara.Button("Clear", on_click=clear_area, outlined=True)
            solara.Select("Basemap", value=b_basemap.value, values=list(BASEMAPS),
                          on_value=set_basemap)
            show_status(b_status.value)

        # ---------- Right: map or statistics ----------
        r = b_result.value

        def stats():
            with solara.Columns([1, 1]):
                with solara.Column():
                    show_table(r["table"])
                with solara.Column():
                    if r["chart"] is not None:
                        solara.FigureMatplotlib(r["chart"])

        with solara.Column():
            headline = f"{r['km2']:.1f} km² burnt" if r else ""
            map_or_stats(m, b_view, headline, stats)


# =====================================================================
# Part 4 · 🌊 FloodScope
# =====================================================================
f_mode     = solara.reactive("Map your own")
f_event    = solara.reactive(list(FLOOD_EVENTS)[-1])
f_b_start  = solara.reactive("2023-08-01")
f_b_end    = solara.reactive("2023-08-31")
f_a_start  = solara.reactive("2023-09-07")
f_a_end    = solara.reactive("2023-09-15")
f_thr      = solara.reactive(-17.0)
f_area     = solara.reactive(ee.Geometry.Rectangle([21.8, 39.25, 22.9, 39.75]))
f_result   = solara.reactive(None)
f_status   = solara.reactive("")
f_basemap  = solara.reactive("Google satellite")
f_version  = solara.reactive(0)
f_view     = solara.reactive("Map")


def flood_map():
    m, base = new_map(center=(39.5, 22.35), zoom=9)
    base.url = BASEMAPS[f_basemap.value]
    m.add_legend(title="FloodScope", legend_dict={"Flooded (new water)": FLOOD_COLOR},
                 position="bottomright")
    r = f_result.value
    if r is not None:
        if not r["event"]:                     # radar images: in the list, off at start
            m.addLayer(r["before"], RADAR_VIS, "Before · radar VV", False)
            m.addLayer(r["after"], RADAR_VIS, "After · radar VV", False)
        m.addLayer(r["mask"], {"palette": [FLOOD_COLOR]}, "Flooded area")
        add_outline(m, r["area"])
        fit_view(m, r["box"])
    return m, base


@solara.component
def FloodScope():
    m, base = solara.use_memo(flood_map, [f_version.value])

    def run(geom, before_dates, after_dates, event):
        try:
            r = eng.floodscope(geom, before_dates, after_dates, vv_thr=f_thr.value)
            r["area"], r["event"] = geom, event
            r["box"] = box_of(geom)
            r["chart"] = eng.lc_chart(r["groups"], xlabel="Flooded area (km²)")
            f_result.value = r
            f_view.value = "Map"
            f_version.value += 1
            f_status.value = (f"✅ Done. Radar images used: "
                              f"{r['n_before']} before, {r['n_after']} after.")
        except Exception as e:
            f_status.value = f"⚠️ {e}"

    def analyze():
        use_drawn_area(m, f_area)
        in_background(f_status, run, f_area.value, (f_b_start.value, f_b_end.value),
                      (f_a_start.value, f_a_end.value), False)

    def load_event():
        ev = FLOOD_EVENTS[f_event.value]
        in_background(f_status, run, ee.Geometry.Rectangle(ev["bbox"]),
                      ev["before"], ev["after"], True)

    def clear_area():
        f_result.value = None
        f_status.value = ""
        f_version.value += 1

    def set_basemap(name):
        f_basemap.value = name
        base.url = BASEMAPS[name]

    with solara.Columns([1, 3]):
        with solara.Column():
            solara.ToggleButtonsSingle(value=f_mode, values=["Map your own", "Major events"])
            if f_mode.value == "Major events":
                solara.Select("Event", value=f_event, values=list(FLOOD_EVENTS))
                event_info(FLOOD_EVENTS[f_event.value])
                solara.Button("Show flooded area", on_click=load_event, color="#0064C8",
                              disabled=busy(f_status))
            else:
                solara.Text("Draw a box on the map (■ tool), or keep the default area.")
                date_inputs("Before", f_b_start, f_b_end)
                date_inputs("After", f_a_start, f_a_end)
                solara.SliderFloat("VV threshold (dB)", value=f_thr, min=-25.0, max=-10.0, step=0.5)
                with solara.Row():
                    solara.Button("Map flooded area", on_click=analyze, color="#0064C8",
                                  disabled=busy(f_status))
                    solara.Button("Clear", on_click=clear_area, outlined=True)
            solara.Select("Basemap", value=f_basemap.value, values=list(BASEMAPS),
                          on_value=set_basemap)
            show_status(f_status.value)

        r = f_result.value

        def stats():
            with solara.Columns([1, 1]):
                with solara.Column():
                    show_table(r["table"])
                with solara.Column():
                    if r["chart"] is not None:
                        solara.FigureMatplotlib(r["chart"])

        with solara.Column():
            headline = f"{r['km2']:.1f} km² flooded" if r else ""
            map_or_stats(m, f_view, headline, stats)


# =====================================================================
# Part 5 · ☀️ DroughtScope
# =====================================================================
d_start    = solara.reactive("2024-07-01")
d_end      = solara.reactive("2024-08-31")
d_thr      = solara.reactive(0.7)
d_area     = solara.reactive(ee.Geometry.Rectangle([21.8, 39.25, 22.9, 39.75]))
d_result   = solara.reactive(None)
d_status   = solara.reactive("")
d_basemap  = solara.reactive("Google satellite")
d_version  = solara.reactive(0)
d_view     = solara.reactive("Map")


def drought_map():
    m, base = new_map(center=(39.5, 22.35), zoom=9)
    base.url = BASEMAPS[d_basemap.value]
    m.add_colorbar(vis_params=TVDI_VIS, label="TVDI (0 wet → 1 dry)", position="bottomright")
    r = d_result.value
    if r is not None:
        add_swipe(m, r["image"], L_TRUE, r["tvdi"], TVDI_VIS,
                  "Landsat · true color", "TVDI")
        add_outline(m, r["area"])
        fit_view(m, r["box"])
    return m, base


@solara.component
def DroughtScope():
    m, base = solara.use_memo(drought_map, [d_version.value])

    def run():
        try:
            r = eng.droughtscope(d_area.value, (d_start.value, d_end.value), tvdi_thr=d_thr.value)
            r["area"] = d_area.value
            r["box"] = box_of(d_area.value)
            r["triangle"] = eng.triangle_chart(r)
            r["chart"] = eng.lc_chart(r["groups"], xlabel="Dry-stressed area (km²)")
            d_result.value = r
            d_view.value = "Map"
            d_version.value += 1
            d_status.value = f"✅ Done. Landsat scenes used: {r['n']}."
        except Exception as e:
            d_status.value = f"⚠️ {e}"

    def analyze():
        use_drawn_area(m, d_area)
        in_background(d_status, run)

    def clear_area():
        d_result.value = None
        d_status.value = ""
        d_version.value += 1

    def set_basemap(name):
        d_basemap.value = name
        base.url = BASEMAPS[name]

    with solara.Columns([1, 3]):
        with solara.Column():
            solara.Text("Draw a box on the map (■ tool), or keep the default area.")
            date_inputs("Period", d_start, d_end)
            solara.SliderFloat("TVDI threshold (dry stress)", value=d_thr, min=0.5, max=0.9, step=0.05)
            with solara.Row():
                solara.Button("Map dryness", on_click=analyze, color="#B45309",
                              disabled=busy(d_status))
                solara.Button("Clear", on_click=clear_area, outlined=True)
            solara.Select("Basemap", value=d_basemap.value, values=list(BASEMAPS),
                          on_value=set_basemap)
            show_status(d_status.value)

        r = d_result.value

        def stats():
            solara.Markdown(f"Mean TVDI **{r['mean_tvdi']:.2f}** · "
                            f"**{r['share']:.0f}%** of the area under dry stress")
            with solara.Columns([1, 1]):
                with solara.Column():
                    solara.FigureMatplotlib(r["triangle"])
                with solara.Column():
                    if r["chart"] is not None:
                        solara.FigureMatplotlib(r["chart"])
            show_table(r["table"])

        with solara.Column():
            headline = f"{r['km2']:.1f} km² under dry stress" if r else ""
            map_or_stats(m, d_view, headline, stats)


# =====================================================================
# Part 5b · 🌈 IndexScope
# =====================================================================
i_sensor   = solara.reactive("Sentinel-2")
i_index    = solara.reactive("NDVI")
i_start    = solara.reactive("2024-06-01")
i_end      = solara.reactive("2024-06-30")
i_area     = solara.reactive(ee.Geometry.Rectangle([21.80, 39.30, 22.10, 39.50]))
i_result   = solara.reactive(None)
i_status   = solara.reactive("")
i_basemap  = solara.reactive("Google satellite")
i_version  = solara.reactive(0)
i_view     = solara.reactive("Map")

RGB_VIS = {"bands": ["RED", "GREEN", "BLUE"], "min": 0, "max": 0.3}


def index_vis(key):
    spec = INDICES[key]
    return {"min": spec["min"], "max": spec["max"], "palette": spec["palette"]}


def index_map():
    m, base = new_map(center=(39.4, 21.95), zoom=10)
    base.url = BASEMAPS[i_basemap.value]
    r = i_result.value
    if r is not None:
        vis = index_vis(r["key"])
        m.addLayer(r["image"], RGB_VIS, f"{r['sensor']} · true colour", False)
        m.addLayer(r["index"], vis, r["key"])
        m.add_colorbar(vis_params=vis, label=f"{r['key']} · {INDICES[r['key']]['name']}",
                       position="bottomright")
        add_outline(m, r["area"])
        fit_view(m, r["box"])
    return m, base


@solara.component
def IndexCard(key):
    """What the index is: name, equation, how to read it, reference."""
    spec = INDICES[key]
    reading = "\n".join(f"- {line.replace('>', '&gt;')}" for line in spec["reading"])
    solara.Markdown(f"**{key} · {spec['name']}**\n\n"
                    f"`{key} = {spec['formula']}`\n\n"
                    f"{spec['about']}\n\n"
                    f"**How to read it**\n\n{reading}\n\n"
                    f"*Reference: {spec['reference']}*\n\n"
                    f"{SOURCES}")


@solara.component
def IndexScope():
    m, base = solara.use_memo(index_map, [i_version.value])

    def run(geom, sensor, key, start, end):
        try:
            r = eng.indexscope(geom, sensor, key, start, end)
            r.update(area=geom, box=box_of(geom), sensor=sensor, key=key)
            r["chart"] = eng.index_histogram(r["values"], INDICES[key], key) if r["values"] else None
            i_result.value = r
            i_view.value = "Map"
            i_version.value += 1
            i_status.value = f"✅ Done. {sensor} images used: {r['n']}."
        except Exception as e:
            i_status.value = f"⚠️ {e}"

    def analyze():
        use_drawn_area(m, i_area)
        in_background(i_status, run, i_area.value, i_sensor.value, i_index.value,
                      i_start.value, i_end.value)

    def clear_area():
        i_result.value = None
        i_status.value = ""
        i_version.value += 1

    def set_basemap(name):
        i_basemap.value = name
        base.url = BASEMAPS[name]

    with solara.Columns([1, 3]):
        with solara.Column():
            solara.Select("Satellite", value=i_sensor, values=list(SENSORS))
            solara.Text(SENSOR_INFO[i_sensor.value], style={"font-size": "13px", "opacity": "0.75"})
            solara.Select("Index", value=i_index, values=list(INDICES))
            solara.Text(INDICES[i_index.value]["name"], style={"font-size": "13px", "opacity": "0.75"})
            date_inputs("Period", i_start, i_end)
            solara.Text("Draw a box on the map (■ tool), or keep the default area.")
            with solara.Row():
                solara.Button("Map index", on_click=analyze, color="#0E7490",
                              disabled=busy(i_status))
                solara.Button("Clear", on_click=clear_area, outlined=True)
            solara.Select("Basemap", value=i_basemap.value, values=list(BASEMAPS),
                          on_value=set_basemap)
            show_status(i_status.value)

        r = i_result.value

        def stats():
            solara.Markdown(
                f"| | {r['key']} |\n|---|---|\n"
                f"| Mean | {r['mean']:.3f} |\n| Median | {r['p50']:.3f} |\n"
                f"| 5th percentile | {r['p5']:.3f} |\n| 95th percentile | {r['p95']:.3f} |\n"
                f"| Images in composite | {r['n']} |\n| Pixel size | {r['scale']} m |")
            if r["chart"] is not None:
                solara.FigureMatplotlib(r["chart"])

        with solara.Column():
            views = ["Map", "Index info"] + (["Statistics"] if r else [])
            with solara.Row(style={"align-items": "center", "gap": "24px"}):
                solara.ToggleButtonsSingle(value=i_view, values=views)
                if r and r["mean"] is not None:
                    solara.Markdown(f"### {r['key']} · mean {r['mean']:.2f}")
            if i_view.value == "Index info":
                with solara.Column(style={"max-width": "760px"}):
                    IndexCard(i_index.value)
            elif i_view.value == "Statistics" and r:
                stats()
            else:
                solara.display(m)


# =====================================================================
# Part 6 · About + the front door (Page)
# =====================================================================
ABOUT = """
## About GaiaScope

GaiaScope maps natural disasters from space with **Google Earth Engine**.
Pick a module, draw a box (or open a major event), and GaiaScope compares satellite
images from **before** and **after** the event. It reports the affected area in km²
and which land cover was hit.

---

### BurnScope · burnt area and burn severity

**Data.** Sentinel-2 Level-2A surface reflectance (Copernicus / ESA), 10–20 m.
Clouds, cirrus and shadows are removed with the Scene Classification band (SCL),
and a median composite is built for each period.

**Method.** The *Normalized Burn Ratio* compares near-infrared (B8), which is high over
healthy vegetation, with shortwave infrared (B12), which rises after fire:

`NBR = (B8 − B12) / (B8 + B12)`   ·   `dNBR = NBR before − NBR after`

A pixel counts as burnt when dNBR is above the threshold (default **0.27**).
Severity follows the USGS classes: low 0.10–0.27 · moderate-low 0.27–0.44 ·
moderate-high 0.44–0.66 · high > 0.66. Permanent water is excluded.
If the scar touches the edge of a drawn box, the box is enlarged automatically.

**Keep in mind.** Harvested fields and clouds left in the composite can look like
burns, so check the result against the true-colour image.

*Key reference:* Key, C. H. & Benson, N. C. (2006). *Landscape Assessment (LA): sampling
and analysis methods.* USDA Forest Service, Gen. Tech. Rep. RMRS-GTR-164-CD.

---

### FloodScope · new flood water

**Data.** Sentinel-1 C-band SAR, GRD, IW mode, VV polarisation (Copernicus / ESA), 10 m.
Radar sees through clouds and works at night, which matters during storms.

**Method.** Calm water reflects the radar signal away from the satellite, so it looks
**dark** (low backscatter). A pixel is mapped as new flood water when it is darker than
the threshold (default **−17 dB**) *after* the event, was **not** dark *before*, and is
not permanent water. A 50 m median filter reduces radar speckle.

**Keep in mind.** Flooded forests and towns can look bright instead of dark and may be
missed. Smooth surfaces such as tarmac or dry sand can look like water.

*Key reference:* Twele, A., Cao, W., Plank, S. & Martinis, S. (2016). Sentinel-1-based
flood mapping: a fully automated processing chain. *International Journal of Remote
Sensing*, 37(13), 2990–3004.

---

### DroughtScope · vegetation dryness (TVDI)

**Data.** Landsat 8 and 9 Collection 2 Level-2 (USGS / NASA), 30 m: surface reflectance
for NDVI and the thermal band for land surface temperature (Ts, °C). Clouds, shadows
and snow are removed with the QA_PIXEL band.

**Method.** In a scatter of Ts against NDVI the pixels form a triangle. Its upper
**dry edge** (the hottest pixels for each NDVI) is fitted as a straight line through
the 99th percentile of Ts in NDVI bins of 0.05 (NDVI ≥ 0.15). The **wet edge** is the
coolest pixels. For every pixel:

`TVDI = (Ts − Ts_min) / (Ts_max(NDVI) − Ts_min)`

TVDI runs from **0** (wet, cool) to **1** (dry, stressed). Pixels at or above the threshold
(default **0.7**) are counted as under dry stress.

**Keep in mind.** The triangle needs enough land with a wide range of NDVI values.
Mountains are cooler with height, which TVDI can mistake for moisture.

*Key reference:* Sandholt, I., Rasmussen, K. & Andersen, J. (2002). A simple
interpretation of the surface temperature/vegetation index space for assessment of
surface moisture status. *Remote Sensing of Environment*, 79(2–3), 213–224.

---

### Land cover and sources

Affected areas are split by **ESA WorldCover 2021 v200** (10 m) classes, using the
official WorldCover colours.

- Sentinel-1 and Sentinel-2: Copernicus programme, European Space Agency
- Landsat 8 and 9: U.S. Geological Survey / NASA
- ESA WorldCover: Zanaga, D. et al. (2022), ESA WorldCover 10 m 2021 v200
- Event descriptions link to their own sources (Copernicus EMS, ESA, scientific papers)
- Processing: Google Earth Engine · Basemap imagery © Google

GaiaScope is a research and teaching tool, not an official emergency product.

---

Made by **Christina Lekka** · PhD candidate, Department of Geography,
Harokopio University of Athens.
"""


@solara.component
def About():
    with solara.Column(style={"max-width": "900px"}):
        solara.Markdown(ABOUT)



# =====================================================================
# Part 7 · Home (the welcome page from our design)
# =====================================================================
def go(name, mode="Map your own"):
    """Open a module, already in the chosen mode."""
    if name == "BurnScope":
        b_mode.value = mode
    elif name == "FloodScope":
        f_mode.value = mode
    module.value = name


CARDS = [
    ("BurnScope", "#C2410C", "Burnt area and burn severity",
     "Sentinel-2 · dNBR. Before in true colour, after in false colour, scar by severity class.", True),
    ("FloodScope", "#0064C8", "New flood water",
     "Sentinel-1 radar (VV), which sees through clouds. Change detection before vs after.", True),
    ("DroughtScope", "#B45309", "Vegetation dryness",
     "Landsat 8 + 9 · the Ts/VI triangle and the TVDI index, from wet (0) to dry (1).", False),
    ("IndexScope", "#0E7490", "Spectral indices",
     "Sentinel-2, Landsat 8 or 9 · NDVI, NDWI, NBR and more, with equations and legends.", False),
]

STEPS = [("1", "Draw an area", "Use the ■ tool on the map, or open a major event."),
         ("2", "Pick the dates", "Before and after. GaiaScope finds the clear images."),
         ("3", "Swipe and read", "Map, km² affected, and which land cover was hit.")]


@solara.component
def Home():
    with solara.Column(style={"max-width": "1100px", "margin": "0 auto", "padding": "24px 8px"}):
        solara.Text("EARTH OBSERVATION · HAZARD MAPPING",
                    style={"letter-spacing": "0.12em", "font-size": "13px", "color": "#0F7A62",
                           "font-weight": "600"})
        solara.Markdown("# Map and visualize what changed on the ground.")
        solara.Markdown("Draw an area, pick two dates, and compare satellite images side by side. "
                        "GaiaScope maps **burnt land**, **floods** and **drought**, then tells you "
                        "how much area was affected.")

        with solara.Columns([1, 1, 1, 1]):
            for name, color, subtitle, text, has_events in CARDS:
                with solara.Card(name, subtitle=subtitle,
                                 style={"border-top": f"4px solid {color}", "height": "100%"}):
                    solara.Markdown(text)
                    with solara.Row(style={"flex-wrap": "wrap", "gap": "8px"}):
                        solara.Button("Map your own", color=color,
                                      on_click=lambda n=name: go(n))
                        if has_events:
                            solara.Button("Major events", outlined=True,
                                          on_click=lambda n=name: go(n, "Major events"))

        solara.Markdown("### How it works")
        with solara.Columns([1, 1, 1]):
            for number, title, text in STEPS:
                with solara.Card(f"{number} · {title}"):
                    solara.Markdown(text)

        solara.Markdown("---\nBuilt by **Christina Lekka** · Harokopio University of Athens  \n"
                        "Data: Copernicus Sentinel-1 & 2, USGS Landsat 8–9, ESA WorldCover · "
                        "Google Earth Engine")

CSS = """
.v-app-bar.v-toolbar {
    background: linear-gradient(90deg, rgba(15,122,98,1) 0%, rgba(15,122,98,0.75) 50%,
                                rgba(15,122,98,0.45) 100%) !important;
}
.gaia-table table { border-collapse: collapse; color: inherit; }
.theme--dark :is(p, h1, h2, h3, h4, li, td, th, strong, em, code):not(.leaflet-container *) {
    color: rgba(255, 255, 255, 0.9) !important;
}
.gaia-table th, .gaia-table td { padding: 4px 12px; text-align: left; }
"""

dark   = solara.reactive(False)         # the app starts in light mode
module = solara.reactive("Home")         # which page is open

MODULES = {"Home": Home, "BurnScope": BurnScope, "FloodScope": FloodScope,
           "DroughtScope": DroughtScope, "IndexScope": IndexScope, "About": About}


def apply_theme():
    solara.lab.theme.themes.light.primary = "#0F7A62"
    solara.lab.theme.themes.dark.primary = "#0F7A62"
    solara.lab.theme.dark = dark.value


@solara.component
def Page():
    solara.use_effect(apply_theme, [dark.value])
    solara.Style(CSS)
    solara.Title("GaiaScope")
    with solara.AppBarTitle():
        solara.Text("GaiaScope")
    with solara.AppBar():
        solara.Switch(label="Dark mode", value=dark)
    with solara.Column():
        solara.ToggleButtonsSingle(value=module, values=list(MODULES))
        MODULES[module.value]()

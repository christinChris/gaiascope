"""GaiaScope · events.py 
Ready-made disaster events. Only data here: no Earth Engine, no maps.
Each event:  before/after = (start, end) dates · bbox = [west, south, east, north]
Order inside each dict = order in the dropdown (oldest → newest).
"""

# ---------- 🔥 Wildfires (BurnScope) ----------
FIRE_EVENTS = {
    "Varympompi · Athens (Aug 2021)": {
        "before": ("2021-07-15", "2021-08-01"),
        "after":  ("2021-08-10", "2021-08-31"),
        "bbox":   [23.70, 38.10, 23.85, 38.20],
        "info":   "One of the extreme wildfires of early August 2021, it burned through the northern suburbs "
                  "of Athens around Varympompi and Tatoi.",
        "source": "https://www.mdpi.com/2673-4931/17/1/8",
    },
    "North Evia · Greece (Aug 2021)": {
        "before": ("2021-07-15", "2021-08-02"),
        "after":  ("2021-08-20", "2021-09-10"),
        "bbox":   [23.05, 38.80, 23.45, 39.05],
        "info":   "In early August 2021, during the Mediterranean heatwave, huge wildfires burned large parts "
                  "of northern Evia's pine forests and villages.",
        "source": "https://www.esa.int/ESA_Multimedia/Images/2021/08/Wildfires_ravage_Greek_island_of_Evia",
    },
    "Dervenochoria · Attica (Jul 2023)": {
        "before": ("2023-07-01", "2023-07-15"),
        "after":  ("2023-07-25", "2023-08-15"),
        "bbox":   [23.30, 38.08, 23.60, 38.25],
        "info":   "One of several fires that started in Attica on 17 July 2023, during a strong heatwave, "
                  "burning around the villages of Dervenochoria in western Attica.",
        "source": "https://mapping.emergency.copernicus.eu/news/information-bulletin-169-the-copernicus-emergency-management-service-maps-some-critical-wildfires-in-greece-update/",
    },
    "Rhodes · Greece (Jul 2023)": {
        "before": ("2023-07-01", "2023-07-15"),
        "after":  ("2023-08-01", "2023-08-20"),
        "bbox":   [27.80, 35.90, 28.25, 36.35],
        "info":   "A wildfire started on 18 July 2023 in central Rhodes and spread south over the following days, "
                  "forcing thousands of residents and tourists to evacuate.",
        "source": "https://mapping.emergency.copernicus.eu/news/wildfire-on-rhodes-island-greece/",
    },
    "Corfu · Ionian Islands (Jul 2023)": {
        "before": ("2023-07-01", "2023-07-21"),
        "after":  ("2023-07-28", "2023-08-20"),
        "bbox":   [19.80, 39.65, 19.95, 39.80],
        "info":   "Wildfires in north-eastern Corfu led to mass evacuations on 23 July 2023, "
                  "with residents directed towards Ipsos and Barbati.",
        "source": "https://mapping.emergency.copernicus.eu/news/information-bulletin-169-the-copernicus-emergency-management-service-maps-some-critical-wildfires-in-greece-update/",
    },
    "Magnesia · Thessaly (Jul 2023)": {
        "before": ("2023-07-05", "2023-07-24"),
        "after":  ("2023-08-01", "2023-08-25"),
        "bbox":   [22.65, 39.15, 22.95, 39.40],
        "info":   "Fires that began on 26 July 2023 near Almyros and Velestino reached the Nea Anchialos "
                  "air base and forced the evacuation of the town.",
        "source": "https://en.wikipedia.org/wiki/2023_Greece_wildfires",
    },
    "Evros – Dadia · Greece (Aug 2023)": {
        "before": ("2023-07-20", "2023-08-15"),
        "after":  ("2023-09-05", "2023-09-30"),
        "bbox":   [25.55, 40.80, 26.50, 41.35],
        "info":   "A wildfire that began on 21 August 2023 burned for weeks across Evros, including the Dadia forest "
                  "and the area north of Alexandroupolis — about 73,000 ha, the largest fire recorded in the EU.",
        "source": "https://www.copernicus.eu/en/media/image-day-gallery/greeces-biggest-fire-crisis-continues",
    },
    "Parnitha – Fyli · Attica (Aug 2023)": {
        "before": ("2023-08-01", "2023-08-20"),
        "after":  ("2023-08-26", "2023-09-15"),
        "bbox":   [23.60, 38.08, 23.80, 38.22],
        "info":   "A wildfire started on 22 August 2023 near a monastery in Fyli and reached "
                  "Mount Parnitha the next day, burning part of the national park before it was put out on 24 August.",
        "source": "https://en.wikipedia.org/wiki/2023_Greece_wildfires",
    },
    "Varnavas · Attica (Aug 2024)": {
        "before": ("2024-07-20", "2024-08-10"),
        "after":  ("2024-08-15", "2024-09-05"),
        "bbox":   [23.75, 37.98, 24.10, 38.32],
        "info":   "A wildfire broke out near Varnavas, north-east of Athens, on 11 August 2024 "
                  "and spread rapidly south towards the northern suburbs of Athens.",
        "source": "https://mapping.emergency.copernicus.eu/news/wildfire-in-attica-region-greece/",
    },
    "Corinthia · Peloponnese (Sep 2024)": {
        "before": ("2024-09-01", "2024-09-27"),
        "after":  ("2024-10-05", "2024-10-25"),
        "bbox":   [22.45, 37.90, 22.75, 38.12],
        "info":   "A wildfire started near the village of Rozena in Corinthia on 29 September 2024 "
                  "and spread across the northern Peloponnese.",
        "source": "https://reliefweb.int/report/greece/greece-wildfire-update-greek-civil-protection-copernicus-emsr-greek-government-jrc-effis-media-echo-daily-flash-03-october-2024",
    },
    # ---------- 2025 ----------
    "Chios · North Aegean (Jun 2025)": {
        "before": ("2025-06-01", "2025-06-20"),
        "after":  ("2025-07-01", "2025-07-20"),
        "bbox":   [25.90, 38.20, 26.15, 38.42],
        "info":   "Three wildfires started on Chios on 22 June 2025 and burned about 4,000 ha, "
                  "reaching villages such as Palaia Fokaia and Thymiana.",
        "source": "https://mapping.emergency.copernicus.eu/news/wildfires-on-chios-island-greece/",
    },
    "Kythira · Attica islands (Jul 2025)": {
        "before": ("2025-07-05", "2025-07-24"),
        "after":  ("2025-08-05", "2025-08-25"),
        "bbox":   [22.90, 36.13, 23.12, 36.38],
        "info":   "A wildfire that broke out on 26 July 2025 near Pitsinades burned a large part of Kythira, "
                  "about 10,900 ha according to Copernicus data.",
        "source": "https://www.copernicus.eu/en/media/image-day-gallery/wildfire-island-kythira-greece",
    },
    "Western Achaia · Patras (Aug 2025)": {
        "before": ("2025-07-25", "2025-08-10"),
        "after":  ("2025-08-20", "2025-09-10"),
        "bbox":   [21.45, 38.05, 21.75, 38.25],
        "info":   "During the August 2025 heatwave a wildfire started on 12 August near Flogeraika in western Achaia "
                  "and spread towards the outskirts of Patras, burning homes and factories.",
        "source": "https://greekreporter.com/2025/08/13/greece-ablaze-wildfires-peloponnese-epirus-and-chios/",
    },
    # ---------- 2026 ----------
    "Rethymno · Crete (Jul 2026)": {
        "before": ("2026-07-10", "2026-07-27"),
        "after":  ("2026-08-08", "2026-08-31"),
        "bbox":   [24.30, 35.10, 24.60, 35.30],
        "info":   "A wildfire that started on 29 July 2026 in southern Rethymno spread near Krya Vrysi, Agia Paraskevi "
                  "and Preveli, burning about 4,500 ha and forcing about 8,000 evacuations.",
        "source": "https://greekcitytimes.com/2026/07/31/greek-wildfires-rethymno-xironormi-argolida-july-2026/",
    },
    "Porto Germeno – Psatha · W. Attica (Jul 2026)": {
        "before": ("2026-07-10", "2026-07-29"),
        "after":  ("2026-08-08", "2026-08-31"),
        "bbox":   [23.10, 37.98, 23.45, 38.22],
        "info":   "A wind-driven wildfire that began on 31 July 2026 near Porto Germeno and Psatha, on the Gulf of Corinth, "
                  "burned more than 10,000 ha across western Attica and Boeotia (Copernicus EMSR909).",
        "source": "https://eu-space.europa.eu/components/earth-observation-copernicus/image-of-the-day/wildfires-burn-more-10000-hectares-greece",
    },
    "Achaia · Western Greece (Jul 2026)": {
        "before": ("2026-07-10", "2026-07-29"),
        "after":  ("2026-08-08", "2026-08-31"),
        "bbox":   [21.82, 38.20, 22.10, 38.38],
        "info":   "A wildfire started on 31 July 2026 about 20 km east-northeast of Patras; villages including Aravonitsa "
                  "and Sinania were evacuated (Copernicus EMSR910).",
        "source": "https://mapping.emergency.copernicus.eu/news/wildfire-in-achaia-greece-emsr910/",
    },
}

# ---------- 🌊 Floods (FloodScope) ----------
FLOOD_EVENTS = {
    "Storm Nefeli · Chrysoupoli (Jun 2018)": {
        "before": ("2018-06-01", "2018-06-24"),
        "after":  ("2018-06-28", "2018-07-08"),
        "bbox":   [24.60, 40.85, 24.95, 41.05],
        "info":   "Storm Nefeli crossed Greece on 25 June 2018. Flooding began on 28 June in north-eastern Greece, "
                  "around Chrysoupoli and the Nestos delta.",
        "source": "https://mapping.emergency.copernicus.eu/news/the-copernicus-emergency-management-service-monitors-floods-in-north-eastern-greece/",
    },
    "Medicane Ianos · Karditsa (Sep 2020)": {
        "before": ("2020-08-15", "2020-09-15"),
        "after":  ("2020-09-18", "2020-09-25"),
        "bbox":   [21.75, 39.25, 22.30, 39.55],
        "info":   "Ianos, a rare Mediterranean cyclone (medicane), hit western and central Greece on 17–19 September 2020, "
                  "flooding farmland and villages around Karditsa.",
        "source": "https://mapping.emergency.copernicus.eu/activations/EMSR465/",
    },
    "Storm Daniel · Thessaly (Sep 2023)": {
        "before": ("2023-08-01", "2023-08-31"),
        "after":  ("2023-09-07", "2023-09-15"),
        "bbox":   [21.8, 39.25, 22.9, 39.75],
        "info":   "Storm Daniel brought days of extreme rainfall to Thessaly on 4–7 September 2023. "
                  "Large parts of the plain and the former Lake Karla basin stayed under water for weeks.",
        "source": "https://mapping.emergency.copernicus.eu/activations/EMSR692",
    },
}
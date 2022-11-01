#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""
    The list of stations used in various KNMI datasets.
"""

from collections import namedtuple

import numpy as np
import pandas as pd

_Station = namedtuple(
    "_Station", ["number", "longitude", "latitude", "altitude", "name"]
)


_stations = {
    8: _Station(
        number=8, longitude=5.528, latitude=52.453, altitude=-4.2, name="LELYSTAD"
    ),
    13: _Station(
        number=13,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="WISSEKERKE ???",
    ),
    16: _Station(
        number=16,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="HEINKENSZAND ???",
    ),
    17: _Station(
        number=17, longitude=3.892, latitude=51.529, altitude=0.7, name="WILHELMINADORP"
    ),
    18: _Station(
        number=18,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="PHILIPPINE ???",
    ),
    19: _Station(
        number=19,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="NIEUWE TONGE ???",
    ),
    20: _Station(
        number=20, longitude=6.7, latitude=51.969, altitude=34.1, name="WINTERSWIJK"
    ),
    28: _Station(
        number=28, longitude=5.82, latitude=52.961, altitude=-0.4, name="JOURE"
    ),
    29: _Station(
        number=29, longitude=5.044, latitude=52.65, altitude=999.9, name="HOORN (NH)"
    ),
    32: _Station(
        number=32, longitude=4.526, latitude=51.576, altitude=1.2, name="OUDENBOSCH"
    ),
    33: _Station(
        number=33, longitude=5.677, latitude=51.549, altitude=13.2, name="GEMERT"
    ),
    34: _Station(
        number=34, longitude=6.887, latitude=52.785, altitude=24.1, name="EMMEN"
    ),
    35: _Station(
        number=35,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="HAAMSTEDE ???",
    ),
    36: _Station(
        number=36,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="NUMANSDORP ???",
    ),
    37: _Station(
        number=37,
        longitude=5.675,
        latitude=51.976,
        altitude=2.0,
        name="WAGENINGEN (HAARWEG)",
    ),
    38: _Station(
        number=38,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="NAALDWIJK ???",
    ),
    39: _Station(
        number=39,
        longitude=4.156,
        latitude=51.988,
        altitude=999.9,
        name="H. VAN HOLLAND(MOLENPAD)",
    ),
    40: _Station(
        number=40,
        longitude=5.837,
        latitude=51.856,
        altitude=999.9,
        name="NIJMEGEN (RADBOUD)",
    ),
    41: _Station(
        number=41, longitude=5.526, latitude=52.458, altitude=-4.0, name="LELYSTAD"
    ),
    108: _Station(
        number=108,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="HELLEVOETSLUIS ???",
    ),
    122: _Station(
        number=122, longitude=6.303, latitude=52.158, altitude=9.0, name="ALMEN"
    ),
    125: _Station(
        number=125, longitude=5.054, latitude=51.784, altitude=1.4, name="ANDEL"
    ),
    126: _Station(
        number=126, longitude=4.079, latitude=51.596, altitude=1.0, name="ST ANNALAND"
    ),
    127: _Station(
        number=127, longitude=3.314, latitude=47.975, altitude=999.9, name="BUCHTEN ???"
    ),
    128: _Station(
        number=128, longitude=6.443, latitude=52.593, altitude=6.0, name="DEDEMSVAART"
    ),
    129: _Station(
        number=129, longitude=5.78, latitude=52.712, altitude=-3.7, name="EMMELOORD"
    ),
    130: _Station(
        number=130, longitude=3.314, latitude=47.975, altitude=999.9, name="EPEN ???"
    ),
    133: _Station(
        number=133,
        longitude=5.342,
        latitude=53.398,
        altitude=-1.0,
        name="HOORN (TERSCHELLING)",
    ),
    135: _Station(
        number=135, longitude=5.338, latitude=53.07, altitude=3.0, name="KORNWERDERZAND"
    ),
    138: _Station(
        number=138, longitude=5.676, latitude=50.843, altitude=999.9, name="MAASTRICHT"
    ),
    139: _Station(
        number=139, longitude=5.121, latitude=52.458, altitude=-0.8, name="MARKEN"
    ),
    142: _Station(
        number=142,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="OUDE WETERING ???",
    ),
    143: _Station(
        number=143, longitude=4.393, latitude=51.855, altitude=0.2, name="POORTUGAAL"
    ),
    147: _Station(
        number=147, longitude=5.611, latitude=52.658, altitude=999.9, name="URK"
    ),
    148: _Station(
        number=148, longitude=6.191, latitude=51.356, altitude=30.0, name="VENLO"
    ),
    152: _Station(
        number=152, longitude=3.558, latitude=51.356, altitude=1.2, name="SCHOONDIJKE"
    ),
    153: _Station(
        number=153, longitude=5.356, latitude=52.886, altitude=2.6, name="STAVOREN"
    ),
    158: _Station(
        number=158,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="SPIJK (GR.) ???",
    ),
    159: _Station(
        number=159, longitude=4.057, latitude=51.251, altitude=2.4, name="KAPELLEBRUG"
    ),
    161: _Station(
        number=161, longitude=5.975, latitude=53.391, altitude=999.9, name="TERNAARD"
    ),
    162: _Station(
        number=162,
        longitude=5.222,
        latitude=52.418,
        altitude=999.9,
        name="OOSTVAARDERSDIEP",
    ),
    163: _Station(
        number=163,
        longitude=5.476,
        latitude=52.263,
        altitude=0.2,
        name="NIJKERK (SLUIS)",
    ),
    164: _Station(
        number=164, longitude=5.909, latitude=51.092, altitude=34.1, name="ECHT"
    ),
    165: _Station(
        number=165,
        longitude=3.314,
        latitude=47.975,
        altitude=999.9,
        name="KAAP HOOFD ???",
    ),
    166: _Station(
        number=166,
        longitude=6.238,
        latitude=53.583,
        altitude=4.0,
        name="SCHIERMONNIKOOG",
    ),
    167: _Station(
        number=167, longitude=6.85, latitude=53.381, altitude=999.9, name="BIERUM"
    ),
    168: _Station(
        number=168, longitude=5.906, latitude=50.764, altitude=155.0, name="EPEN"
    ),
    169: _Station(
        number=169, longitude=5.304, latitude=53.392, altitude=0.4, name="FORMERUM"
    ),
    170: _Station(
        number=170,
        longitude=5.715,
        latitude=50.794,
        altitude=50.0,
        name="OOST MAARLAND",
    ),
    200: _Station(
        number=200, longitude=4.355, latitude=52.041, altitude=999.9, name="YPENBURG"
    ),
    201: _Station(
        number=201, longitude=2.936, latitude=54.327, altitude=42.7, name="D15-FA-1"
    ),
    202: _Station(
        number=202, longitude=4.362, latitude=52.206, altitude=9999.9, name="MP KATWIJK"
    ),
    203: _Station(
        number=203, longitude=3.342, latitude=52.361, altitude=41.8, name="P11-B"
    ),
    204: _Station(
        number=204, longitude=3.628, latitude=53.271, altitude=41.8, name="K14-FA-1C"
    ),
    205: _Station(
        number=205, longitude=3.81, latitude=55.401, altitude=48.4, name="A12-CPP"
    ),
    206: _Station(
        number=206, longitude=4.012, latitude=54.118, altitude=43.4, name="F16-A"
    ),
    207: _Station(
        number=207, longitude=4.961, latitude=53.616, altitude=44.0, name="L9-FF-1"
    ),
    208: _Station(
        number=208, longitude=5.942, latitude=53.493, altitude=40.5, name="AWG-1"
    ),
    209: _Station(
        number=209, longitude=4.518, latitude=52.465, altitude=0.0, name="IJMOND"
    ),
    210: _Station(
        number=210, longitude=4.43, latitude=52.171, altitude=-0.2, name="VALKENBURG"
    ),
    211: _Station(
        number=211, longitude=2.945, latitude=53.825, altitude=45.7, name="J6-A"
    ),
    212: _Station(
        number=212, longitude=4.151, latitude=52.919, altitude=50.9, name="HOORN-A"
    ),
    214: _Station(
        number=214, longitude=6.042, latitude=54.038, altitude=42.5, name="Gemini"
    ),
    215: _Station(
        number=215, longitude=4.437, latitude=52.141, altitude=-1.1, name="VOORSCHOTEN"
    ),
    225: _Station(
        number=225, longitude=4.555, latitude=52.463, altitude=4.4, name="IJMUIDEN"
    ),
    227: _Station(
        number=227, longitude=4.655, latitude=52.774, altitude=0.5, name="PETTEN"
    ),
    229: _Station(
        number=229, longitude=4.72, latitude=52.996, altitude=10.0, name="TEXELHORS MM"
    ),
    230: _Station(
        number=230, longitude=4.759, latitude=52.967, altitude=999.9, name="DEN HELDER"
    ),
    235: _Station(
        number=235, longitude=4.781, latitude=52.928, altitude=1.2, name="DE KOOY"
    ),
    239: _Station(
        number=239, longitude=4.696, latitude=54.855, altitude=50.6, name="F3-FB-1"
    ),
    240: _Station(
        number=240, longitude=4.79, latitude=52.318, altitude=-3.3, name="SCHIPHOL"
    ),
    242: _Station(
        number=242, longitude=4.921, latitude=53.241, altitude=10.8, name="VLIELAND"
    ),
    244: _Station(
        number=244, longitude=5.044, latitude=52.65, altitude=999.9, name="HOORN (NH)"
    ),
    247: _Station(
        number=247, longitude=4.555, latitude=52.422, altitude=18.0, name="BLOEMENDAAL"
    ),
    248: _Station(
        number=248, longitude=5.174, latitude=52.634, altitude=0.8, name="WIJDENES"
    ),
    249: _Station(
        number=249, longitude=4.979, latitude=52.644, altitude=-2.4, name="BERKHOUT"
    ),
    250: _Station(
        number=250, longitude=5.147, latitude=53.36, altitude=31.4, name="TERSCHELLING"
    ),
    251: _Station(
        number=251,
        longitude=5.346,
        latitude=53.392,
        altitude=0.7,
        name="HOORN (TERSCHELLING)",
    ),
    252: _Station(
        number=252, longitude=3.22, latitude=53.219, altitude=37.7, name="K13"
    ),
    253: _Station(
        number=253, longitude=2.067, latitude=56.4, altitude=999.9, name="AUK-ALFA"
    ),
    254: _Station(
        number=254,
        longitude=4.296,
        latitude=52.274,
        altitude=999.9,
        name="MEETPOST NOORDWIJK",
    ),
    255: _Station(
        number=255,
        longitude=1.16,
        latitude=61.234,
        altitude=999.9,
        name="NORTH CORMORANT",
    ),
    257: _Station(
        number=257, longitude=4.603, latitude=52.506, altitude=8.5, name="WIJK AAN ZEE"
    ),
    258: _Station(
        number=258, longitude=5.401, latitude=52.649, altitude=7.3, name="HOUTRIBDIJK"
    ),
    260: _Station(
        number=260, longitude=5.18, latitude=52.1, altitude=1.9, name="DE BILT"
    ),
    263: _Station(
        number=263,
        longitude=5.177,
        latitude=52.101,
        altitude=2.0,
        name="DE BILT (TEST)",
    ),
    265: _Station(
        number=265, longitude=5.274, latitude=52.13, altitude=13.9, name="SOESTERBERG"
    ),
    266: _Station(
        number=266, longitude=5.338, latitude=53.07, altitude=3.0, name="KORNWERDERZAND"
    ),
    267: _Station(
        number=267, longitude=5.384, latitude=52.898, altitude=-1.3, name="STAVOREN"
    ),
    268: _Station(
        number=268, longitude=5.436, latitude=52.531, altitude=999.9, name="HOUTRIB"
    ),
    269: _Station(
        number=269, longitude=5.52, latitude=52.458, altitude=-3.7, name="LELYSTAD"
    ),
    270: _Station(
        number=270, longitude=5.752, latitude=53.224, altitude=1.2, name="LEEUWARDEN"
    ),
    271: _Station(
        number=271, longitude=5.356, latitude=52.888, altitude=2.6, name="STAVOREN"
    ),
    272: _Station(
        number=272, longitude=5.85, latitude=52.616, altitude=3.6, name="RAMSPOL"
    ),
    273: _Station(
        number=273, longitude=5.888, latitude=52.703, altitude=-3.3, name="MARKNESSE"
    ),
    275: _Station(
        number=275, longitude=5.873, latitude=52.056, altitude=48.2, name="DEELEN"
    ),
    277: _Station(
        number=277, longitude=6.2, latitude=53.413, altitude=2.9, name="LAUWERSOOG"
    ),
    278: _Station(
        number=278, longitude=6.259, latitude=52.435, altitude=3.6, name="HEINO"
    ),
    279: _Station(
        number=279, longitude=6.574, latitude=52.75, altitude=15.8, name="HOOGEVEEN"
    ),
    280: _Station(
        number=280, longitude=6.585, latitude=53.125, altitude=5.2, name="EELDE"
    ),
    283: _Station(
        number=283, longitude=6.657, latitude=52.069, altitude=29.1, name="HUPSEL"
    ),
    285: _Station(
        number=285, longitude=6.399, latitude=53.575, altitude=0.0, name="HUIBERTGAT"
    ),
    286: _Station(
        number=286, longitude=7.15, latitude=53.196, altitude=-0.2, name="NIEUW BEERTA"
    ),
    290: _Station(
        number=290, longitude=6.891, latitude=52.274, altitude=34.8, name="TWENTHE"
    ),
    300: _Station(
        number=300,
        longitude=2.567,
        latitude=51.65,
        altitude=999.9,
        name="LICHTSCHIP NOORDHINDER",
    ),
    308: _Station(
        number=308, longitude=3.379, latitude=51.381, altitude=0.0, name="CADZAND"
    ),
    310: _Station(
        number=310, longitude=3.596, latitude=51.442, altitude=8.0, name="VLISSINGEN"
    ),
    311: _Station(
        number=311, longitude=3.672, latitude=51.379, altitude=0.0, name="HOOFDPLAAT"
    ),
    312: _Station(
        number=312, longitude=3.622, latitude=51.768, altitude=0.0, name="OOSTERSCHELDE"
    ),
    313: _Station(
        number=313,
        longitude=3.242,
        latitude=51.505,
        altitude=0.0,
        name="VLAKTE V.D. RAAN",
    ),
    315: _Station(
        number=315, longitude=3.998, latitude=51.447, altitude=0.0, name="HANSWEERT"
    ),
    316: _Station(
        number=316, longitude=3.694, latitude=51.657, altitude=0.0, name="SCHAAR"
    ),
    319: _Station(
        number=319, longitude=3.861, latitude=51.226, altitude=1.7, name="WESTDORPE"
    ),
    320: _Station(
        number=320,
        longitude=3.67,
        latitude=51.927,
        altitude=22.0,
        name="LICHTEILAND GOEREE",
    ),
    321: _Station(
        number=321, longitude=3.275, latitude=51.999, altitude=19.0, name="EUROPLATFORM"
    ),
    323: _Station(
        number=323,
        longitude=3.884,
        latitude=51.527,
        altitude=1.4,
        name="WILHELMINADORP",
    ),
    324: _Station(
        number=324, longitude=4.006, latitude=51.596, altitude=0.0, name="STAVENISSE"
    ),
    325: _Station(
        number=325, longitude=3.931, latitude=51.654, altitude=-4.0, name="ZIERIKZEE"
    ),
    328: _Station(
        number=328, longitude=3.821, latitude=51.668, altitude=999.9, name="ROGGENPLAAT"
    ),
    330: _Station(
        number=330,
        longitude=4.122,
        latitude=51.992,
        altitude=11.9,
        name="HOEK VAN HOLLAND",
    ),
    331: _Station(
        number=331, longitude=4.193, latitude=51.48, altitude=0.0, name="THOLEN"
    ),
    340: _Station(
        number=340, longitude=4.342, latitude=51.449, altitude=19.2, name="WOENSDRECHT"
    ),
    343: _Station(
        number=343,
        longitude=4.313,
        latitude=51.893,
        altitude=3.5,
        name="R'DAM-GEULHAVEN",
    ),
    344: _Station(
        number=344, longitude=4.447, latitude=51.962, altitude=-4.3, name="ROTTERDAM"
    ),
    348: _Station(
        number=348, longitude=4.926, latitude=51.97, altitude=-0.7, name="CABAUW"
    ),
    350: _Station(
        number=350, longitude=4.936, latitude=51.566, altitude=14.9, name="GILZE-RIJEN"
    ),
    356: _Station(
        number=356, longitude=5.146, latitude=51.859, altitude=0.7, name="HERWIJNEN"
    ),
    370: _Station(
        number=370, longitude=5.377, latitude=51.451, altitude=22.6, name="EINDHOVEN"
    ),
    375: _Station(
        number=375, longitude=5.707, latitude=51.659, altitude=22.0, name="VOLKEL"
    ),
    377: _Station(
        number=377, longitude=5.763, latitude=51.198, altitude=30.0, name="ELL"
    ),
    379: _Station(
        number=379, longitude=5.7, latitude=50.794, altitude=42.0, name="OOST-MAARLAND"
    ),
    380: _Station(
        number=380, longitude=5.762, latitude=50.906, altitude=114.3, name="MAASTRICHT"
    ),
    385: _Station(
        number=385, longitude=5.933, latitude=51.55, altitude=9999.9, name="DE PEEL"
    ),
    391: _Station(
        number=391, longitude=6.197, latitude=51.498, altitude=19.5, name="ARCEN"
    ),
    550: _Station(
        number=550, longitude=3.22, latitude=53.218, altitude=999.9, name="K13"
    ),
    551: _Station(
        number=551, longitude=2.066, latitude=56.4, altitude=999.9, name="AUK"
    ),
    552: _Station(
        number=552, longitude=3.213, latitude=56.547, altitude=999.9, name="EKOFISK"
    ),
    553: _Station(
        number=553,
        longitude=3.276,
        latitude=51.999,
        altitude=999.9,
        name="EUROPLATFORM",
    ),
    554: _Station(
        number=554,
        longitude=3.592,
        latitude=51.681,
        altitude=999.9,
        name="MEETPOST NOORDWIJK",
    ),
    603: _Station(
        number=603, longitude=6.189, latitude=52.311, altitude=999.9, name="DIEPENVEEN"
    ),
    604: _Station(
        number=604, longitude=6.262, latitude=52.435, altitude=1.4, name="HERWIJNEN"
    ),
    605: _Station(
        number=605, longitude=6.196, latitude=53.409, altitude=3.0, name="LAUWERSOOG"
    ),
    609: _Station(
        number=609,
        longitude=4.318,
        latitude=51.891,
        altitude=999.9,
        name="R'DAM-GEULHAVEN",
    ),
    614: _Station(
        number=614, longitude=6.92, latitude=53.337, altitude=999.9, name="EEMSHAVEN"
    ),
    615: _Station(
        number=615, longitude=4.296, latitude=52.274, altitude=12.0, name="HOOGEVEEN"
    ),
    616: _Station(
        number=616,
        longitude=4.907,
        latitude=52.367,
        altitude=999.9,
        name="AMSTERDAM (COENHAVEN)",
    ),
    617: _Station(
        number=617, longitude=6.196, latitude=51.498, altitude=19.0, name="ARCEN"
    ),
    995: _Station(
        number=995,
        longitude=3.596,
        latitude=51.442,
        altitude=8.0,
        name="VLISSINGEN (TEST)",
    ),
    998: _Station(
        number=998,
        longitude=5.177,
        latitude=52.101,
        altitude=2.0,
        name="DE BILT (TEST)",
    ),
    999: _Station(
        number=999,
        longitude=6.575,
        latitude=52.75,
        altitude=15.6,
        name="HOOGEVEEN TEST",
    ),
    917536001: _Station(
        number=917536001,
        longitude=5.762,
        latitude=50.905,
        altitude=113,
        name="MAASTRICHT-AACHEN AIRPORT",
    ),
}


# convert to data frame
_stations_df = pd.DataFrame(_stations).transpose()
_stations_df.index.name = "STN"
_stations_df.columns = ["STN", "lon", "lat", "alt", "name"]


# filter on prediction and models
def filter_stations(stns):
    filtered_stations: pd.DataFrame = _stations_df.copy(deep=True)
    filtered_stations.set_index("STN", inplace=True)
    filtered_stations = filtered_stations.loc[stns, :]
    filtered_stations.reset_index(level=0, inplace=True)
    return filtered_stations


# filter
_stations_prediction_idx = np.array(
    [260, 235, 280, 270, 380, 240, 290, 310], dtype=np.int64
)

_stations_history_idx = np.array(
    [
        209,
        215,
        225,
        235,
        240,
        242,
        248,
        249,
        251,
        257,
        258,
        260,
        267,
        269,
        270,
        273,
        275,
        277,
        278,
        279,
        280,
        283,
        285,
        286,
        290,
        308,
        310,
        312,
        313,
        315,
        316,
        319,
        323,
        324,
        330,
        331,
        340,
        343,
        344,
        348,
        350,
        356,
        370,
        375,
        377,
        380,
        391,
    ],
    dtype=np.int64,
)

_stations_actual_idx = np.array(
    [
        8,
        17,
        153,
        215,
        225,
        229,
        230,
        240,
        242,
        249,
        250,
        257,
        258,
        260,
        270,
        273,
        275,
        277,
        278,
        280,
        283,
        286,
        290,
        310,
        319,
        330,
        340,
        344,
        348,
        350,
        356,
        370,
        375,
        377,
        391,
        615,
        917536001,
    ],
    dtype=np.int64,
)


stations_prediction = filter_stations(_stations_prediction_idx)
stations_history = filter_stations(_stations_history_idx)
stations_actual = filter_stations(_stations_actual_idx)

stations_actual_reversed = {
    s["name"]: s["STN"] for s in stations_actual.reset_index().to_dict(orient="records")
}
stations_actual_reversed["TWENTE"] = stations_actual_reversed["TWENTHE"]
stations_actual_reversed["TEXELHORS"] = stations_actual_reversed["TEXELHORS MM"]
stations_actual_reversed["GILZE RIJEN"] = stations_actual_reversed["GILZE-RIJEN"]

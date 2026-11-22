import numpy as np, pickle, colorsys
meta = pickle.load(open('/tmp/claude-0/-home-user/972dab79-8ec0-567e-9dbe-b1d16b78ca89/scratchpad/pc/meta.pkl','rb'))
NAMES = ["Anduin Banks","Campsite","Corsair Camp","Corsair Chase","Top Room","Tower","Ambush","Cirith Campsite","Ledge","Parapet","Pass","Lair Campsite","Stairs","Summit","Above","Below","Crack of Doom","Edge of Volcano","Tunnel","Campsite","Dwimerberg Base","Dwimerberg Mt.","Glen","Road","Anduin Docks","Minas Tirith Docks","Campsite","Foot of Mt Doom","Sammath Naur","Slopes of Mt Doom","Camps","Campsite","Hills","Hollow","Plateau","River Crossing","Campsite","Clearing","Copse","Entwash","Campsite","Hills","Orc Road","Plains","Campsite","Caverns","Fortress","Valley","Ice Caves","Balin's Tomb","Campsite","Flooded Field","Uruk Hatchery","Orthanc","Orthanc Tunnel","Tower Base","Tower Door","Tower Levels","Black Gate","Black Road","North","Waterfall","Battlements","Court of Kings","Gates","City Center","Streets","Steward's Tomb","Denethor Fall","Gates","Minas City Center","Streets","Tier Four","Tier Three","Bridge","Campsite","Crossroads","Gate","Minas Morgul","Vale of Morgul","Valley","Hall","Hall Top","Long Stairs","Treasure Hoards","Black Chasm","Campsite","Dark Paths","Grey Vapors","Secret Cave","West Beacon","East Beacon","Minas Entrance","Edge","Fall of Rohirrim","North Fields","Hidden Plains","West Fields","Witch King","Mumakil Attack","Campsite","Theoden's Charge","Footpath","Fork","Haradrim Camp","Mt. Mindolluin","Mumakil Camp","Outpost","Campsite","Edoras Fields","Gap","Deeping Outskirts","Hills","Plains","Snowbourne Trail","Caves","Lair","Tunnel Mouth","Campsite","Hills","Marsh","Tower","Approach","Campsite","Edge","Foothills","Narrow Pass","SE Mts. Edge","Hidden Trail","Storm"]
REG = [[0,3,"Anduin River"],[4,5,"Orc Tower"],[6,13,"Cirith Ungol"],[14,15,"Corsair Flagship"],[16,18,"Crack of Doom"],[19,23,"Dimholt"],[24,25,"Docks"],[26,29,"Mt Doom"],[30,35,"Dunharrow"],[36,39,"Entwood"],[40,43,"Gorgoroth"],[44,47,"Hornburg"],[48,49,"Ice Cave"],[50,57,"Isengard"],[58,61,"Ithilien"],[62,67,"Minas Tirith"],[68,68,"Balcony"],[69,73,"Minas Tirith"],[74,80,"Morgul"],[81,84,"Dwarf Halls"],[85,89,"Paths of the Dead"],[90,92,"Pelennor Beacon"],[93,98,"Pelennor Battle"],[99,107,"Pelennor Fields"],[108,114,"Rohan"],[115,117,"Shelob's Lair"],[118,121,"Amon Sul"],[122,129,"White Mountains"]]
def region(l):
    for a,b,n in REG:
        if a<=l<=b: return n
def rgb(pal):
    P = np.asarray(pal, np.int32)
    c = np.stack([(P & 31), (P >> 5) & 31, (P >> 10) & 31], 1)
    return (c * 255 // 31).astype(np.uint8)
def to555(c):
    c = np.clip(np.round(np.asarray(c, float) * 31 / 255), 0, 31).astype(np.int32)
    return (c[..., 0] | c[..., 1] << 5 | c[..., 2] << 10).astype(np.uint16)
def load(L): return np.load('/tmp/claude-0/-home-user/972dab79-8ec0-567e-9dbe-b1d16b78ca89/scratchpad/pc/idx/%d.npy' % L)
def paint(idx, pal): return rgb(pal)[idx]
# OKLab
def srgb2lin(c):
    c = np.asarray(c, float) / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin2srgb(c):
    c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255
M1 = np.array([[0.4122214708,0.5363325363,0.0514459929],[0.2119034982,0.6806995451,0.1073969566],[0.0883024619,0.2817188376,0.6299787005]])
M2 = np.array([[0.2104542553,0.7936177850,-0.0040720468],[1.9779984951,-2.4285922050,0.4505937099],[0.0259040371,0.7827717662,-0.8086757660]])
def oklab(c):
    l = srgb2lin(c) @ M1.T; return np.cbrt(l) @ M2.T
def from_oklab(lab):
    l = lab @ np.linalg.inv(M2).T; return lin2srgb((l ** 3) @ np.linalg.inv(M1).T)
def lch(c):
    lab = oklab(c); return lab[..., 0], np.hypot(lab[..., 1], lab[..., 2]), np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360

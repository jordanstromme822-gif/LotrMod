# Lore colour plans. Rules work in OKLCH; value (lightness) is kept unless ls/lo say otherwise.
PINK = dict(h=0, w=28, f=12, cmin=0.012)          # mauve / pink / rose band (332..28)
VIOLET = dict(h=300, w=40, f=15, cmin=0.012)       # violet / purple band (260..340)
def R(base, **k): d = dict(base); d.update(k); return d
DUNHARROW_A = {   # Harrowdale at the muster: trampled brown earth, green-gold Rohan grass, dark pines, grey mountain stone, pale canvas
    'banks': {
        8: [dict(ent=(1, 10), to=68, cset=0.045, ls=0.97, cmin=0), dict(ent=(11, 15), to=92, cs=1.5, cmin=0.01)],
        3: [dict(to=90, cs=1.3, cmin=0.01)],
        4: [R(PINK, to=150, cset=0.035, ls=0.95, lmax=0.5), R(PINK, to=68, cset=0.045, lmin=0.5), dict(h=60, w=40, f=10, to=130, cset=0.03, lmax=0.5)],
        5: [R(PINK, to=125, cs=1.0, cset=0.07), dict(h=80, w=30, f=10, to=115, cs=1.2)],
        7: [R(PINK, to=66, cset=0.042), R(dict(h=38, w=14, f=8), to=70, cs=1.0)],
        10: [R(PINK, to=80, cset=0.014)],
        13: [R(PINK, to=85, cset=0.025, ls=1.0)],
        12: [R(PINK, to=68, cset=0.04), R(VIOLET, to=68, cset=0.02)],
        14: [R(PINK, to=60, cset=0.03)],
        6: [R(PINK, to=92, cset=0.05)],
        15: [R(PINK, to=70, cset=0.03), R(VIOLET, to=230, cs=1.0)],
        11: [R(PINK, to=85, cset=0.025, lmin=0.78), R(PINK, to=66, cset=0.042, lmax=0.78), R(VIOLET, to=66, cset=0.02), R(dict(h=40, w=20, f=8), to=92, cs=1.5)],
    },
    'default': [R(PINK, to=68, cset=0.04)],
}
MORGUL_A = {   # Imlad Morgul: pale corpse-light, ghost-green haze over the vale (no rose or violet)
    'banks': {
        11: [dict(cmin=0, lmin=0.84, to=140, cset=0.05, ls=0.84), dict(cmin=0, lmax=0.84, to=170, cset=0.026, ls=0.58)],
        10: [dict(cmin=0.012, to=165, cset=0.022, ls=0.88)],
        4: [dict(h=300, w=30, f=10, cmin=0.005, to=200, cs=0.35)],
    },
}
MORGUL_B = {   # the Shadow of Mordor: smoke-brown sky, dim ember glow
    'banks': {
        11: [dict(cmin=0, lmin=0.84, to=55, cset=0.09, ls=0.8), dict(cmin=0, lmax=0.84, to=60, cset=0.016, ls=0.56)],
        10: [dict(cmin=0.012, to=70, cset=0.014, ls=0.85)],
        4: [dict(h=300, w=30, f=10, cmin=0.005, to=80, cs=0.35)],
    },
}

COOL = dict(h=290, w=62, f=18, cmin=0.006)        # 210..10: blue-violet, violet, mauve
DUNHARROW_B = {   # same, but the trampled ground is the green turf of the Firienfeld
    'banks': dict(DUNHARROW_A['banks']),
    'default': DUNHARROW_A['default'],
}
DUNHARROW_B['banks'][8] = [dict(ent=(1, 10), to=112, cset=0.05, ls=0.95, cmin=0), dict(ent=(11, 15), to=92, cs=1.5, cmin=0.01)]
DUNHARROW_B['banks'][7] = [R(PINK, to=90, cset=0.04), R(dict(h=38, w=14, f=8), to=80, cs=1.0)]
DUNHARROW_B['banks'][11] = [R(PINK, to=85, cset=0.025, lmin=0.78), R(PINK, to=105, cset=0.045, lmax=0.78), R(VIOLET, to=105, cset=0.02), R(dict(h=40, w=20, f=8), to=92, cs=1.5)]

ISENGARD_A = {    # Isengard laid waste: soot, ash and rust, grey flood water
    'default': [dict(h=300, w=78, f=14, cmin=0, cmax=0.045, to=62, cset=0.016), R(COOL, to=55, cs=1.0, cmin=0.04)],
    'banks_by_pal': {0x894722c: {10: [dict(cmin=0, to=150, cset=0.018, ls=0.86)]}},
}
ISENGARD_B = {    # cold iron and wet slate
    'default': [dict(h=300, w=78, f=14, cmin=0, cmax=0.045, to=230, cset=0.004), R(COOL, to=230, cs=0.5, cmin=0.04)],
    'banks_by_pal': {0x894722c: {10: [dict(cmin=0, to=225, cset=0.02, ls=0.82)]}},
}
GORGOROTH_A = {   # plateau of Gorgoroth: ash-grey reek, dull red glare under the cloud
    'default': [R(COOL, w=70, to=55, cset=0.02, ls=0.92), R(PINK, to=35, cs=0.8, cmin=0.06, ls=0.95)],
}
GORGOROTH_B = {   # lit by the fires of Orodruin: smoke lit rust-red from below
    'default': [R(COOL, w=70, to=40, cset=0.035, ls=0.85), R(PINK, to=32, cs=1.0, cmin=0.06)],
}
SHELOB_A = {      # Torech Ungol: black-grey stone, cold and dead
    'default': [R(COOL, w=70, to=75, cset=0.01, ls=0.9)],
}
SHELOB_B = {      # faint sickly green-grey reek of the lair
    'default': [R(COOL, w=70, to=125, cset=0.02, ls=0.88)],
}
ICE_A = {'default': [R(COOL, w=50, h=300, to=232, cs=0.9)]}           # blue-white ice
ICE_B = {'default': [R(COOL, w=50, h=300, to=210, cs=0.6, ls=1.02)]}  # glacier grey-cyan
MORIA_A = {'default': [R(COOL, h=300, w=55, to=75, cset=0.008)]}      # plain dark granite
MORIA_B = {'default': [R(COOL, h=300, w=55, to=230, cs=0.5)]}         # cold blue-grey stone
DEAD_A = {'banks': {11: [dict(cmin=0.01, to=160, cs=0.45, ls=0.95)]}}  # pale grey-green ghost light
DEAD_B = {'banks': {11: [dict(cmin=0.01, to=235, cs=0.3, ls=0.9)]}}   # cold dead blue-grey
BALCONY_A = {'banks': {3: [dict(cmin=0.01, to=55, cs=0.6, ls=0.88), dict(h=0, w=30, f=10, cmin=0.06, to=40, cs=0.9)]}}   # smoke over the burning city
BALCONY_B = {'banks': {3: [dict(cmin=0.01, to=85, cs=0.7, ls=0.97), dict(h=0, w=30, f=10, cmin=0.06, to=70, cs=0.9)]}}   # pale gold dawn (the Rohirrim come)
SNOW_A = {'banks': {15: [dict(h=0, w=45, f=15, cmin=0.03, to=60, cs=0.55), R(COOL, to=245, cs=0.8)]}}   # winter dusk: pale gold over steel-blue cloud
SNOW_B = {'banks': {15: [dict(h=0, w=45, f=15, cmin=0.03, to=25, cs=0.75), R(COOL, to=250, cs=0.8)]}}   # keep a warm sunset, but orange not pink

WARMCOOL = dict(h=305, w=50, f=12, cmin=0.006)   # 255..355 only (keeps teal/blue things)
GORGOROTH_A = {'default': [R(WARMCOOL, to=55, cset=0.02, ls=0.92), R(PINK, w=20, to=40, cs=0.8, cmin=0.05, ls=0.95)]}
GORGOROTH_B = {'default': [R(WARMCOOL, to=48, cset=0.04, ls=0.86), R(PINK, w=20, to=38, cs=1.0, cmin=0.05)]}
SNOW_A = {'banks': {15: [dict(h=5, w=40, f=15, cmin=0.03, to=78, cs=0.4, ls=1.04), R(COOL, w=40, h=290, to=245, cs=0.7)]}}
SNOW_B = {'banks': {15: [dict(h=5, w=40, f=15, cmin=0.03, to=42, cs=0.85), R(COOL, w=40, h=290, to=250, cs=0.8)]}}
GORGOROTH_A = {'default': [R(WARMCOOL, to=55, cset=0.02, ls=0.92)],
               'banks': {3: [dict(cmin=0.006, to=62, cset=0.018, ls=0.9)], 11: [R(WARMCOOL, to=55, cset=0.02, ls=0.92), R(PINK, w=20, to=55, cset=0.02, cmin=0.05)]}}
GORGOROTH_B = {'default': [R(WARMCOOL, to=45, cset=0.04, ls=0.86)],
               'banks': {3: [dict(cmin=0.006, to=45, cset=0.045, ls=0.85)], 11: [R(WARMCOOL, to=45, cset=0.04, ls=0.86), R(PINK, w=20, to=40, cset=0.05, cmin=0.05)]}}
for _p in (SNOW_A, SNOW_B): _p['default'] = [dict(h=292, w=14, f=8, cmin=0.03, to=262, cs=1.0)]

# ---- organic pass: material ramps with natural light/shadow hue shifts, original variety kept ----
ANYC = dict(cmin=0.006)
def M_(mat, **k): d = dict(cmin=0.0, mat=mat); d.update(k); return d
DUNHARROW_O = {
    'banks': {
        8: [M_('turf-soil', ent=(1, 10), spread=0.3, ls=1.25, lo=-0.2), M_('straw', ent=(11, 15), ls=1.12, lo=-0.09)],
        3: [M_('straw', spread=0.3, ls=1.12, lo=-0.09)],
        4: [M_('pine', lmax=0.5), M_('earth', lmin=0.5)],
        5: [M_('leaf', h=0, w=60, f=20, spread=0.4), M_('leaf', h=80, w=30, f=10, spread=0.3)],
        7: [M_('shade-bank', spread=0.3)],
        10: [M_('granite', spread=0.3)],
        13: [M_('canvas', spread=0.3)],
        12: [M_('earth', spread=0.4)],
        14: [M_('earth-rich')],
        6: [M_('granite', ent=(1, 8), spread=0.2), M_('straw', ent=(9, 15), h=0, w=40, f=10)],
        15: [M_('earth', h=0, w=40, f=10), R(VIOLET, to=230, cs=1.0)],
        11: [M_('turf', ent=(1, 10), h=0, w=40, f=10), M_('drygrass', ent=(1, 10), h=60, w=40, f=10), M_('canvas', ent=(11, 14)), R(VIOLET, to=105, cset=0.02)],
    },
    'default': [M_('earth', h=0, w=40, f=10)],
    'anchor': [8, 3], 'no_anchor': (13, 10, 4, 5, 11, 6),
}
MORGUL_O = {'banks': {
    11: [dict(cmin=0, mat='night-haze', ls=0.95, lo=-0.24, spread=0.0, cs=1.3)],
    10: [dict(cmin=0.0, mat='night-haze', ls=0.85, spread=0.2)],
    4: [dict(h=300, w=30, f=10, cmin=0.005, to=200, cs=0.35)],
    14: [dict(cmin=0.0, mat='dead-water', spread=0.4)]}}
ISENGARD_O = {
    'default': [dict(h=300, w=78, f=14, cmin=0, cmax=0.045, mat='soot', spread=0.3), dict(COOL, mat='ember', cmin=0.04, spread=0.2)],
    'banks_by_pal': {0x894722c: {10: [dict(cmin=0, mat='mud-water', ls=0.9, spread=0.3)]}},
}
GORGOROTH_O = {'default': [dict(WARMCOOL, mat='reek', spread=0.3, ls=0.95)],
               'banks': {3: [dict(cmin=0.0, mat='ash-sky', spread=0.3, ls=0.92)], 11: [dict(WARMCOOL, mat='reek', ls=0.95), dict(PINK, w=20, cmin=0.05, mat='ash-sky')]}}
SHELOB_O = {'default': [dict(COOL, w=70, mat='lair-stone', spread=0.3, ls=0.92)]}
ICE_O = {'default': [dict(COOL, w=50, h=300, mat='ice', spread=0.3)]}
DEAD_O = {'banks': {11: [dict(cmin=0.01, mat='ghost', spread=0.3)]}}
SNOW_O = {'banks': {15: [dict(h=5, w=40, f=15, cmin=0.03, mat='dusk-sky', spread=0.2), dict(COOL, w=40, h=290, to=250, cs=0.8)]},
          'default': [dict(h=292, w=14, f=8, cmin=0.03, to=262, cs=1.0)]}
BALCONY_O = {'banks': {3: [dict(cmin=0.01, mat='smoke-glow', spread=0.3)]}}

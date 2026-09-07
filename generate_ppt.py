"""
PPT generáló szkript – Műholdas kvantumkommunikáció önálló labor prezentáció.
Futtatás: .venv/Scripts/python generate_ppt.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import pptx.oxml.ns as nsmap
from lxml import etree

# ── Színek ──────────────────────────────────────────────────────────────────
BME_BLUE   = RGBColor(0x00, 0x37, 0x7F)   # BME sötétkék
LIGHT_BLUE = RGBColor(0x00, 0x7A, 0xC2)   # Világoskék hangsúlyokhoz
GRAY       = RGBColor(0x55, 0x55, 0x55)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF0, 0xF0, 0xF0)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# ── Segédfüggvények ──────────────────────────────────────────────────────────

def add_rect(slide, l, t, w, h, fill=None, line=None):
    shape = slide.shapes.add_shape(
        pptx.enum.shapes.MSO_SHAPE_TYPE.AUTO_SHAPE if False else 1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(l), Inches(t), Inches(w), Inches(h)
    )
    shape.line.fill.background() if line is None else None
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line is None:
        shape.line.fill.background()
    return shape


def add_textbox(slide, text, l, t, w, h,
                font_size=18, bold=False, color=None,
                align=PP_ALIGN.LEFT, wrap=True, italic=False):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    return tb


def add_bullet_textbox(slide, items, l, t, w, h,
                       font_size=16, title=None, title_size=18):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True

    if title:
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = title
        run.font.size = Pt(title_size)
        run.font.bold = True
        run.font.color.rgb = BME_BLUE
    else:
        first = True

    for item in items:
        if title or not (title is None and item == items[0]):
            p = tf.add_paragraph()
        else:
            p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        p.level = 0
        run = p.add_run()
        run.text = f"▪  {item}"
        run.font.size = Pt(font_size)
        run.font.color.rgb = GRAY
    return tb


def add_header_bar(slide, text, subtitle=None):
    """Kék fejléc sáv a dia tetején."""
    rect = add_rect(slide, 0, 0, 13.33, 1.15, fill=BME_BLUE)
    add_textbox(slide, text, 0.3, 0.08, 12.0, 0.7,
                font_size=28, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    if subtitle:
        add_textbox(slide, subtitle, 0.35, 0.72, 12.0, 0.38,
                    font_size=14, color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.LEFT)


def add_image_placeholder(slide, label, l, t, w, h):
    """Szürke képhelyőrző (ide kell majd beilleszteni a screenshotot)."""
    rect = add_rect(slide, l, t, w, h, fill=LIGHT_GRAY)
    rect.line.color.rgb = LIGHT_BLUE
    rect.line.width = Pt(1.5)
    add_textbox(slide, f"[ Screenshot: {label} ]",
                l + 0.1, t + h / 2 - 0.25, w - 0.2, 0.5,
                font_size=12, color=GRAY, align=PP_ALIGN.CENTER, italic=True)


def add_formula_box(slide, text, l, t, w, h):
    """Formuladoboz halvány kék háttérrel."""
    rect = add_rect(slide, l, t, w, h, fill=RGBColor(0xE8, 0xF2, 0xFF))
    rect.line.color.rgb = LIGHT_BLUE
    rect.line.width = Pt(1)
    add_textbox(slide, text, l + 0.1, t + 0.05, w - 0.2, h - 0.1,
                font_size=13, color=BME_BLUE, align=PP_ALIGN.LEFT)


def set_notes(slide, text):
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = text


# ── Prezentáció ─────────────────────────────────────────────────────────────

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

blank_layout = prs.slide_layouts[6]  # teljesen üres layout

# ════════════════════════════════════════════════════════════════════════════
# 1. DIA – Cím
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)

add_rect(slide, 0, 0, 13.33, 7.5, fill=BME_BLUE)
add_rect(slide, 0, 5.2, 13.33, 2.3, fill=RGBColor(0x00, 0x28, 0x60))

add_textbox(slide,
    "Műholdas kvantumkommunikáció",
    1.0, 1.0, 11.33, 1.0,
    font_size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_textbox(slide,
    "Szimulációs prototípus időindexelt kvantumhálózat modellezésre",
    1.0, 2.0, 11.33, 0.7,
    font_size=20, color=RGBColor(0xAA, 0xCC, 0xFF), align=PP_ALIGN.CENTER)

add_textbox(slide,
    "Horváth Péter  |  I17R50  |  HIT szakirány",
    1.0, 3.1, 11.33, 0.55,
    font_size=18, color=WHITE, align=PP_ALIGN.CENTER)

add_textbox(slide,
    "Konzulens: Mihály András  |  Hálózati Rendszerek és Szolgáltatások Tanszék",
    1.0, 3.65, 11.33, 0.55,
    font_size=15, color=RGBColor(0xAA, 0xCC, 0xFF), align=PP_ALIGN.CENTER)

add_textbox(slide,
    "Önálló laboratórium  –  2025/2026. 2. félév",
    1.0, 6.1, 11.33, 0.55,
    font_size=14, color=RGBColor(0xAA, 0xCC, 0xFF), align=PP_ALIGN.CENTER)

set_notes(slide, """Üdvözlöm a hallgatóságot. Horváth Péter vagyok, I17R50 Neptun-kóddal, HIT szakirányon tanulok.
Ez az önálló laboratóriumi munkám bemutatója, amelynek témája műholdas kvantumkommunikáció szimulációs prototípus fejlesztése.
A konzulensem Mihály András a HIT Tanszékről.
A prezentáció kb. 5-6 percet vesz igénybe.""")

# ════════════════════════════════════════════════════════════════════════════
# 2. DIA – Motiváció és célkitűzés
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "Motiváció és célkitűzés",
               "Miért érdekes a műholdas QKD?")

# Bal oszlop – szöveg
add_bullet_textbox(slide, [
    "A kvantumkulcs-elosztás (QKD) informatikai-elméleti biztonságot nyújt",
    "Szálfény alapú QKD: ~100 km korlát a veszteségek miatt",
    "Műholdas szabadterű optikai link kiterjeszti a hatótávot",
    "A hálózat idővariáns: kapcsolatok csak meghatározott időablakokban léteznek",
    "Cél: szimulációs prototípus, amely geometriát, link-modellt és QKD-rátát összekapcsol",
], 0.4, 1.3, 6.5, 5.8, font_size=17)

# Jobb oszlop – ábra
add_image_placeholder(slide, "2D térkép – aktív linkekkel", 7.2, 1.3, 5.8, 5.7)

set_notes(slide, """A kvantumkulcs-elosztás alapötlete, hogy kvantummechanikai elvek alapján garantáltan biztonságos kulcsot lehet kiosztani két fél között.
A szálfényes megoldásoknál a maximális hatótáv kb. 100 km, mert a jelcsillapítás legyőzhetetlen.
Műholdakkal ez a korlát feloldható: egy alacsony pályán keringő műhold a légkör fölötti szabad tér optikai csatornán keresztül összeköthet két kontinenst.
A kihívás, hogy a műholdak mozgása miatt a hálózat topológiája percről percre változik.
A félév célja egy olyan szimulációs prototípus volt, amely valós TLE pályaadatokból indulva, optikai linkmodellen és QKD kulcsrátaszámításon keresztül időindexelt hálózati gráfot épít fel.""")

# ════════════════════════════════════════════════════════════════════════════
# 3. DIA – Szimulátor felépítése
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "A szimulátor felépítése")

# Pipeline dobozok
boxes = [
    ("TLE adatok\n(Celestrak)", 0.3),
    ("Pályaszámítás\nSGP4 / Skyfield", 2.3),
    ("Optikai link\nmodell", 4.3),
    ("QKD kulcsráta\nmodell (ESKR)", 6.3),
    ("Temporális\nélgráf (cache)", 8.3),
    ("Vizualizáció\n& elemzés", 10.3),
]
for label, x in boxes:
    r = add_rect(slide, x, 1.5, 1.85, 1.1, fill=BME_BLUE)
    add_textbox(slide, label, x + 0.05, 1.55, 1.75, 1.0,
                font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if x < 10.3:
        add_textbox(slide, "→", x + 1.85, 1.85, 0.45, 0.5,
                    font_size=22, bold=True, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)

# Modul lista
add_bullet_textbox(slide, [
    "simulation_config.py – konstelláció, földi állomások, időablak, modellparaméterek",
    "linkmodel.py – geometriai (1/d²) + légköri (Chapman) veszteség",
    "keyratamodel.py – fotonpár-ráta, QBER, SKR, ESKR; μ optimalizáció",
    "passdetector.py – elevációs küszöb alapú pass detektálás",
    "satlink.py – műhold-műhold távolság, LOS (line-sphere intersection)",
    "temporal_io.py – időindexelt élgráf építés, CSV cache, hash-alapú érvényesítés",
    "app.py + visualizer.py – Matplotlib GUI, 6 interaktív nézet",
], 0.3, 2.85, 12.7, 4.4, font_size=14)

set_notes(slide, """A szimulátor hat egymásra épülő lépésben dolgoz.
Először letölti az Iridium konstelláció TLE pályaelemeit a Celestrak adatbázisból.
A Skyfield könyvtár SGP4 modellel kiszámolja minden percben minden műhold pozícióját.
Az optikai linkmodell megbecsüli a csatorna hatásfokát: geometriai veszteség a távolság négyzetével, légköri veszteség Chapman-közelítéssel.
A QKD modell ebből ESKR-t számít, és megkeresi az optimális fotonpár-rátát.
Az eredmény egy időindexelt élgráfba kerül, amelyet cache-elünk, hogy ismételt futtatásnál ne kelljen mindent újraszámolni.
Végül a Matplotlib-alapú GUI 6 interaktív nézetben jeleníti meg az eredményeket.""")

# ════════════════════════════════════════════════════════════════════════════
# 4. DIA – Optikai link és QKD modell
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "Optikai link modell és QKD kulcsráta")

# Bal – formulák
add_textbox(slide, "Csatorna hatásfok (föld–műhold):", 0.4, 1.35, 6.2, 0.4,
            font_size=14, bold=True, color=BME_BLUE)
add_formula_box(slide,
    "η = (G / d²) · exp(−α / sin ε)\n\n"
    "d: távolság [m]   ε: elevációs szög\n"
    "G: összevont geometriai erősítés (G=10⁸)\n"
    "α: légköri veszteség paraméter (α=0,15)",
    0.4, 1.75, 6.2, 1.4)

add_textbox(slide, "QKD kulcsráta (entanglement-forrás modell):", 0.4, 3.25, 6.2, 0.4,
            font_size=14, bold=True, color=BME_BLUE)
add_formula_box(slide,
    "C_true = R_pair · η_A · η_B\n"
    "C_acc  = S_A · S_B · τ\n"
    "QBER = (e_det · C_true + 0.5 · C_acc) / C_raw\n\n"
    "ESKR = (1 − f_int) · q_sift · C_raw · max(0, 1 − f_ec·h₂(QBER) − h₂(QBER))\n\n"
    "μ optimalizáció: minden csatornához megkeresi a max ESKR-t adó μ-t",
    0.4, 3.65, 6.2, 2.5)

# Jobb – kulcsráta görbe placeholder
add_image_placeholder(slide, "ESKR görbék – fotonpár-ráta vs. ESKR\n(single-link és dual-downlink)", 6.9, 1.35, 6.1, 4.9)

set_notes(slide, """Az optikai linkmodell két tagból áll.
A geometriai veszteség a távolság négyzetével arányos – ez a szabad tér diffrakciójának egyszerűsített közelítése.
A légköri veszteség a Chapman-függvénnyel adott: alacsony elevációnál a jel hosszabb utat tesz meg a légkörben, ezért a csillapítás nagyobb.
A QKD modell entanglement-alapú forrást feltételez. A valódi egybeesések rátája a csatorna hatásfokától függ, a véletlen egybeesések (accidentals) pedig a háttérzajból és a számlálási rátákból adódnak.
A QBER a véletlen egybeesések arányától nő. Az ESKR a BB84 protokoll bináris entrópia alapú kulcstöredékével számolt biztonságos kulcsráta, csökkentve a belső rendszerhasználattal.
Lényeges eredmény: a fotonpár-rátának veszteségfüggő optimuma van – ahogy Ecker és szerzőtársai is megmutatták. A program ezt automatikusan keresi meg.""")

# ════════════════════════════════════════════════════════════════════════════
# 5. DIA – Hálózati topológia és pass-detektálás
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "Idővariáns hálózati topológia",
               "Műhold-földiállomás és műhold-műhold kapcsolatok")

# Bal – szöveg
add_bullet_textbox(slide, [
    "Minden percben külön hálózati pillanatkép (snapshot-gráf)",
    "Csomópontok: műholdak + földi állomások",
    "Élek súlya: ESKR [bit/s]",
    "Műhold–GS link: elevációs küszöb (≥ 20°)",
    "Műhold–műhold ISL: távolságkorlát (≤ 4000 km) + LOS ellenőrzés",
    "LOS: line-sphere intersection – kizárja Föld által takart pályákat",
    "Cache: konfigurációfüggő SHA-256 hash, CSV formátum",
], 0.4, 1.3, 6.3, 5.7, font_size=16)

# Jobb – topológia placeholder
add_image_placeholder(slide, "Temporal Network Topology nézet\n(műholdak körön, GS belül)", 6.9, 1.35, 6.1, 5.8)

set_notes(slide, """A hálózat idővariáns: a műholdak mozgása miatt percenként más a topológia.
A program ezért minden időlépéshez külön NetworkX gráfot épít.
A műhold-földiállomás kapcsolatnál a feltétel az elevációs küszöb: legalább 20 fok szükséges, hogy a légköri csillapítás ne legyen túl nagy.
A műhold-műhold linkek esetén két feltétel érvényes: a távolság legfeljebb 4000 km lehet, és közvetlen optikai rálátás szükséges.
A rálátás vizsgálata line-sphere intersection módszerrel történik: ha a két műholdot összekötő egyenes szegmens metszi a Föld gömbjét, nincs összeköttetés.
Az összes számítás eredménye egy időindexelt él-táblába kerül, amelyet CSV fájlban cache-elünk. A cache hash-alapú: ha a konfiguráció megváltozik, automatikusan újragenerálódik.""")

# ════════════════════════════════════════════════════════════════════════════
# 6. DIA – End-to-end ESKR és max-flow elemzés
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "End-to-end ESKR – maximális folyam elemzés")

# Bal felső – szöveg
add_bullet_textbox(slide, [
    "Minden időlépésben irányított kapacitásgráf: él kapacitás = ESKR",
    "NetworkX maximum_flow algoritmus: max átvihető kulcsráta",
    "Minimum cut: szűk keresztmetszeteket tárja fel",
    "Összesített görbe: összes GS-pár max-flow értékének összege",
    "Budapest → N'Djamena: 280 aktív időlépés, ~7,18×10⁴ bit",
], 0.4, 1.3, 6.4, 3.0, font_size=15)

# Bal alsó placeholder
add_image_placeholder(slide, "Budapest → N'Djamena\nmax-flow ESKR idősor", 0.4, 4.05, 6.0, 3.1)

# Jobb – összesített ESKR placeholder
add_image_placeholder(slide, "Összesített GS-pár end-to-end ESKR\naz idő függvényében (log skála)", 6.7, 1.3, 6.3, 5.85)

set_notes(slide, """A hálózati szintű elemzés a maximális folyam algoritmust alkalmazza.
Minden időpillanatban irányított kapacitásgráfot építünk, ahol egy él kapacitása az adott pillanatban becsült ESKR.
Két kiválasztott földi állomás között a max-flow megadja, hogy összesen mekkora kulcsráta vihető át – akár több párhuzamos útvonalon keresztül.
A min-cut megmutatja, hogy melyik élek a szűk keresztmetszetek, vagyis amelyek eltávolítása megszüntetné a kapcsolatot.
Az összesített görbén látható erős ingadozás az idővariáns topológia következménye: amikor épp sok műhold van látható pozícióban, nagyobb a kapacitás.
Budapest és N'Djamena esetén a 24 órás szimulációban 280 perces aktív összeköttetés adódott, ami 7,18×10⁴ bit becsült kulcsmennyiséget jelent.""")

# ════════════════════════════════════════════════════════════════════════════
# 7. DIA – Vizualizációs nézetek
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "Vizualizációs nézetek – interaktív GUI")

# 2x2 rács placeholderekkel
add_image_placeholder(slide, "2D Satellite Constellation Map\n(animált, aktív linkekkel)", 0.3, 1.3, 6.1, 2.85)
add_image_placeholder(slide, "Elevation vs Time\n(csak passokkal rendelkező műholdak)", 6.7, 1.3, 6.3, 2.85)
add_image_placeholder(slide, "Network ESKR összeg – log skála", 0.3, 4.35, 6.1, 2.85)
add_image_placeholder(slide, "Budapest → N'Djamena Pair Flow", 6.7, 4.35, 6.3, 2.85)

# Kis feliratok a placeholderek alá
labels = [
    ("Térkép nézet", 0.3, 4.1, 3.0),
    ("Eleváció nézet", 6.7, 4.1, 3.0),
]
# (nem kell, a placeholder label már tartalmaz mindent)

set_notes(slide, """A GUI összesen hat nézetet tartalmaz, mindegyik a Főmenüből érhető el.
A 2D térképes nézetben valós időben látható, hogy a műholdak hol tartózkodnak, és melyiknek van épp aktív föld-kapcsolata.
Az eleváció-idősor nézet mutatja, hogy az egyes műholdak mikor kerülnek a láthatósági küszöb fölé az egyes állomásoknál.
A kulcsráta elemzési nézet az ESKR-görbéket mutatja a fotonpár-ráta függvényében, különböző veszteségi szinteken – egyedi link és szimmetrikus dual-downlink esetén.
A hálózati ESKR nézet az összes állomáspár end-to-end összkapacitását mutatja logaritmikus skálán.
A pair flow nézet egy kiválasztott állomáspár részletes elemzése max-flow algoritmussal.""")

# ════════════════════════════════════════════════════════════════════════════
# 8. DIA – Korlátok és kitekintés
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "Korlátok és továbbfejlesztési irányok")

# Bal – jelenlegi korlátok
add_bullet_textbox(slide, [
    "Geometriai gain (G=10⁸) összevont – nincs teleszkóp/apertura modell",
    "Légköri modell: Chapman-közelítés, derült ég, nincs turbulencia",
    "QKD modell: BB84 feltételezés, rögzített detektor paraméterek",
    "ISL kulcsráta: egyszerűsített, valódi optikai terminál nélkül",
    "Nincs store-and-forward temporális útvonalválasztás",
    "Összesített ESKR görbe: párhuzamos igények esetén túlbecslés lehetséges",
], 0.4, 1.35, 6.2, 4.8,
   font_size=15, title="Jelenlegi egyszerűsítések", title_size=16)

# Jobb – fejlesztési irányok
add_bullet_textbox(slide, [
    "Pontosabb link budget: apertura, divergencia, pointing error",
    "Légköri turbulencia, felhőzet hatása",
    "Decoy-state BB84 vagy más konkrét protokoll illesztése",
    "Store-and-forward temporális routing algoritmus",
    "Többforrású kapacitáselosztás (multi-commodity flow)",
    "UI-on keresztüli konfiguráció (konstelláció, időablak váltása)",
    "Valós mérési adatokhoz illesztett paraméterek",
], 6.7, 1.35, 6.3, 5.8,
   font_size=15, title="Lehetséges fejlesztések", title_size=16)

# Vízszintes elválasztó vonal
add_rect(slide, 0.4, 6.3, 12.5, 0.03, fill=LIGHT_BLUE)

set_notes(slide, """A prototípus tudatosan egyszerűsített – kutatási demonstrációra készült, nem éles alkalmazásnak.
A legfontosabb közelítések: a geometriai gain egy összevont paraméter, amelybe a teleszkóp, az optikai hatásfok és a nyalábdivergangia bele van sűrítve. A légköri modell derült égre vonatkozik, turbulenciát nem vesz figyelembe.
A QKD modell BB84-et feltételez szimmetrikus QBER-rel.
A hálózati elemzés pillanatképekkel dolgozik, nem valósít meg store-and-forward kulcstárolást.
A következő lépések között szerepelhetne pontosabb link budget modell, konkrét protokollhoz illesztett paraméterek, és temporális útvonalválasztó algoritmus.""")

# ════════════════════════════════════════════════════════════════════════════
# 9. DIA – Összefoglalás
# ════════════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)
add_header_bar(slide, "Összefoglalás")

add_bullet_textbox(slide, [
    "Valós TLE adatokon alapuló műholdkonstelláció-szimuláció (Iridium, 50 műhold, 6 GS, 24 h)",
    "Optikai linkmodell: geometriai veszteség + Chapman-féle légköri csillapítás",
    "QKD kulcsráta modell: QBER, SKR, ESKR; automatikus μ optimalizáció",
    "Temporális élgráf konfigurációfüggő hash-cache-szel (CSV, újraszámítás csak szükség esetén)",
    "Max-flow / min-cut alapú end-to-end kvantumkulcs-kapacitás elemzés",
    "6 interaktív Matplotlib nézet: térkép, hálózat, eleváció, kulcsráta, ESKR, pair flow",
    "Prototípus: az egymásra épülő vizsgálati szintek kialakítása volt a fő eredmény",
], 0.5, 1.35, 12.3, 4.6, font_size=17,
   title="Elvégzett munka és eredmények", title_size=19)

# Zárszó doboz
r = add_rect(slide, 0.5, 6.0, 12.3, 1.2, fill=RGBColor(0xE8, 0xF2, 0xFF))
r.line.color.rgb = BME_BLUE
r.line.width = Pt(1.5)
add_textbox(slide,
    "A prototípus alkalmas az idővariáns műholdas kvantumhálózat alapvető jelenségeinek "
    "bemutatására, és megfelelő kiindulópont a részletesebb fizikai modellezéshez és "
    "temporális útvonalválasztáshoz.",
    0.6, 6.1, 12.1, 1.0,
    font_size=14, color=BME_BLUE, align=PP_ALIGN.LEFT, italic=True)

set_notes(slide, """Összefoglalva: a félév során egy egyszerű műholdpálya-megjelenítő programból olyan szimulációs prototípust alakítottam ki, amely a geometriai adatokat optikai linkmodellel, QKD kulcsrátabecsléssel és időindexelt hálózati reprezentációval kapcsolja össze.
A legfontosabb eredmény nem egyetlen grafikon, hanem az egymásra épülő vizsgálati szintek: a térkép a geometriai helyzetet, a topológiai nézet a pillanatnyi hálózatot, a kulcsráta görbék a linkszintű modellt, az end-to-end grafikonok a hálózati kapacitást szemléltetik.
Köszönöm a figyelmet, szívesen válaszolok kérdésekre.""")

# ── Mentés ───────────────────────────────────────────────────────────────────
out = "prezentacio_muholdasQKD.pptx"
prs.save(out)
print(f"Saved: {out}")

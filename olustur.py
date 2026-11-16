#!/usr/bin/env python3
"""Bilinmeyen No - site oluşturucu.

numaralar.txt + yontemler.txt + ayarlar.txt dosyalarını okur,
_site/ klasörüne tüm sayfaları üretir. GitHub her kayıtta bunu
otomatik çalıştırır; elle bir şey yapmana gerek yok.
"""
import html
import json
import os
import re
import shutil
import sys
from collections import OrderedDict, defaultdict
from datetime import date

KOK = os.path.dirname(os.path.abspath(__file__))
CIKTI = os.path.join(KOK, "_site")
UYARILAR = []


# ------------------------------------------------------------------ okuma
def oku(ad):
    with open(os.path.join(KOK, ad), encoding="utf-8") as f:
        return f.read().splitlines()


def ayarlari_oku():
    a = {"SITE_ADI": "Bilinmeyen No", "SITE_ADRESI": "", "ITIRAZ_EPOSTA": ""}
    for s in oku("ayarlar.txt"):
        s = s.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        a[k.strip()] = v.strip()
    a["SITE_ADRESI"] = a["SITE_ADRESI"].rstrip("/")
    return a


TR = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")


def slug(metin):
    s = metin.translate(TR).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "diger"


def numara_normal(ham):
    d = re.sub(r"\D", "", ham)
    if d.startswith("0090"):
        d = d[4:]
    if d.startswith("90") and len(d) == 12:
        d = d[2:]
    if len(d) == 10 and d[0] in "2345789":
        d = "0" + d
    return d


def numara_goster(d):
    if len(d) == 11 and d.startswith("0"):
        return f"{d[0:4]} {d[4:7]} {d[7:9]} {d[9:11]}"
    return d


def yontemleri_oku():
    yontemler = OrderedDict()
    simdiki = None
    for s in oku("yontemler.txt"):
        if s.startswith("# ") or s.strip() == "#" or s.startswith("#="):
            continue
        if s.startswith("## "):
            baslik = s[3:].strip()
            simdiki = {"baslik": baslik, "slug": slug(baslik), "bloklar": []}
            yontemler[simdiki["slug"]] = simdiki
            continue
        if simdiki is None or not s.strip():
            continue
        if s.strip().startswith("- "):
            simdiki["bloklar"].append(("madde", s.strip()[2:]))
        else:
            simdiki["bloklar"].append(("p", s.strip()))
    return yontemler


def numaralari_oku():
    kayitlar = defaultdict(list)
    for no, s in enumerate(oku("numaralar.txt"), 1):
        t = s.strip()
        if not t or t.startswith("#"):
            continue
        parca = [p.strip() for p in t.split("|")]
        if len(parca) < 3:
            UYARILAR.append(f"numaralar.txt satır {no}: en az 'numara | yöntem | ne oldu' olmalı -> atlandı")
            continue
        d = numara_normal(parca[0])
        if len(d) < 7:
            UYARILAR.append(f"numaralar.txt satır {no}: numara anlaşılamadı ({parca[0]}) -> atlandı")
            continue
        tarih = parca[3] if len(parca) > 3 else ""
        if tarih and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tarih):
            UYARILAR.append(f"numaralar.txt satır {no}: tarih YYYY-AA-GG olmalı ({tarih}) -> tarih yok sayıldı")
            tarih = ""
        kayitlar[d].append({"yontem": parca[1] or "Diğer", "aciklama": parca[2], "tarih": tarih, "sira": no})
    return kayitlar


# ------------------------------------------------------------------ html
e = html.escape


def tarih_tr(t):
    if not t:
        return ""
    y, m, g = t.split("-")
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
             "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    return f"{int(g)} {aylar[int(m) - 1]} {y}"


def sayfa(A, baslik, aciklama, govde, yol, ekstra_head=""):
    tam_baslik = baslik if A["SITE_ADI"] in baslik else f"{baslik} | {A['SITE_ADI']}"
    canon = f'<link rel="canonical" href="{e(A["SITE_ADRESI"] + yol)}">' if A["SITE_ADRESI"] else ""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(tam_baslik)}</title>
<meta name="description" content="{e(aciklama)}">
{canon}
<meta property="og:title" content="{e(tam_baslik)}">
<meta property="og:description" content="{e(aciklama)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/stil.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📞</text></svg>">
{ekstra_head}
</head>
<body>
<header class="ust">
  <div class="kap">
    <a class="logo" href="/">📞 {e(A["SITE_ADI"])}</a>
    <nav><a href="/yontemler/">Yöntemler</a><a href="/hakkinda/">Hakkında &amp; İtiraz</a></nav>
  </div>
</header>
<main class="kap">
{govde}
</main>
<footer class="alt">
  <div class="kap">
    <p>Bu sitedeki kayıtlar, numaralar hakkında <strong>gelen şikayetlerin özetidir</strong>; numaranın sahibi hakkında kesin bir hüküm değildir. Dolandırıcılar başkasının numarasını taklit edebilir (numara sahteciliği).</p>
    <p>Kaydın hatalı olduğunu düşünüyorsan <a href="/hakkinda/#itiraz">itiraz et</a>, inceleyip kaldıralım.</p>
  </div>
</footer>
<script src="/arama.js" defer></script>
</body>
</html>
"""


ARAMA_FORMU = """
<form class="arama" data-arama>
  <input type="tel" inputmode="tel" name="n" placeholder="Numara yaz: 0850 123 45 67" autocomplete="off" aria-label="Telefon numarası" required>
  <button type="submit">Sorgula</button>
</form>
<div class="arama-sonuc" data-sonuc hidden></div>
"""


def yontem_linki(ad, yontemler):
    s = slug(ad)
    if s in yontemler:
        return f'<a class="etiket" href="/yontem/{s}/">{e(yontemler[s]["baslik"])}</a>'
    return f'<span class="etiket">{e(ad)}</span>'


def numara_kart(d, liste, yontemler):
    son = max((k["tarih"] for k in liste), default="")
    etiketler = " ".join(OrderedDict.fromkeys(yontem_linki(k["yontem"], yontemler) for k in liste))
    return f"""<li class="kart">
  <a class="kart-no" href="/numara/{d}/">{e(numara_goster(d))}</a>
  <div class="kart-alt">{etiketler} <span class="sayi">{len(liste)} şikayet</span>{f' <span class="tarih">· {e(tarih_tr(son))}</span>' if son else ''}</div>
</li>"""


def yaz(yol, icerik):
    tam = os.path.join(CIKTI, yol.lstrip("/"))
    if tam.endswith("/"):
        tam = os.path.join(tam, "index.html")
    os.makedirs(os.path.dirname(tam), exist_ok=True)
    with open(tam, "w", encoding="utf-8") as f:
        f.write(icerik)


# ------------------------------------------------------------------ sayfalar
def main():
    A = ayarlari_oku()
    yontemler = yontemleri_oku()
    kayitlar = numaralari_oku()

    for d, liste in kayitlar.items():
        for k in liste:
            if slug(k["yontem"]) not in yontemler:
                UYARILAR.append(f"{numara_goster(d)}: yöntem '{k['yontem']}' yontemler.txt'de yok (etiket olarak gösterilecek)")

    if os.path.exists(CIKTI):
        shutil.rmtree(CIKTI)
    os.makedirs(CIKTI)
    shutil.copy(os.path.join(KOK, "stil.css"), CIKTI)
    shutil.copy(os.path.join(KOK, "arama.js"), CIKTI)

    # son eklenenler: tarihe, sonra dosyadaki sıraya göre
    def son_anahtar(item):
        d, liste = item
        return (max(k["tarih"] for k in liste), max(k["sira"] for k in liste))

    sirali = sorted(kayitlar.items(), key=son_anahtar, reverse=True)

    # --- numara sayfaları
    for d, liste in kayitlar.items():
        g = numara_goster(d)
        yontem_adlari = list(OrderedDict.fromkeys(yontemler.get(slug(k["yontem"]), {"baslik": k["yontem"]})["baslik"] for k in liste))
        sikayetler = "\n".join(
            f"""<li class="sikayet">
  <div class="sikayet-ust">{yontem_linki(k["yontem"], yontemler)}{f'<span class="tarih">{e(tarih_tr(k["tarih"]))}</span>' if k["tarih"] else ''}</div>
  <p>{e(k["aciklama"])}</p>
</li>"""
            for k in sorted(liste, key=lambda k: (k["tarih"], k["sira"]), reverse=True))
        ilgili = ""
        for ad in yontem_adlari:
            s = slug(ad)
            if s in yontemler:
                y = yontemler[s]
                ilk = next((b[1] for b in y["bloklar"] if b[0] == "p"), "")
                ilgili += f'<div class="bilgi"><h3>Bu yöntem nasıl işliyor? — {e(y["baslik"])}</h3><p>{e(ilk)}</p><a href="/yontem/{s}/">Devamını oku →</a></div>'
        aciklama = f"{g} numarası hakkında {len(liste)} şikayet var: {', '.join(yontem_adlari)}. Bu numara sizi aradıysa dikkatli olun."
        govde = f"""
<p class="yol"><a href="/">Ana sayfa</a> › Numara</p>
<h1 class="numara-baslik">{e(g)}</h1>
<p class="durum durum-uyari">⚠️ Bu numara hakkında <strong>{len(liste)} şikayet</strong> var. Kesin hüküm değildir; numara taklit edilmiş olabilir.</p>
<h2>Şikayetler</h2>
<ul class="sikayetler">
{sikayetler}
</ul>
{ilgili}
<div class="bilgi bilgi-yesil">
  <h3>Bu numara seni aradıysa</h3>
  <ul>
    <li>Telefonda <strong>şifre, SMS kodu, kart bilgisi</strong> verme.</li>
    <li>Para gönderme, "güvenli hesap" diye bir şey yoktur.</li>
    <li>Kendini kurum olarak tanıtıyorsa telefonu kapat, kurumun resmi numarasını <strong>kendin</strong> ara.</li>
  </ul>
</div>
<h2>Başka bir numara sorgula</h2>
{ARAMA_FORMU}
"""
        yaz(f"/numara/{d}/", sayfa(A, f"{g} kimin numarası? Şikayetler", aciklama, govde, f"/numara/{d}/"))

    # --- yöntem sayfaları
    yontem_numaralari = defaultdict(list)
    for d, liste in kayitlar.items():
        for s in OrderedDict.fromkeys(slug(k["yontem"]) for k in liste):
            yontem_numaralari[s].append((d, liste))

    for s, y in yontemler.items():
        icerik, maddeler = [], []
        for tur, metin in y["bloklar"]:
            if tur == "madde":
                maddeler.append(f"<li>{e(metin)}</li>")
            else:
                if maddeler:
                    icerik.append("<ul class='maddeler'>" + "".join(maddeler) + "</ul>")
                    maddeler = []
                icerik.append(f"<p>{e(metin)}</p>")
        if maddeler:
            icerik.append("<ul class='maddeler'>" + "".join(maddeler) + "</ul>")
        nums = yontem_numaralari.get(s, [])
        nums_html = ("<h2>Bu yöntemle şikayet edilen numaralar</h2><ul class='kartlar'>" +
                     "".join(numara_kart(d, l, yontemler) for d, l in sorted(nums, key=son_anahtar, reverse=True)) +
                     "</ul>") if nums else ""
        ilk = next((b[1] for b in y["bloklar"] if b[0] == "p"), y["baslik"])
        govde = f"""
<p class="yol"><a href="/">Ana sayfa</a> › <a href="/yontemler/">Yöntemler</a> › {e(y["baslik"])}</p>
<h1>{e(y["baslik"])} dolandırıcılığı</h1>
<div class="metin">{''.join(icerik)}</div>
{nums_html}
"""
        yaz(f"/yontem/{s}/", sayfa(A, f"{y['baslik']} dolandırıcılığı nasıl yapılır, nasıl korunulur?", ilk[:155], govde, f"/yontem/{s}/"))

    yontem_kartlari = "".join(
        f'<li class="kart"><a class="kart-no kucuk" href="/yontem/{s}/">{e(y["baslik"])}</a>'
        f'<div class="kart-alt"><span class="sayi">{len(yontem_numaralari.get(s, []))} numara</span></div></li>'
        for s, y in yontemler.items())

    yaz("/yontemler/", sayfa(A, "Telefon dolandırıcılığı yöntemleri", "En sık karşılaşılan telefon ve SMS dolandırıcılığı yöntemleri ve korunma yolları.", f"""
<p class="yol"><a href="/">Ana sayfa</a> › Yöntemler</p>
<h1>Dolandırıcılık yöntemleri</h1>
<p>Telefon ve SMS ile en sık karşılaşılan yöntemler. Hangisinin nasıl işlediğini bilmek, tuzağa düşmemenin en kolay yolu.</p>
<ul class="kartlar">{yontem_kartlari}</ul>
""", "/yontemler/"))

    # --- ana sayfa
    son = "".join(numara_kart(d, l, yontemler) for d, l in sirali[:20])
    govde = f"""
<section class="kahraman">
  <h1>Seni arayan numara kimin?</h1>
  <p>Bilinmeyen bir numara mı aradı? Numarayı yaz, hakkında şikayet var mı hemen gör.</p>
  {ARAMA_FORMU}
  <p class="kucuk-not">Kayıtlar tek tek incelenerek eklenir; herkes kayıt ekleyemez.</p>
</section>
<h2>Son eklenen numaralar</h2>
{f'<ul class="kartlar">{son}</ul>' if son else '<p>Henüz kayıt yok.</p>'}
<h2>Dolandırıcılık yöntemleri</h2>
<ul class="kartlar">{yontem_kartlari}</ul>
"""
    yaz("/", sayfa(A, f"{A['SITE_ADI']} — Seni arayan numara kimin? Şikayet sorgula",
                   "Seni arayan bilinmeyen numarayı sorgula: dolandırıcılık şikayeti var mı, hangi yöntemle aradı, nasıl korunursun.", govde, "/"))

    # --- hakkında & itiraz
    ep = A["ITIRAZ_EPOSTA"]
    mailto = f"mailto:{ep}?subject={html.escape('İtiraz / Kaldırma Talebi')}"
    yaz("/hakkinda/", sayfa(A, "Hakkında ve itiraz", "Bu site nasıl çalışır, kayıtlar nasıl eklenir, hatalı bir kayıt nasıl kaldırılır.", f"""
<p class="yol"><a href="/">Ana sayfa</a> › Hakkında</p>
<h1>Hakkında</h1>
<div class="metin">
<p>{e(A["SITE_ADI"])}, telefon ve SMS dolandırıcılığına karşı insanları uyarmak için hazırlanmış bir bilgilendirme sitesidir.</p>
<ul class="maddeler">
<li>Kayıtları <strong>sadece site yöneticisi</strong> ekler; kullanıcılar kayıt ekleyemez.</li>
<li>Kayıtlarda <strong>isim ve kişisel bilgi yer almaz</strong>; sadece numara ve ne yaşandığı yazılır.</li>
<li>Kayıtlar <strong>şikayet özetidir, kesin hüküm değildir.</strong> Dolandırıcılar başkalarının numaralarını taklit edebilir.</li>
</ul>
</div>
<h2 id="itiraz">İtiraz / kaldırma talebi</h2>
<div class="metin">
<p>Numaranın sahibiysen ve kaydın hatalı olduğunu düşünüyorsan bize yaz. E-postanda şunları belirt:</p>
<ul class="maddeler">
<li>İtiraz ettiğin numara</li>
<li>Kısa açıklama (örn. "Bu numara bana ait, numaram taklit edilmiş")</li>
</ul>
<p>Talepler incelenir ve uygun bulunan kayıtlar kaldırılır.</p>
<p><a class="dugme" href="{e(mailto)}">✉️ İtiraz e-postası gönder</a></p>
<p class="kucuk-not">E-posta: {e(ep)}</p>
</div>
""", "/hakkinda/"))

    # --- 404
    yaz("/404.html", sayfa(A, "Sayfa bulunamadı", "Aradığın sayfa bulunamadı.", f"""
<h1>Sayfa bulunamadı</h1>
<p>Aradığın sayfa yok ya da kaldırılmış. Numara sorgulamak için:</p>
{ARAMA_FORMU}
""", "/404.html"))

    # --- arama verisi, sitemap, robots
    with open(os.path.join(CIKTI, "arama.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(kayitlar.keys()), f)

    bugun = date.today().isoformat()
    urls = ["/", "/yontemler/", "/hakkinda/"] + [f"/yontem/{s}/" for s in yontemler] + [f"/numara/{d}/" for d in kayitlar]
    with open(os.path.join(CIKTI, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            f.write(f"  <url><loc>{e(A['SITE_ADRESI'] + u)}</loc><lastmod>{bugun}</lastmod></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(CIKTI, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {A['SITE_ADRESI']}/sitemap.xml\n")

    print(f"Tamam: {len(kayitlar)} numara, {len(yontemler)} yöntem, {len(urls)} sayfa üretildi.")
    for u in UYARILAR:
        print("UYARI:", u)
    # Hatalı satırlar siteyi durdurmasın, sadece uyarı versin.
    return 0


if __name__ == "__main__":
    sys.exit(main())

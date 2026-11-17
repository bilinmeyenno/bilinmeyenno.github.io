(function () {
  function normal(ham) {
    var d = (ham || "").replace(/\D/g, "");
    if (d.indexOf("0090") === 0) d = d.slice(4);
    if (d.indexOf("90") === 0 && d.length === 12) d = d.slice(2);
    if (d.length === 10 && "2345789".indexOf(d[0]) !== -1) d = "0" + d;
    return d;
  }
  function goster(d) {
    if (d.length === 11 && d[0] === "0")
      return d.slice(0, 4) + " " + d.slice(4, 7) + " " + d.slice(7, 9) + " " + d.slice(9);
    if (d.length === 7 && d.indexOf("444") === 0)
      return d.slice(0, 3) + " " + d[3] + " " + d.slice(4);
    return d;
  }
  var liste = null;
  function yukle() {
    if (liste) return Promise.resolve(liste);
    return fetch("/arama.json").then(function (r) { return r.json(); })
      .then(function (j) { liste = j; return j; });
  }
  document.querySelectorAll("form[data-arama]").forEach(function (form) {
    var sonuc = form.parentNode.querySelector("[data-sonuc]");
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var d = normal(form.n.value);
      if (d.length < 7) {
        sonuc.hidden = false;
        sonuc.className = "arama-sonuc durum";
        sonuc.textContent = "Lütfen geçerli bir telefon numarası yaz.";
        return;
      }
      yukle().then(function (l) {
        if (l.indexOf(d) !== -1) {
          location.href = "/numara/" + d + "/";
        } else {
          sonuc.hidden = false;
          sonuc.className = "arama-sonuc durum durum-iyi";
          sonuc.innerHTML = "✅ <strong>" + goster(d) + "</strong> hakkında kayıtlı şikayet yok.<br>" +
            "<small>Bu, numaranın kesin güvenli olduğu anlamına gelmez. Telefonda asla şifre, SMS kodu veya kart bilgisi verme.</small>";
        }
      }).catch(function () {
        sonuc.hidden = false;
        sonuc.className = "arama-sonuc durum";
        sonuc.textContent = "Bir hata oldu, sayfayı yenileyip tekrar dene.";
      });
    });
  });
})();

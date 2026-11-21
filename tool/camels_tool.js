/* camels-score: scoring of one new bank in the browser. Mirrors camels_score/newbank.py;
   tests/test_newbank.py runs both on the same inputs. */
var CamelsTool = (function () {
  var RATING = {"AAA":1,"AA+":1,"AA":1,"AA-":1,"A+":2,"A":2,"A-":3,"BBB+":4,"BBB":4,"BBB-":5,
    "BB+":6,"BB":6,"BB-":7,"B+":8,"B":8,"B-":9,"CCC+":10,"CCC":10,"CCC-":10,"CC":10,"C":10,"RD":10,"D":10};
  var PROB = {core:0.5, strategic:0.35, moderate:0.15, none:0};
  var ABILITY = [[0.20,0.50],[0.10,0.75]];
  var DESC = {1:"Very strong",2:"Very strong",3:"Strong",4:"Strong",5:"Adequate",6:"Adequate",
    7:"Moderate",8:"Moderate",9:"Weak",10:"Very weak"};
  function clip(x, lo, hi) { return Math.min(Math.max(x, lo), hi); }
  function rhe(x) { var f = Math.floor(x), d = x - f;            // round half to even, as numpy
    if (Math.abs(d - 0.5) < 1e-12) return (f % 2 === 0) ? f : f + 1; return Math.round(x); }
  function std(a) { var m = a.reduce(function (s, v) { return s + v; }, 0) / a.length;
    return Math.sqrt(a.reduce(function (s, v) { return s + (v - m) * (v - m); }, 0) / (a.length - 1)); }
  function interp(x, xs, ys) {
    if (x <= xs[0]) return ys[0]; if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
    for (var i = 1; i < xs.length; i++) if (x <= xs[i])
      return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
  }
  function label(score) { var g = clip(rhe(score), 1, 10), f = score - g;
    return {grade: g, label: g + (f <= -1 / 6 ? "+" : f >= 1 / 6 ? "-" : "")}; }

  function score(years, calib, o) {
    o = o || {};
    var P = calib.params, cfg = calib.config, nb = P.new_bank, R = P.ratios;
    var yrs = Object.keys(years).map(Number).sort(function (a, b) { return a - b; });
    var raw = {}, cl = {};
    yrs.forEach(function (y) {
      var row = {};
      R.forEach(function (r) {
        var v = years[y][r]; v = (v === "" || v === null || v === undefined) ? null : Number(v);
        if (v !== null && isNaN(v)) v = null;
        if (v !== null) { var b = nb[r].bounds;
          if ((b[0] !== null && v < b[0]) || (b[1] !== null && v > b[1])) v = null; }
        row[r] = v;
      });
      raw[y] = row;
    });
    yrs.forEach(function (y, i) {
      var i0 = Math.max(0, i - 2), last3 = yrs.slice(i0, i + 1).map(function (yy) { return raw[yy].ROAA; });
      var ok = last3.length === 3 && last3.every(function (v) { return v !== null; }) && yrs[i] - yrs[i0] === 2;
      if (R.indexOf("ROAA VOLATILITY 3Y") >= 0) raw[y]["ROAA VOLATILITY 3Y"] = ok ? std(last3) : null;
      cl[y] = {};
      R.forEach(function (r) { var v = raw[y][r];
        cl[y][r] = v === null ? null : clip(v, nb[r].p01, nb[r].p99); });
    });
    var out = yrs.map(function (y) {
      var steps = [], used = {}, imputed = [], z = {};
      R.forEach(function (r) {
        var v = cl[y][r];
        if (nb[r].through_cycle && v !== null) {
          var w = yrs.filter(function (yy) { return yy >= y - 2 && yy <= y && cl[yy][r] !== null; })
                     .map(function (yy) { return cl[yy][r]; });
          if (w.length >= 2) { var avg = w.reduce(function (s, x) { return s + x; }, 0) / w.length;
            v = nb[r].direction === 1 ? Math.min(v, avg) : Math.max(v, avg); }
        }
        if (v === null) { v = nb[r].weak_fill; imputed.push(r); }
        used[r] = v;
        var zz = nb[r].direction * (v - P.centre[r]) / P.scale[r];
        if (nb[r].pillar === "C" && P.capital_z_cap !== null && P.capital_z_cap !== undefined) zz = Math.min(zz, P.capital_z_cap);
        z[r] = clip(zz, -3, 3);
      });
      var pl = {}, order = [];
      R.forEach(function (r) { var p = nb[r].pillar; if (!pl[p]) { pl[p] = []; order.push(p); } pl[p].push(z[r]); });
      var pillars = {}, tw = 0, comp = 0;
      order.forEach(function (p) { pillars[p] = pl[p].reduce(function (s, x) { return s + x; }, 0) / pl[p].length;
        tw += (P.weights[p] || 0); });
      order.forEach(function (p) { comp += pillars[p] * (P.weights[p] || 0) / tw; });
      var c = P.composite_cuts, n = cfg.n_grades, qs = [];
      for (var k = 1; k < n; k++) qs.push(k / n);
      var xs = [c[0] - (c[1] - c[0])].concat(c, [c[c.length - 1] + (c[c.length - 1] - c[c.length - 2])]);
      var pct = interp(comp, xs, [0].concat(qs, [1]));
      var standalone = clip(10.5 - 10 * pct, 1, 10), sc = standalone;
      steps.push(["Standalone, from the ratios", standalone]);
      var oe = null;
      if (o.countryScore !== null && o.countryScore !== undefined && o.countryScore !== "") {
        oe = clip(Number(o.countryScore), 1, 10);
        sc = Math.max(cfg.oe_weight * oe + (1 - cfg.oe_weight) * standalone, Math.max(oe - cfg.max_uplift, 1));
        steps.push(["Country score " + oe + ": 15% blend, cap of " + cfg.max_uplift + " notches", sc]);
      }
      var notch = 0;
      if (cfg.loss_notch) { notch = used.ROAA < -1 ? 2 : used.ROAA < 0 ? 1 : 0;
        sc += notch; if (notch) steps.push(["Loss notch +" + notch, sc]); }
      var own = clip(sc, 1, 10), fin = own, pUsed = 0;
      var parent = o.parentRating ? RATING[o.parentRating] :
        (o.parentScore !== null && o.parentScore !== undefined && o.parentScore !== "" ? Number(o.parentScore) : null);
      var sov = o.sovereignRating ? RATING[o.sovereignRating] : null;
      var lvl = o.supportLevel || "none";
      if (parent !== null && parent !== undefined && lvl !== "none") {
        var p = Math.min(PROB[lvl] || 0, 0.5), ab = 1;
        if (o.assetsShare !== null && o.assetsShare !== undefined && o.assetsShare !== "")
          for (var a = 0; a < ABILITY.length; a++) if (Number(o.assetsShare) > ABILITY[a][0]) { ab = ABILITY[a][1]; break; }
        p = o.parentStress ? 0 : p * ab;
        var gap = Math.max(own - parent, 0), sup = own - p * gap;
        if (oe !== null) sup = Math.max(sup, Math.max(oe - 2, 1));
        if (sov) sup = Math.max(sup, sov);
        fin = clip(Math.min(sup, own), 1, 10); pUsed = gap > 0 ? p : 0;
        steps.push(["Group support, probability " + pUsed.toFixed(2), fin]);
      }
      if (o.overlay) { fin = clip(fin + clip(Number(o.overlay), -2, 2), 1, 10);
        steps.push(["Analyst overlay " + (o.overlay > 0 ? "+" : "") + o.overlay, fin]); }
      var L = label(fin), ratios = {};
      R.forEach(function (r) { ratios[r] = {entered: raw[y][r], used: used[r], z: z[r], imputed: imputed.indexOf(r) >= 0}; });
      return {year: y, final_score: fin, grade: L.grade, label: L.label, descriptor: DESC[L.grade],
        standalone_score: standalone, own_score: own, loss_notch: notch, support_prob: pUsed,
        composite_z: comp, pillars: pillars, ratios: ratios, reported_ratios: R.length - imputed.length,
        data_quality: imputed.length / R.length > 0.4 ? "LOW" : "OK", enough_data: R.length - imputed.length >= 5,
        steps: steps};
    });
    return {bank_years: out, latest: out[out.length - 1]};
  }
  return {score: score, RATING: RATING, DESC: DESC};
})();
if (typeof module !== "undefined") module.exports = CamelsTool;

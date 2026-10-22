/* BIS click events. No network transmission or cookies without an installed counter. */
(function () {
  "use strict";
  var projectPaths = new Set(["zelenodolsk.html","himfest.html","kastamonu.html","spartakiada.html","festival-dobryh-del.html","phuket-wedding.html","plehanov-reu.html"]);
  document.addEventListener("click", function (event) {
    var link = event.target && event.target.closest && event.target.closest("a[href]");
    if (!link) return;
    var href = (link.getAttribute("href") || "").trim();
    var kind = "";
    if (/^tel:/i.test(href)) kind = "contact_phone";
    else if (/^mailto:/i.test(href)) kind = "contact_email";
    else if (/^https:\/\/t\.me\//i.test(href)) kind = "contact_telegram";
    else if (/^#contacts$/i.test(href)) kind = "contact_cta";
    else if (projectPaths.has(href.split(/[?#]/)[0].replace(/^\.\//, ""))) kind = "portfolio_open";
    else if (/^(?:\.\/)?assets\/letters\//i.test(href)) kind = "document_open";
    if (!kind) return;
    var eventName = "bis_" + kind;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({event: eventName, page_path: location.pathname});
    // Set BIS_METRIKA_ID only after a real counter has been created.
    var id = Number(window.BIS_METRIKA_ID);
    if (id > 0 && typeof window.ym === "function") {
      window.ym(id, "reachGoal", eventName);
    }
  }, true);
})();

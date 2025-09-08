// Configure NProgress
NProgress.configure({
  showSpinner: false, // disable the loader circle
  trickleSpeed: 150, // adjust speed (default 200ms)
});

/**
 * Track active requests globally
 */
let activeRequests = 0;

function startProgress() {
  if (activeRequests === 0) {
    NProgress.start();
  }
  activeRequests++;
}

function stopProgress() {
  activeRequests--;
  if (activeRequests <= 0) {
    activeRequests = 0;
    NProgress.done();
  }
}

/* ----------------------------
   Intercept fetch()
---------------------------- */
const origFetch = window.fetch;
window.fetch = function (...args) {
  startProgress();
  return origFetch
    .apply(this, args)
    .then((res) => {
      stopProgress();
      return res;
    })
    .catch((err) => {
      stopProgress();
      throw err;
    });
};

/* ----------------------------
   Intercept XMLHttpRequest
   (covers htmx + jQuery.ajax + raw XHR)
---------------------------- */
(function (open, send) {
  XMLHttpRequest.prototype.open = function (...args) {
    this.addEventListener("loadstart", startProgress);
    this.addEventListener("loadend", stopProgress);
    open.apply(this, args);
  };
})(XMLHttpRequest.prototype.open, XMLHttpRequest.prototype.send);

/* ----------------------------
   Hook into htmx (optional,
   but covered since htmx uses XHR)
---------------------------- */
if (window.htmx) {
  document.body.addEventListener("htmx:beforeRequest", startProgress);
  document.body.addEventListener("htmx:afterRequest", stopProgress);

  // When navigating back/forward, htmx restores from cache without XHR
  document.body.addEventListener("htmx:historyRestore", function () {
    // Ensure bar shows briefly then finishes
    NProgress.start();
    NProgress.done();

    // Reset counters so fetch/XHR interceptors don’t get confused
    activeRequests = 0;
  });
}

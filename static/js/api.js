/**
 * Shared AJAX utility. Reads CSRF from cookie (Django default) or
 * from a [name=csrfmiddlewaretoken] input on the page.
 */
(function (global) {
  'use strict';

  function getCsrf() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  }

  /**
   * POST data as FormData to url.
   * @param {string} url
   * @param {Object} data  key/value pairs to append
   * @returns {Promise<Response>}
   */
  function postForm(url, data) {
    var fd = new FormData();
    fd.append('csrfmiddlewaretoken', getCsrf());
    Object.entries(data || {}).forEach(function (kv) { fd.append(kv[0], kv[1]); });
    return fetch(url, { method: 'POST', body: fd });
  }

  /**
   * postForm + parse JSON response.
   * @returns {Promise<Object>}
   */
  function postJSON(url, data) {
    return postForm(url, data).then(function (r) { return r.json(); });
  }

  global.FitAPI = { postForm: postForm, postJSON: postJSON };
})(window);

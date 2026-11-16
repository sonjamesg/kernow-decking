  /* boot.js: Adds the .js hook and fills .year. */
/* Kernow Decking Co. — site behaviour (no dependencies) */
(function () {
  'use strict';
  document.documentElement.classList.add('js');
  var nav = document.getElementById('main-nav');
  var toggle = document.querySelector('.nav-toggle');
  var mobileBar = document.querySelector('.mobile-bar');

  document.querySelectorAll('.year').forEach(function (y) { y.textContent = new Date().getFullYear(); });


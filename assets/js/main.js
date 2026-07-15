/* 스피드 배관공사 — main.js */
(function () {
  var hamb = document.querySelector(".hamb");
  var menu = document.querySelector(".menu");
  if (hamb && menu) {
    hamb.addEventListener("click", function () {
      menu.classList.toggle("open");
      var open = menu.classList.contains("open");
      hamb.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    });
  }
  // 모바일: 드롭다운 부모 클릭 시 펼치기
  document.querySelectorAll(".menu > li.has-drop > a").forEach(function (a) {
    a.addEventListener("click", function (e) {
      if (window.innerWidth <= 720) {
        e.preventDefault();
        a.parentElement.classList.toggle("mobile-open");
      }
    });
  });
  // 현재 연도
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();

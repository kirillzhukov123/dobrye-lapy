(function () {
    var burger = document.querySelector('.burger');
    var nav = document.getElementById('main-nav');

    if (!burger || !nav) {
        return;
    }

    burger.addEventListener('click', function () {
        var open = nav.classList.toggle('nav-open');
        burger.classList.toggle('burger-open', open);
        burger.setAttribute('aria-expanded', open ? 'true' : 'false');
        burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    });

    nav.addEventListener('click', function (event) {
        if (event.target.tagName === 'A' && nav.classList.contains('nav-open')) {
            nav.classList.remove('nav-open');
            burger.classList.remove('burger-open');
            burger.setAttribute('aria-expanded', 'false');
        }
    });
}());

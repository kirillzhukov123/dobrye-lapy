/*
 * Демонстрационный вход для статической версии на GitHub Pages.
 * Django на Pages не работает, поэтому форма входа обрабатывается в браузере.
 * На локальном сервере файл не подключается.
 */
(function () {
    'use strict';

    if (!window.DEMO_STATIC) {
        return;
    }

    var PREFIX = window.DEMO_PREFIX || '';
    var KEY = 'dobrye-lapy-demo-user';
    var ACCOUNTS = {
        applicant: { password: 'demo12345', page: '/profile/' },
        curator: { password: 'demo12345', page: '/applications/' },
        admin: { password: 'demo12345', page: '/applications/' },
        vet: { password: 'demo12345', page: '/profile/' },
        volunteer: { password: 'demo12345', page: '/profile/' }
    };

    function currentUser() {
        try {
            return localStorage.getItem(KEY);
        } catch (error) {
            return null;
        }
    }

    function notice(form, text) {
        var node = form.querySelector('.demo-note');
        if (!node) {
            node = document.createElement('p');
            node.className = 'warning-text demo-note';
            form.appendChild(node);
        }
        node.textContent = text;
    }

    function login(form) {
        var loginField = form.querySelector('#id_username');
        var passwordField = form.querySelector('#id_password');
        var name = loginField ? loginField.value.trim().toLowerCase() : '';
        var password = passwordField ? passwordField.value : '';
        var account = ACCOUNTS[name];

        if (!account || account.password !== password) {
            notice(form, 'Неверный логин или пароль. Демо-доступ: applicant / demo12345, curator / demo12345, admin / demo12345.');
            return;
        }

        try {
            localStorage.setItem(KEY, name);
        } catch (error) {
            /* приватный режим браузера */
        }
        window.location.href = PREFIX + account.page;
    }

    function logout() {
        try {
            localStorage.removeItem(KEY);
        } catch (error) {
            /* приватный режим браузера */
        }
        window.location.href = PREFIX + '/';
    }

    function paintHeader() {
        var user = currentUser();
        if (!user) {
            return;
        }

        var nav = document.getElementById('main-nav');
        if (!nav) {
            return;
        }

        var links = nav.querySelectorAll('a.nav-link');
        for (var i = 0; i < links.length; i += 1) {
            var href = links[i].getAttribute('href') || '';
            if (href.indexOf('/login') !== -1 || href.indexOf('/register') !== -1) {
                links[i].style.display = 'none';
            }
        }

        if (nav.querySelector('.user-name')) {
            nav.querySelector('.user-name').textContent = user;
            return;
        }

        var name = document.createElement('span');
        name.className = 'user-name';
        name.textContent = user;
        nav.appendChild(name);

        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'logout-btn';
        button.textContent = 'Выйти';
        button.addEventListener('click', logout);
        nav.appendChild(button);
    }

    function addLoginHint() {
        if (!document.querySelector('#id_username') || !document.querySelector('#id_password')) {
            return;
        }
        var form = document.querySelector('#id_username').closest('form');
        if (!form || form.querySelector('.demo-hint')) {
            return;
        }
        var hint = document.createElement('p');
        hint.className = 'field-help demo-hint';
        hint.innerHTML = 'Демо-доступ: <b>applicant</b> / demo12345, <b>curator</b> / demo12345, <b>admin</b> / demo12345.';
        var button = form.querySelector('button[type="submit"]');
        form.insertBefore(hint, button || null);
    }

    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form || form.tagName !== 'FORM') {
            return;
        }

        if (form.querySelector('#id_username') && form.querySelector('#id_password')) {
            event.preventDefault();
            login(form);
            return;
        }

        var action = form.getAttribute('action') || '';
        if (action.indexOf('/logout') !== -1) {
            event.preventDefault();
            logout();
            return;
        }

        if ((form.getAttribute('method') || '').toLowerCase() === 'post') {
            event.preventDefault();
            notice(form, 'Это статическая демонстрация на GitHub Pages. Сохранение данных работает в локальной версии на Django.');
        }
    }, true);

    document.addEventListener('DOMContentLoaded', function () {
        paintHeader();
        addLoginHint();
    });
}());

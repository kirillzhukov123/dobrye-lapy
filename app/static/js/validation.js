(function () {
    'use strict';

    var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[a-zA-Zа-яА-Я]{2,}$/;
    var PHONE_RE = /^\+?[\d\s\-()]{10,20}$/;
    var PERIOD_RE = /^\d{4}-(0[1-9]|1[0-2])$/;

    function digitsOnly(value) {
        return value.replace(/\D/g, '');
    }

    function errorNode(field) {
        var next = field.nextElementSibling;
        while (next && !next.classList.contains('client-error')) {
            if (next.classList.contains('form-error') || next.tagName === 'BUTTON') {
                break;
            }
            next = next.nextElementSibling;
        }
        if (next && next.classList.contains('client-error')) {
            return next;
        }
        var node = document.createElement('p');
        node.className = 'form-error client-error';
        field.parentNode.insertBefore(node, field.nextSibling);
        return node;
    }

    function clearError(field) {
        field.removeAttribute('aria-invalid');
        var group = field.closest('.form-group') || field.parentNode;
        var nodes = group.querySelectorAll('.client-error');
        for (var i = 0; i < nodes.length; i += 1) {
            nodes[i].remove();
        }
    }

    function showError(field, message) {
        clearError(field);
        var node = errorNode(field);
        node.textContent = message;
        field.setAttribute('aria-invalid', 'true');
    }

    function labelOf(field) {
        var label = document.querySelector('label[for="' + field.id + '"]');
        return label ? label.textContent.replace(/\*/g, '').trim() : 'Поле';
    }

    function validateField(field) {
        var value = (field.value || '').trim();
        var rule = field.getAttribute('data-check');
        var required = field.hasAttribute('required') || rule === 'required';

        if (!value) {
            if (required) {
                showError(field, labelOf(field) + ': поле обязательно для заполнения.');
                return false;
            }
            clearError(field);
            return true;
        }

        if (rule === 'email' && !EMAIL_RE.test(value)) {
            showError(field, 'Укажите почту в формате name@example.ru.');
            return false;
        }

        if (rule === 'phone') {
            var digits = digitsOnly(value);
            if (!PHONE_RE.test(value) || digits.length < 10 || digits.length > 15) {
                showError(field, 'Телефон должен содержать 10-15 цифр, например +7 (900) 000-00-00.');
                return false;
            }
        }

        if (rule === 'text') {
            var min = parseInt(field.getAttribute('data-min'), 10) || 0;
            var max = parseInt(field.getAttribute('data-max'), 10) || 0;
            if (min && value.length < min) {
                showError(field, 'Минимум ' + min + ' символов, сейчас ' + value.length + '.');
                return false;
            }
            if (max && value.length > max) {
                showError(field, 'Максимум ' + max + ' символов, сейчас ' + value.length + '.');
                return false;
            }
        }

        if (rule === 'number') {
            var number = Number(value.replace(',', '.'));
            var minValue = parseFloat(field.getAttribute('data-min'));
            var maxValue = parseFloat(field.getAttribute('data-max'));
            if (isNaN(number)) {
                showError(field, 'Введите число.');
                return false;
            }
            if (!isNaN(minValue) && number < minValue) {
                showError(field, 'Минимальное значение: ' + minValue + '.');
                return false;
            }
            if (!isNaN(maxValue) && number > maxValue) {
                showError(field, 'Максимальное значение: ' + maxValue + '.');
                return false;
            }
        }

        if (rule === 'future') {
            var when = new Date(value);
            if (isNaN(when.getTime()) || when.getTime() <= Date.now()) {
                showError(field, 'Выберите будущую дату и время.');
                return false;
            }
        }

        if (rule === 'period' && !PERIOD_RE.test(value)) {
            showError(field, 'Укажите период в формате ГГГГ-ММ, например 2026-11.');
            return false;
        }

        if (rule === 'password') {
            if (value.length < 8) {
                showError(field, 'Пароль должен содержать не менее 8 символов.');
                return false;
            }
            if (/^\d+$/.test(value)) {
                showError(field, 'Пароль не может состоять только из цифр.');
                return false;
            }
        }

        if (rule === 'password2') {
            var target = document.getElementById(field.getAttribute('data-match'));
            if (target && target.value !== field.value) {
                showError(field, 'Пароли не совпадают.');
                return false;
            }
        }

        var maxLength = parseInt(field.getAttribute('data-max'), 10);
        if (maxLength && value.length > maxLength && rule !== 'text') {
            showError(field, 'Не больше ' + maxLength + ' символов.');
            return false;
        }

        clearError(field);
        return true;
    }

    function validateForm(form) {
        var fields = form.querySelectorAll('[data-check], [required]');
        var firstInvalid = null;

        for (var i = 0; i < fields.length; i += 1) {
            if (fields[i].type === 'hidden' || fields[i].disabled) {
                continue;
            }
            if (!validateField(fields[i]) && !firstInvalid) {
                firstInvalid = fields[i];
            }
        }

        if (firstInvalid) {
            firstInvalid.focus();
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
        }
        return true;
    }

    var forms = document.querySelectorAll('form[data-validate]');
    for (var i = 0; i < forms.length; i += 1) {
        (function (form) {
            form.setAttribute('novalidate', 'novalidate');

            form.addEventListener('submit', function (event) {
                if (!validateForm(form)) {
                    event.preventDefault();
                    event.stopPropagation();
                }
            });

            form.addEventListener('blur', function (event) {
                var field = event.target;
                if (field.matches && field.matches('[data-check], [required]')) {
                    validateField(field);
                }
            }, true);

            form.addEventListener('input', function (event) {
                var field = event.target;
                if (field.getAttribute && field.getAttribute('aria-invalid') === 'true') {
                    validateField(field);
                }
                updateCounter(field);
            });
        }(forms[i]));
    }

    function updateCounter(field) {
        if (!field.id) {
            return;
        }
        var counter = document.querySelector('[data-counter-for="' + field.id + '"]');
        if (!counter) {
            return;
        }
        var max = parseInt(field.getAttribute('data-max'), 10) || 1000;
        var min = parseInt(field.getAttribute('data-min'), 10) || 0;
        counter.textContent = 'Символов: ' + field.value.length + ' из ' + max + (min ? ', минимум ' + min : '');
    }

    var counters = document.querySelectorAll('[data-counter-for]');
    for (var j = 0; j < counters.length; j += 1) {
        var field = document.getElementById(counters[j].getAttribute('data-counter-for'));
        if (field) {
            updateCounter(field);
        }
    }
}());

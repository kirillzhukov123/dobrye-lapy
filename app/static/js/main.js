(function () {
    'use strict';

    /* Меню на мобильных */
    var burger = document.querySelector('.burger');
    var nav = document.getElementById('main-nav');

    if (burger && nav) {
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
    }

    /* Избранное в localStorage */
    var FAV_KEY = 'dobrye-lapy-favorites';

    function readFavorites() {
        try {
            var raw = JSON.parse(localStorage.getItem(FAV_KEY));
            return Array.isArray(raw) ? raw.map(String) : [];
        } catch (error) {
            return [];
        }
    }

    function writeFavorites(list) {
        try {
            localStorage.setItem(FAV_KEY, JSON.stringify(list));
        } catch (error) {
            /* приватный режим браузера */
        }
    }

    function isFavorite(id) {
        return readFavorites().indexOf(String(id)) !== -1;
    }

    function updateFavoriteCount() {
        var list = readFavorites();
        var nodes = document.querySelectorAll('[data-fav-count]');
        for (var i = 0; i < nodes.length; i += 1) {
            nodes[i].textContent = list.length;
        }
    }

    function paintFavorite(button) {
        var active = isFavorite(button.getAttribute('data-fav'));
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
        button.classList.toggle('is-active', active);
        var icon = button.querySelector('[aria-hidden="true"]');
        if (icon) {
            icon.innerHTML = active ? '&#9829;' : '&#9825;';
        }
        var name = button.getAttribute('data-name') || 'питомца';
        button.setAttribute('aria-label', (active ? 'Убрать ' : 'Добавить ') + name + (active ? ' из избранного' : ' в избранное'));
    }

    function paintAllFavorites(root) {
        var buttons = (root || document).querySelectorAll('[data-fav]');
        for (var i = 0; i < buttons.length; i += 1) {
            paintFavorite(buttons[i]);
        }
        updateFavoriteCount();
    }

    document.addEventListener('click', function (event) {
        var button = event.target.closest('[data-fav]');
        if (!button) {
            return;
        }
        event.preventDefault();
        var id = String(button.getAttribute('data-fav'));
        var list = readFavorites();
        var index = list.indexOf(id);
        if (index === -1) {
            list.push(id);
        } else {
            list.splice(index, 1);
        }
        writeFavorites(list);
        paintAllFavorites();

        var favOnly = document.querySelector('[data-fav-only]');
        if (favOnly && favOnly.checked && window.PetsCatalog) {
            window.PetsCatalog.reload();
        }
    });

    /* Каталог: живой фильтр, пагинация и загрузка JSON */
    var form = document.querySelector('[data-filter-form]');
    var results = document.querySelector('[data-results]');

    if (!form || !results) {
        paintAllFavorites();
        return;
    }

    var api = form.getAttribute('data-api');
    var grid = results.querySelector('[data-pets-grid]');
    var loading = results.querySelector('[data-loading]');
    var errorBox = results.querySelector('[data-results-error]');
    var status = document.querySelector('[data-filter-status]');
    var pagination = document.querySelector('[data-pagination]');
    var debounceTimer = null;
    var requestNumber = 0;
    var staticCache = null;

    function escapeHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function currentParams(page) {
        var data = new FormData(form);
        var params = new URLSearchParams();
        data.forEach(function (value, key) {
            if (key === 'fav' || value === '') {
                return;
            }
            params.set(key, value);
        });
        if (page && page > 1) {
            params.set('page', page);
        }
        return params;
    }

    function setText(selector, value) {
        var nodes = document.querySelectorAll(selector);
        for (var i = 0; i < nodes.length; i += 1) {
            nodes[i].textContent = value;
        }
    }

    function showLoading() {
        if (loading) {
            loading.hidden = false;
        }
        results.classList.add('is-loading');
        if (errorBox) {
            errorBox.hidden = true;
        }
    }

    function hideLoading() {
        if (loading) {
            loading.hidden = true;
        }
        results.classList.remove('is-loading');
    }

    function cardTemplate(pet) {
        var photo = pet.photo ? escapeHtml(pet.photo) : '';
        return '' +
            '<article class="pet-card" data-pet-id="' + escapeHtml(pet.id) + '">' +
                '<a class="pet-card-link" href="' + escapeHtml(pet.url) + '">' +
                    '<img src="' + photo + '" alt="' + escapeHtml(pet.name) + '" class="card-image" width="600" height="400" loading="lazy" decoding="async">' +
                    '<h2 class="card-title">' + escapeHtml(pet.name) + '</h2>' +
                '</a>' +
                '<p class="card-desc">' + escapeHtml(pet.species_label) + ', ' + escapeHtml(pet.breed) + ', ' + escapeHtml(pet.age) + '</p>' +
                '<p class="card-meta">' + escapeHtml(pet.enclosure) + '</p>' +
                '<div class="card-footer">' +
                    '<span class="status-badge ' + escapeHtml(pet.status) + '">' + escapeHtml(pet.status_label) + '</span>' +
                    '<button type="button" class="fav-btn" data-fav="' + escapeHtml(pet.id) + '" data-name="' + escapeHtml(pet.name) + '" aria-pressed="false" aria-label="Добавить в избранное">' +
                        '<span aria-hidden="true">&#9825;</span>' +
                    '</button>' +
                '</div>' +
            '</article>';
    }

    function render(pets, total, page, pages) {
        var html = '';
        for (var i = 0; i < pets.length; i += 1) {
            html += cardTemplate(pets[i]);
        }
        if (!pets.length) {
            html = '<p class="empty-msg">Ничего не найдено. Попробуйте изменить условия поиска.</p>';
        }
        grid.innerHTML = html;

        setText('[data-results-count]', total);
        setText('[data-current-page]', page);
        setText('[data-total-pages]', pages);

        if (status) {
            status.textContent = 'Найдено питомцев: ' + total;
        }

        renderPagination(page, pages);
        paintAllFavorites(grid);
    }

    function renderPagination(page, pages) {
        if (!pagination) {
            pagination = document.createElement('nav');
            pagination.className = 'pagination';
            pagination.setAttribute('aria-label', 'Страницы');
            pagination.setAttribute('data-pagination', '');
            results.parentNode.insertBefore(pagination, results.nextSibling);
        }

        if (pages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        var html = '';
        if (page > 1) {
            html += '<button type="button" class="page-link" data-page="' + (page - 1) + '">Назад</button>';
        }
        for (var num = 1; num <= pages; num += 1) {
            if (num === page) {
                html += '<span class="page-link page-current" aria-current="page">' + num + '</span>';
            } else {
                html += '<button type="button" class="page-link" data-page="' + num + '">' + num + '</button>';
            }
        }
        if (page < pages) {
            html += '<button type="button" class="page-link" data-page="' + (page + 1) + '">Вперёд</button>';
        }
        pagination.innerHTML = html;
    }

    function filterStatic(data, params) {
        var q = (params.get('q') || '').toLowerCase();
        var species = params.get('species') || '';
        var petStatus = params.get('status') || '';
        var sort = params.get('sort') || 'name';

        var items = data.pets.filter(function (pet) {
            if (q && pet.name.toLowerCase().indexOf(q) === -1 && pet.breed.toLowerCase().indexOf(q) === -1) {
                return false;
            }
            if (species && pet.species !== species) {
                return false;
            }
            if (petStatus && pet.status !== petStatus) {
                return false;
            }
            return true;
        });

        items.sort(function (a, b) {
            if (sort === '-name') {
                return b.name.localeCompare(a.name, 'ru');
            }
            if (sort === 'age_months' || sort === '-age_months') {
                var first = parseInt(a.age, 10) || 0;
                var second = parseInt(b.age, 10) || 0;
                return sort === 'age_months' ? first - second : second - first;
            }
            return a.name.localeCompare(b.name, 'ru');
        });

        return items;
    }

    function load(page) {
        var params = currentParams(page);
        var favOnly = form.querySelector('[data-fav-only]');

        if (favOnly && favOnly.checked) {
            params.set('ids', readFavorites().join(','));
        }

        requestNumber += 1;
        var current = requestNumber;
        showLoading();

        var isStatic = api.indexOf('.json') !== -1;
        var url;

        if (isStatic) {
            url = api + '?v=' + Date.now();
        } else {
            var query = params.toString();
            url = api + (query ? '?' + query : '');
        }

        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                if (current !== requestNumber) {
                    return;
                }

                var pageNumber = 1;
                var pages = 1;
                var total = data.total;
                var pets = data.pets;

                if (isStatic) {
                    staticCache = staticCache || data;
                    pets = filterStatic(staticCache, params);
                    if (favOnly && favOnly.checked) {
                        var ids = readFavorites();
                        pets = pets.filter(function (pet) {
                            return ids.indexOf(String(pet.id)) !== -1;
                        });
                    }
                    total = pets.length;
                    pages = Math.max(1, Math.ceil(total / 20));
                    pageNumber = Math.min(Math.max(1, parseInt(page, 10) || 1), pages);
                    pets = pets.slice((pageNumber - 1) * 20, pageNumber * 20);
                } else {
                    pageNumber = data.page;
                    pages = data.pages;
                }

                render(pets, total, pageNumber, pages);
                hideLoading();

                if (!isStatic) {
                    var clean = params.toString();
                    var next = window.location.pathname + (clean ? '?' + clean : '');
                    window.history.replaceState({}, '', next);
                }
            })
            .catch(function () {
                if (current !== requestNumber) {
                    return;
                }
                hideLoading();
                if (errorBox) {
                    errorBox.hidden = false;
                }
            });
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        load(1);
    });

    form.addEventListener('change', function (event) {
        if (event.target.matches('select, [data-fav-only]')) {
            load(1);
        }
    });

    var searchInput = form.querySelector('input[name="q"]');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            window.clearTimeout(debounceTimer);
            debounceTimer = window.setTimeout(function () {
                load(1);
            }, 300);
        });
    }

    document.addEventListener('click', function (event) {
        var link = event.target.closest('[data-page]');
        if (!link || !pagination || !pagination.contains(link)) {
            return;
        }
        event.preventDefault();
        load(parseInt(link.getAttribute('data-page'), 10));
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    window.PetsCatalog = { reload: function () { load(1); } };

    paintAllFavorites();

    if (form.querySelector('[data-fav-only]') && form.querySelector('[data-fav-only]').checked) {
        load(1);
    }
}());

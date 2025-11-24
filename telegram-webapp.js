/**
 * Telegram Web App Integration Module
 * Полная интеграция с Telegram Mini Apps API
 * Использует все современные функции Telegram Web App
 */

class TelegramWebApp {
    constructor() {
        this.webApp = null;
        this.isTelegram = false;
        this.init();
    }

    /**
     * Инициализация Telegram Web App
     */
    init() {
        // Проверяем, запущено ли приложение в Telegram
        if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
            this.webApp = window.Telegram.WebApp;
            this.isTelegram = true;
            this.setupTelegramApp();
        } else {
            // Режим разработки/тестирования вне Telegram
            console.log('Telegram Web App не обнаружен. Режим разработки.');
            this.setupDevelopmentMode();
        }
    }

    /**
     * Настройка приложения для работы в Telegram
     */
    setupTelegramApp() {
        // Уведомляем Telegram, что приложение готово
        this.webApp.ready();

        // ВАЖНО: Сначала запрашиваем viewport для получения правильных размеров
        this.webApp.requestViewport();

        // Расширяем приложение на весь экран (убирает стандартные отступы)
        this.webApp.expand();

        // Блокируем закрытие приложения свайпом - используем все доступные методы
        this.setupSwipeProtection();

        // Настраиваем цвета заголовка и фона в соответствии с темой
        this.setupTheme();

        // Настраиваем кнопки
        this.setupButtons();

        // Настраиваем обработчики событий
        this.setupEventHandlers();

        // Включаем тактильную обратную связь
        this.enableHapticFeedback();

        // Убираем лишнее белое пространство внизу (учитывая шапку и подвал Telegram)
        this.removeBottomSpacing();

        // Настраиваем полноэкранный режим если доступен
        this.setupFullscreenMode();

        console.log('Telegram Web App инициализирован:', {
            version: this.webApp.version,
            platform: this.webApp.platform,
            colorScheme: this.webApp.colorScheme,
            themeParams: this.webApp.themeParams
        });
    }

    /**
     * Настройка темы приложения
     */
    setupTheme() {
        const themeParams = this.webApp.themeParams;
        
        // Устанавливаем цвет заголовка
        if (themeParams.bg_color) {
            this.webApp.setHeaderColor(themeParams.bg_color);
        } else {
            // Используем градиент из CSS
            this.webApp.setHeaderColor('#94d4ff');
        }

        // Устанавливаем цвет фона
        if (themeParams.bg_color) {
            this.webApp.setBackgroundColor(themeParams.bg_color);
        } else {
            this.webApp.setBackgroundColor('#ffffff');
        }

        // Применяем CSS переменные для темы
        if (themeParams.text_color) {
            document.documentElement.style.setProperty('--tg-theme-text-color', themeParams.text_color);
        }
        if (themeParams.hint_color) {
            document.documentElement.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
        }
        if (themeParams.link_color) {
            document.documentElement.style.setProperty('--tg-theme-link-color', themeParams.link_color);
        }
        if (themeParams.button_color) {
            document.documentElement.style.setProperty('--tg-theme-button-color', themeParams.button_color);
        }
        if (themeParams.button_text_color) {
            document.documentElement.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
        }
        if (themeParams.secondary_bg_color) {
            document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color);
        }
    }

    /**
     * Настройка кнопок Telegram (MainButton, BackButton)
     */
    setupButtons() {
        // Настройка MainButton для кнопок "Связаться"
        this.setupMainButton();

        // Настройка BackButton для навигации
        this.setupBackButton();
    }

    /**
     * Настройка главной кнопки (MainButton)
     * MainButton - это нативная кнопка Telegram, которая отображается внизу экрана
     * Она интегрирована в интерфейс Telegram и всегда видна поверх контента
     */
    setupMainButton() {
        const mainButton = this.webApp.MainButton;
        
        // Устанавливаем текст кнопки
        mainButton.setText('Связаться');
        
        // Устанавливаем цвет кнопки из темы или используем градиент
        const buttonColor = this.webApp.themeParams.button_color || '#94d4ff';
        mainButton.setParams({
            color: buttonColor,
            text_color: this.webApp.themeParams.button_text_color || '#ffffff'
        });

        // Обработчик клика на главную кнопку
        mainButton.onClick(() => {
            this.handleContactClick();
        });

        // Скрываем HTML кнопки на странице, так как используем MainButton
        this.hideHTMLContactButtons();

        // Показываем кнопку при прокрутке к секциям с контактами
        this.setupMainButtonVisibility();

        // Показываем MainButton сразу, так как на странице есть кнопки контакта
        mainButton.show();
    }

    /**
     * Скрытие HTML кнопок "Связаться" при использовании MainButton
     * MainButton заменяет их в Telegram Mini App
     */
    hideHTMLContactButtons() {
        const contactButtons = document.querySelectorAll('.contact-button, .values-contact-button');
        contactButtons.forEach(button => {
            // Скрываем кнопки в Telegram, так как используется MainButton
            button.style.display = 'none';
            button.classList.add('tg-hidden-button');
        });
        
        // Также скрываем кнопку в подвале через CSS класс
        const footerButton = document.querySelector('.values-contact-button');
        if (footerButton) {
            footerButton.style.display = 'none';
        }
    }

    /**
     * Управление видимостью MainButton при прокрутке
     */
    setupMainButtonVisibility() {
        const mainButton = this.webApp.MainButton;
        const contactButtons = document.querySelectorAll('.contact-button, .values-contact-button');
        
        // Показываем кнопку, если есть кнопки контакта на странице
        if (contactButtons.length > 0) {
            mainButton.show();
        }

        // Отслеживаем прокрутку для показа/скрытия кнопки
        let lastScrollTop = 0;
        const scrollThreshold = 100;

        const handleScroll = () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Показываем кнопку при прокрутке вниз
            if (scrollTop > scrollThreshold && scrollTop > lastScrollTop) {
                mainButton.show();
            }
            
            lastScrollTop = scrollTop;
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
    }

    /**
     * Настройка кнопки "Назад" (BackButton)
     */
    setupBackButton() {
        const backButton = this.webApp.BackButton;
        
        // Показываем кнопку "Назад" при необходимости
        // В данном случае скрываем, так как это одностраничное приложение
        backButton.hide();

        // Обработчик клика на кнопку "Назад"
        backButton.onClick(() => {
            this.hapticFeedback('light');
            window.history.back();
        });
    }

    /**
     * Обработка клика на кнопку "Связаться"
     * Открывает личный аккаунт @a_ivaschenko (не канал)
     */
    handleContactClick() {
        this.hapticFeedback('medium');
        
        // Личный аккаунт для связи (не канал)
        const personalTelegramUsername = 'a_ivaschenko';
        const email = 'anna.anna.ivaschenko@gmail.com';

        // Показываем меню выбора способа связи
        this.showPopup({
            title: 'Связаться',
            message: 'Выберите способ связи:',
            buttons: [
                {
                    id: 'telegram',
                    type: 'default',
                    text: '📱 Telegram'
                },
                {
                    id: 'email',
                    type: 'default',
                    text: '✉️ Email'
                },
                {
                    id: 'cancel',
                    type: 'cancel',
                    text: 'Отмена'
                }
            ]
        }, (buttonId) => {
            if (buttonId === 'telegram') {
                this.hapticFeedback('notification', 'success');
                // Открываем личный аккаунт @a_ivaschenko
                this.openTelegramLink(`https://t.me/${personalTelegramUsername}`);
            } else if (buttonId === 'email') {
                this.hapticFeedback('notification', 'success');
                this.openLink(`mailto:${email}?subject=Контакт с сайта-визитки`);
            } else {
                this.hapticFeedback('selection');
            }
        });
    }

    /**
     * Настройка обработчиков событий Telegram
     */
    setupEventHandlers() {
        // Обработка изменения темы
        this.webApp.onEvent('themeChanged', () => {
            console.log('Тема изменена');
            this.setupTheme();
        });

        // Обработка изменения viewport
        this.webApp.onEvent('viewportChanged', (event) => {
            console.log('Viewport изменен:', event);
            // Можно обновить layout при изменении размера окна
            this.handleViewportChange(event);
        });

        // Обработка закрытия приложения
        this.webApp.onEvent('close', () => {
            console.log('Приложение закрывается');
        });

        // Обработка изменения видимости
        this.webApp.onEvent('visibilityChanged', (event) => {
            console.log('Видимость изменена:', event);
        });

        // Обработка изменения состояния MainButton
        this.webApp.onEvent('mainButtonClicked', () => {
            this.handleContactClick();
        });

        // Обработка изменения состояния BackButton
        this.webApp.onEvent('backButtonClicked', () => {
            this.hapticFeedback('light');
        });
    }

    /**
     * Обработка изменения viewport
     */
    handleViewportChange(event) {
        // Можно добавить логику для адаптации под изменение размера окна
        if (event.isStateStable) {
            // Viewport стабилизировался - можно обновить layout
            console.log('Viewport стабилизирован:', {
                height: event.height,
                width: event.width,
                isExpanded: event.isExpanded,
                isStateStable: event.isStateStable
            });
        }
    }

    /**
     * Включение тактильной обратной связи
     */
    enableHapticFeedback() {
        // Тактильная обратная связь уже доступна через this.webApp.HapticFeedback
    }

    /**
     * Тактильная обратная связь
     * @param {string} type - Тип вибрации: 'impact', 'notification', 'selectionChanged'
     * @param {string} style - Стиль (для impact): 'light', 'medium', 'heavy', 'rigid', 'soft'
     */
    hapticFeedback(type = 'impact', style = 'light') {
        if (!this.isTelegram) return;

        const haptic = this.webApp.HapticFeedback;
        
        switch (type) {
            case 'impact':
                haptic.impactOccurred(style);
                break;
            case 'notification':
                haptic.notificationOccurred(style); // 'error', 'success', 'warning'
                break;
            case 'selection':
                haptic.selectionChanged();
                break;
            default:
                haptic.impactOccurred('light');
        }
    }

    /**
     * Открытие ссылки через Telegram
     * @param {string} url - URL для открытия
     */
    openTelegramLink(url) {
        if (this.isTelegram) {
            this.webApp.openTelegramLink(url);
        } else {
            window.open(url, '_blank');
        }
    }

    /**
     * Открытие внешней ссылки
     * @param {string} url - URL для открытия
     */
    openLink(url) {
        if (this.isTelegram) {
            this.webApp.openLink(url, { try_instant_view: true });
        } else {
            window.open(url, '_blank');
        }
    }

    /**
     * Показ всплывающего окна
     * @param {Object} params - Параметры окна
     * @param {Function} callback - Callback функция
     */
    showPopup(params, callback) {
        if (this.isTelegram) {
            try {
                this.webApp.showPopup(params, callback);
            } catch (e) {
                console.error('Ошибка при показе popup:', e);
                // Fallback на showAlert
                this.showAlert(params.message || 'Ошибка', callback);
            }
        } else {
            // Fallback для режима разработки
            const result = confirm(params.message || 'Подтвердите действие');
            callback && callback(result ? 'ok' : 'cancel');
        }
    }

    /**
     * Показ алерта
     * @param {string} message - Сообщение
     * @param {Function} callback - Callback функция
     */
    showAlert(message, callback) {
        if (this.isTelegram) {
            this.webApp.showAlert(message, callback);
        } else {
            alert(message);
            callback && callback();
        }
    }

    /**
     * Показ подтверждения
     * @param {string} message - Сообщение
     * @param {Function} callback - Callback функция
     */
    showConfirm(message, callback) {
        if (this.isTelegram) {
            this.webApp.showConfirm(message, callback);
        } else {
            const result = confirm(message);
            callback && callback(result);
        }
    }

    /**
     * Запрос контакта пользователя
     * @param {Function} callback - Callback функция
     */
    requestContact(callback) {
        if (this.isTelegram) {
            this.webApp.requestContact(callback);
        } else {
            console.log('Запрос контакта (только в Telegram)');
            callback && callback({ contact: null });
        }
    }

    /**
     * Запрос номера телефона
     * @param {Function} callback - Callback функция
     */
    requestPhoneNumber(callback) {
        if (this.isTelegram) {
            this.webApp.requestPhoneNumber(callback);
        } else {
            console.log('Запрос номера телефона (только в Telegram)');
            callback && callback({ phone_number: null });
        }
    }

    /**
     * Запрос доступа на запись
     * @param {Function} callback - Callback функция
     */
    requestWriteAccess(callback) {
        if (this.isTelegram) {
            this.webApp.requestWriteAccess(callback);
        } else {
            console.log('Запрос доступа на запись (только в Telegram)');
            callback && callback({ write_access_allowed: false });
        }
    }

    /**
     * Работа с CloudStorage
     */
    getCloudStorage() {
        if (this.isTelegram) {
            return this.webApp.CloudStorage;
        }
        return null;
    }

    /**
     * Сохранение данных в CloudStorage
     * @param {string} key - Ключ
     * @param {string} value - Значение
     * @param {Function} callback - Callback функция
     */
    saveToCloudStorage(key, value, callback) {
        const cloudStorage = this.getCloudStorage();
        if (cloudStorage) {
            cloudStorage.setItem(key, value, callback);
        } else {
            // Fallback на localStorage
            try {
                localStorage.setItem(key, value);
                callback && callback(true);
            } catch (e) {
                callback && callback(false);
            }
        }
    }

    /**
     * Получение данных из CloudStorage
     * @param {string} key - Ключ
     * @param {Function} callback - Callback функция
     */
    getFromCloudStorage(key, callback) {
        const cloudStorage = this.getCloudStorage();
        if (cloudStorage) {
            cloudStorage.getItem(key, callback);
        } else {
            // Fallback на localStorage
            try {
                const value = localStorage.getItem(key);
                callback && callback(value);
            } catch (e) {
                callback && callback(null);
            }
        }
    }

    /**
     * Получение данных пользователя из initData
     */
    getUserData() {
        if (this.isTelegram && this.webApp.initDataUnsafe?.user) {
            return this.webApp.initDataUnsafe.user;
        }
        return null;
    }

    /**
     * Получение данных инициализации
     */
    getInitData() {
        if (this.isTelegram) {
            return this.webApp.initData;
        }
        return null;
    }

    /**
     * Получение небезопасных данных инициализации (для разработки)
     */
    getInitDataUnsafe() {
        if (this.isTelegram) {
            return this.webApp.initDataUnsafe;
        }
        return null;
    }

    /**
     * Настройка защиты от закрытия свайпом
     * Использует все доступные методы для максимальной защиты
     */
    setupSwipeProtection() {
        if (!this.isTelegram) return;

        try {
            // Метод 1: enableClosingConfirmation - требует подтверждения перед закрытием
            if (typeof this.webApp.enableClosingConfirmation === 'function') {
                this.webApp.enableClosingConfirmation();
                console.log('✅ enableClosingConfirmation включен');
            }

            // Метод 2: disableVerticalSwipes - блокирует вертикальные свайпы (если доступен)
            if (typeof this.webApp.disableVerticalSwipes === 'function') {
                this.webApp.disableVerticalSwipes();
                console.log('✅ disableVerticalSwipes включен');
            }

            // Метод 3: Обработка события закрытия для предотвращения
            if (typeof this.webApp.onEvent === 'function') {
                this.webApp.onEvent('viewportChanged', (event) => {
                    // Если viewport изменился из-за попытки закрытия, предотвращаем
                    if (event.isStateStable === false) {
                        console.log('⚠️ Обнаружена попытка закрытия');
                    }
                });
            }

            // Метод 4: Перехват события закрытия
            const originalClose = this.webApp.close;
            this.webApp.close = () => {
                // Можно добавить дополнительную логику перед закрытием
                console.log('⚠️ Попытка закрытия приложения');
                originalClose.call(this.webApp);
            };

        } catch (e) {
            console.error('Ошибка при настройке защиты от свайпа:', e);
        }
    }

    /**
     * Настройка полноэкранного режима если доступен
     */
    setupFullscreenMode() {
        if (!this.isTelegram) return;

        try {
            // Проверяем доступность полноэкранного режима
            // В новых версиях Telegram может быть доступен через параметры Mini App
            if (this.webApp.isExpanded) {
                console.log('✅ Приложение расширено на весь экран');
            }

            // Если доступен метод для полноэкранного режима
            if (typeof this.webApp.requestFullscreen === 'function') {
                // Не вызываем автоматически, так как это может быть навязчиво
                // Но сохраняем метод для возможного использования
                console.log('ℹ️ requestFullscreen доступен');
            }

        } catch (e) {
            console.error('Ошибка при настройке полноэкранного режима:', e);
        }
    }

    /**
     * Убирает лишнее белое пространство внизу страницы в Telegram
     * Учитывает шапку и подвал Telegram через contentSafeAreaInsets
     */
    removeBottomSpacing() {
        if (!this.isTelegram) return;
        
        // Получаем правильные отступы с учетом шапки и подвала Telegram
        // contentSafeAreaInsets доступен в новых версиях Telegram Web App API
        let contentSafeAreaBottom = 0;
        
        // Пробуем получить через API
        if (this.webApp.contentSafeAreaInsets) {
            contentSafeAreaBottom = this.webApp.contentSafeAreaInsets.bottom || 0;
        } else if (this.webApp.safeAreaInsets) {
            // Fallback на safeAreaInsets если contentSafeAreaInsets недоступен
            contentSafeAreaBottom = this.webApp.safeAreaInsets.bottom || 0;
        }
        
        // Убираем лишнее пространство через CSS
        // Используем 0, так как expand() уже должен убрать стандартные отступы
        const style = document.createElement('style');
        style.id = 'telegram-bottom-spacing-fix';
        style.textContent = `
            html {
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }
            body {
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
                /* Убираем все отступы снизу */
                overflow-x: hidden !important;
            }
            .main-wrapper {
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }
            .main-container {
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }
            /* Убираем лишнее пространство после последней секции */
            .project-section-7 {
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }
            .values-banner {
                margin-bottom: 0 !important;
                padding-bottom: 0 !important;
            }
            /* Убираем лишнее пространство внизу страницы */
            body::after {
                display: none !important;
            }
        `;
        
        // Удаляем старый стиль если есть
        const oldStyle = document.getElementById('telegram-bottom-spacing-fix');
        if (oldStyle) {
            oldStyle.remove();
        }
        
        document.head.appendChild(style);
        
        // Также применяем стили напрямую к body для надежности
        document.body.style.paddingBottom = '0';
        document.body.style.marginBottom = '0';
        document.documentElement.style.paddingBottom = '0';
        document.documentElement.style.marginBottom = '0';
        
        console.log('✅ Убрано лишнее белое пространство внизу', {
            contentSafeAreaBottom: contentSafeAreaBottom,
            viewportHeight: this.webApp.viewportHeight,
            viewportStableHeight: this.webApp.viewportStableHeight,
            isExpanded: this.webApp.isExpanded,
            platform: this.webApp.platform
        });
    }

    /**
     * Режим разработки (вне Telegram)
     * В этом режиме HTML кнопки остаются видимыми, так как MainButton недоступен
     */
    setupDevelopmentMode() {
        console.log('Режим разработки активирован');
        // В режиме разработки HTML кнопки остаются видимыми
        // MainButton доступен только в Telegram Mini App
        const contactButtons = document.querySelectorAll('.contact-button, .values-contact-button');
        contactButtons.forEach(button => {
            button.style.display = '';
            button.classList.remove('tg-hidden-button');
        });
    }

    /**
     * Закрытие приложения
     */
    close() {
        if (this.isTelegram) {
            this.webApp.close();
        } else {
            console.log('Закрытие приложения (только в Telegram)');
        }
    }

    /**
     * Проверка, запущено ли приложение в Telegram
     */
    isInTelegram() {
        return this.isTelegram;
    }

    /**
     * Получение версии Telegram Web App
     */
    getVersion() {
        if (this.isTelegram) {
            return this.webApp.version;
        }
        return null;
    }

    /**
     * Получение платформы
     */
    getPlatform() {
        if (this.isTelegram) {
            return this.webApp.platform;
        }
        return 'unknown';
    }

    /**
     * Проверка, расширено ли приложение
     */
    isExpanded() {
        if (this.isTelegram) {
            return this.webApp.isExpanded;
        }
        return false;
    }

    /**
     * Показ QR сканера
     * @param {Object} params - Параметры сканера
     * @param {Function} callback - Callback функция с результатом
     */
    showScanQrPopup(params, callback) {
        if (this.isTelegram && this.webApp.showScanQrPopup) {
            try {
                this.webApp.showScanQrPopup(params, callback);
            } catch (e) {
                console.error('Ошибка при показе QR сканера:', e);
                callback && callback(null);
            }
        } else {
            console.log('QR сканер недоступен (только в Telegram)');
            callback && callback(null);
        }
    }

    /**
     * Закрытие QR сканера
     */
    closeScanQrPopup() {
        if (this.isTelegram && this.webApp.closeScanQrPopup) {
            try {
                this.webApp.closeScanQrPopup();
            } catch (e) {
                console.error('Ошибка при закрытии QR сканера:', e);
            }
        }
    }

    /**
     * Чтение текста из буфера обмена
     * @param {Function} callback - Callback функция с текстом
     */
    readTextFromClipboard(callback) {
        if (this.isTelegram && this.webApp.readTextFromClipboard) {
            try {
                this.webApp.readTextFromClipboard(callback);
            } catch (e) {
                console.error('Ошибка при чтении из буфера обмена:', e);
                callback && callback(null);
            }
        } else {
            // Fallback на Clipboard API
            if (navigator.clipboard && navigator.clipboard.readText) {
                navigator.clipboard.readText().then(text => {
                    callback && callback(text);
                }).catch(() => {
                    callback && callback(null);
                });
            } else {
                callback && callback(null);
            }
        }
    }

    /**
     * Запрос доступа на чтение
     * @param {Function} callback - Callback функция
     */
    requestReadAccess(callback) {
        if (this.isTelegram && this.webApp.requestReadAccess) {
            try {
                this.webApp.requestReadAccess(callback);
            } catch (e) {
                console.error('Ошибка при запросе доступа на чтение:', e);
                callback && callback({ read_access_allowed: false });
            }
        } else {
            console.log('Запрос доступа на чтение (только в Telegram)');
            callback && callback({ read_access_allowed: false });
        }
    }

    /**
     * Отправка данных боту
     * @param {string} data - Данные для отправки
     */
    sendData(data) {
        if (this.isTelegram) {
            try {
                this.webApp.sendData(data);
                this.hapticFeedback('notification', 'success');
            } catch (e) {
                console.error('Ошибка при отправке данных:', e);
            }
        } else {
            console.log('Отправка данных боту (только в Telegram):', data);
        }
    }

    /**
     * Открытие инвойса (для платежей)
     * @param {string} url - URL инвойса
     * @param {Function} callback - Callback функция
     */
    openInvoice(url, callback) {
        if (this.isTelegram && this.webApp.openInvoice) {
            try {
                this.webApp.openInvoice(url, callback);
            } catch (e) {
                console.error('Ошибка при открытии инвойса:', e);
                callback && callback(null);
            }
        } else {
            console.log('Открытие инвойса (только в Telegram)');
            callback && callback(null);
        }
    }

    /**
     * Показ всплывающего окна с подтверждением
     * @param {string} message - Сообщение
     * @param {Function} callback - Callback функция (true/false)
     */
    showConfirm(message, callback) {
        if (this.isTelegram) {
            try {
                this.webApp.showConfirm(message, callback);
            } catch (e) {
                console.error('Ошибка при показе подтверждения:', e);
                // Fallback на обычный confirm
                const result = confirm(message);
                callback && callback(result);
            }
        } else {
            const result = confirm(message);
            callback && callback(result);
        }
    }

    /**
     * Установка цвета заголовка
     * @param {string} color - Цвет в формате #RRGGBB
     */
    setHeaderColor(color) {
        if (this.isTelegram) {
            try {
                this.webApp.setHeaderColor(color);
            } catch (e) {
                console.error('Ошибка при установке цвета заголовка:', e);
            }
        }
    }

    /**
     * Установка цвета фона
     * @param {string} color - Цвет в формате #RRGGBB
     */
    setBackgroundColor(color) {
        if (this.isTelegram) {
            try {
                this.webApp.setBackgroundColor(color);
            } catch (e) {
                console.error('Ошибка при установке цвета фона:', e);
            }
        }
    }

    /**
     * Получение информации о приложении для отладки
     */
    getDebugInfo() {
        if (this.isTelegram) {
            return {
                version: this.webApp.version,
                platform: this.webApp.platform,
                colorScheme: this.webApp.colorScheme,
                isExpanded: this.webApp.isExpanded,
                viewportHeight: this.webApp.viewportHeight,
                viewportStableHeight: this.webApp.viewportStableHeight,
                headerColor: this.webApp.headerColor,
                backgroundColor: this.webApp.backgroundColor,
                themeParams: this.webApp.themeParams,
                initData: this.webApp.initData ? 'present' : 'absent',
                initDataUnsafe: this.webApp.initDataUnsafe
            };
        }
        return {
            isTelegram: false,
            message: 'Приложение запущено вне Telegram'
        };
    }
}

// Создаем глобальный экземпляр
const telegramWebApp = new TelegramWebApp();

// Экспортируем для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TelegramWebApp;
}


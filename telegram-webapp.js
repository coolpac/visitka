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
        try {
            // Уведомляем Telegram, что приложение готово
            this.webApp.ready();

            // ВАЖНО: Сначала запрашиваем viewport для получения правильных размеров
            this.webApp.requestViewport();

            // Расширяем приложение на весь экран (убирает стандартные отступы)
            this.webApp.expand();

            // Настраиваем цвета заголовка и фона в соответствии с темой
            this.setupTheme();

            // Настраиваем обработчики событий (до кнопок, чтобы перехватить события)
            this.setupEventHandlers();

            // Настраиваем кнопки (после expand и ready)
            this.setupButtons();

            // Включаем тактильную обратную связь
            this.enableHapticFeedback();

            // ВАЖНО: Убираем лишнее белое пространство и настраиваем стили СРАЗУ
            console.log('[TG-Init] 🎯 Вызов removeBottomSpacing (первый раз)');
            this.removeBottomSpacing();

            // Блокируем закрытие приложения свайпом - вызываем после небольшой задержки
            // чтобы SDK был полностью готов
            setTimeout(() => {
                console.log('[TG-Init] 🛡️ Вызов setupSwipeProtection');
                this.setupSwipeProtection();
            }, 100);
            
            // НЕ вызываем removeBottomSpacing повторно - функция защищена от множественных вызовов
            // Но проверяем, что стили применились после загрузки
            const checkStylesAfterLoad = () => {
                setTimeout(() => {
                    const wrapper = document.querySelector('.main-wrapper');
                    if (wrapper) {
                        const computed = window.getComputedStyle(wrapper);
                        const hasTgClass = document.body.classList.contains('tg-webapp');
                        const overflowY = computed.overflowY;
                        console.log('[TG-Init] 🔍 Проверка стилей после загрузки:', {
                            hasTgClass: hasTgClass,
                            overflowY: overflowY,
                            height: computed.height,
                            width: computed.width
                        });
                        
                        if (!hasTgClass || overflowY !== 'auto') {
                            console.warn('[TG-Init] ⚠️ Стили не применились правильно, повторный вызов removeBottomSpacing');
                            // Сбрасываем флаг для повторного вызова
                            window._telegramRemoveBottomSpacingCalled = false;
                            this.removeBottomSpacing();
                        } else {
                            console.log('[TG-Init] ✅ Стили применены правильно');
                        }
                    }
                }, 500);
            };
            
            if (document.readyState === 'complete') {
                checkStylesAfterLoad();
            } else {
                window.addEventListener('load', checkStylesAfterLoad, { once: true });
            }

            // Настраиваем полноэкранный режим если доступен
            this.setupFullscreenMode();

            console.log('✅ Telegram Web App инициализирован:', {
                version: this.webApp.version,
                platform: this.webApp.platform,
                colorScheme: this.webApp.colorScheme,
                themeParams: this.webApp.themeParams,
                isExpanded: this.webApp.isExpanded
            });
        } catch (error) {
            console.error('❌ Ошибка при настройке Telegram Web App:', error);
        }
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
        try {
            if (!this.webApp || !this.webApp.MainButton) {
                console.error('❌ MainButton недоступен');
                return;
            }
            
            const mainButton = this.webApp.MainButton;
            
            // Устанавливаем текст кнопки
            mainButton.setText('Связаться');
            
            // Устанавливаем цвет кнопки из темы или используем градиент
            const buttonColor = this.webApp.themeParams?.button_color || '#94d4ff';
            const textColor = this.webApp.themeParams?.button_text_color || '#ffffff';
            
            mainButton.setParams({
                color: buttonColor,
                text_color: textColor
            });

            // Обработчик клика на главную кнопку
            mainButton.onClick(() => {
                this.handleContactClick();
            });

            // Скрываем HTML кнопки на странице, так как используем MainButton
            this.hideHTMLContactButtons();

            // Показываем кнопку при прокрутке к секциям с контактами
            this.setupMainButtonVisibility();

            // ВАЖНО: Показываем MainButton после небольшой задержки, чтобы убедиться что все готово
            setTimeout(() => {
                try {
                    mainButton.show();
                    console.log('✅ MainButton показан');
                } catch (error) {
                    console.error('❌ Ошибка при показе MainButton:', error);
                    // Пробуем еще раз через секунду
                    setTimeout(() => {
                        try {
                            mainButton.show();
                            console.log('✅ MainButton показан (повторная попытка)');
                        } catch (e) {
                            console.error('❌ Ошибка при повторной попытке показа MainButton:', e);
                        }
                    }, 1000);
                }
            }, 100);
            
        } catch (error) {
            console.error('❌ Ошибка при настройке MainButton:', error);
        }
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
        try {
            if (!this.webApp || !this.webApp.MainButton) {
                console.error('❌ MainButton недоступен для setupMainButtonVisibility');
                return;
            }
            
            const mainButton = this.webApp.MainButton;
            const contactButtons = document.querySelectorAll('.contact-button, .values-contact-button');
            
            // Показываем кнопку, если есть кнопки контакта на странице
            if (contactButtons.length > 0) {
                setTimeout(() => {
                    try {
                        mainButton.show();
                        console.log('✅ MainButton показан через setupMainButtonVisibility');
                    } catch (error) {
                        console.error('❌ Ошибка при показе MainButton:', error);
                    }
                }, 200);
            }

            // Отслеживаем прокрутку для показа/скрытия кнопки
            let lastScrollTop = 0;
            const scrollThreshold = 100;

            const handleScroll = () => {
                try {
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    
                    // Показываем кнопку при прокрутке вниз
                    if (scrollTop > scrollThreshold && scrollTop > lastScrollTop) {
                        mainButton.show();
                    }
                    
                    lastScrollTop = scrollTop;
                } catch (error) {
                    console.error('❌ Ошибка в handleScroll:', error);
                }
            };

            window.addEventListener('scroll', handleScroll, { passive: true });
        } catch (error) {
            console.error('❌ Ошибка в setupMainButtonVisibility:', error);
        }
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
            console.log('[TG-Event] 🔄 viewportChanged событие:', {
                isStateStable: event.isStateStable,
                viewportHeight: this.webApp.viewportHeight,
                viewportStableHeight: this.webApp.viewportStableHeight
            });
            // Можно обновить layout при изменении размера окна
            this.handleViewportChange(event);
            // НЕ вызываем removeBottomSpacing здесь - функция защищена от множественных вызовов
            // CSS переменные обновляются автоматически через слушатель в removeBottomSpacing
            
            // Показываем MainButton при стабилизации viewport
            if (event.isStateStable && this.webApp && this.webApp.MainButton) {
                try {
                    this.webApp.MainButton.show();
                    console.log('[TG-Event] ✅ MainButton показан через viewportChanged');
                } catch (error) {
                    console.error('[TG-Event] ❌ Ошибка при показе MainButton через viewportChanged:', error);
                }
            }
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
        if (!this.isTelegram) {
            console.log('[TG-Swipe] ⏭️ setupSwipeProtection: не в Telegram, пропускаем');
            return;
        }

        // Защита от множественных вызовов
        if (window._telegramSwipeProtectionSetup) {
            console.log('[TG-Swipe] ⚠️ setupSwipeProtection уже вызывался, пропускаем');
            return;
        }
        window._telegramSwipeProtectionSetup = true;

        console.log('[TG-Swipe] 🚀 setupSwipeProtection вызван');
        console.log('[TG-Swipe] 📊 Состояние SDK:', {
            version: this.webApp.version,
            platform: this.webApp.platform,
            isExpanded: this.webApp.isExpanded,
            hasEnableClosingConfirmation: typeof this.webApp.enableClosingConfirmation === 'function',
            hasDisableVerticalSwipes: typeof this.webApp.disableVerticalSwipes === 'function'
        });

        try {
            // Метод 1: enableClosingConfirmation - требует подтверждения перед закрытием
            if (typeof this.webApp.enableClosingConfirmation === 'function') {
                this.webApp.enableClosingConfirmation();
                console.log('[TG-Swipe] ✅ enableClosingConfirmation включен');
            } else {
                console.warn('[TG-Swipe] ⚠️ enableClosingConfirmation недоступен');
            }

            // Метод 2: disableVerticalSwipes - блокирует вертикальные свайпы (Bot API 7.7+)
            // ВАЖНО: Вызываем с задержкой после expand() для надежности
            if (typeof this.webApp.disableVerticalSwipes === 'function') {
                // Пробуем сразу
                try {
                    this.webApp.disableVerticalSwipes();
                    console.log('[TG-Swipe] ✅ disableVerticalSwipes включен (сразу)');
                    console.log('[TG-Swipe] 📊 isVerticalSwipesEnabled:', this.webApp.isVerticalSwipesEnabled);
                } catch (e) {
                    console.warn('[TG-Swipe] ⚠️ Первая попытка disableVerticalSwipes не удалась:', e.message);
                    // Если не получилось, пробуем через задержку
                    setTimeout(() => {
                        try {
                            this.webApp.disableVerticalSwipes();
                            console.log('[TG-Swipe] ✅ disableVerticalSwipes включен (после задержки)');
                            console.log('[TG-Swipe] 📊 isVerticalSwipesEnabled:', this.webApp.isVerticalSwipesEnabled);
                        } catch (e2) {
                            console.error('[TG-Swipe] ❌ disableVerticalSwipes недоступен:', e2);
                        }
                    }, 200);
                }
            } else {
                console.warn('[TG-Swipe] ⚠️ disableVerticalSwipes недоступен в этой версии Telegram (требуется Bot API 7.7+)');
            }

            console.log('[TG-Swipe] ✅ Защита от свайпа настроена');

        } catch (e) {
            console.error('[TG-Swipe] ❌ Ошибка при настройке защиты от свайпа:', e);
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
     * Использует правильный подход: body.tg-webapp с position: fixed и прокручиваемый контент
     * Основано на решении из https://github.com/QB-Quardobot/barsa
     */
    removeBottomSpacing() {
        if (!this.isTelegram) {
            console.log('[TG-Fix] ⏭️ removeBottomSpacing: не в Telegram, пропускаем');
            return;
        }
        
        // Защита от множественных вызовов
        const callId = Date.now();
        if (window._telegramRemoveBottomSpacingCalled) {
            console.log('[TG-Fix] ⚠️ removeBottomSpacing уже вызывался, пропускаем повторный вызов');
            return;
        }
        window._telegramRemoveBottomSpacingCalled = true;
        
        console.log('[TG-Fix] 🚀 removeBottomSpacing вызван (ID:', callId + ')');
        console.log('[TG-Fix] 📊 Состояние:', {
            readyState: document.readyState,
            hasBody: !!document.body,
            bodyClasses: document.body ? Array.from(document.body.classList) : [],
            viewportHeight: this.webApp.viewportHeight,
            viewportStableHeight: this.webApp.viewportStableHeight
        });
        
        // Добавляем класс tg-webapp к body для применения правильных стилей
        const hadClass = document.body.classList.contains('tg-webapp');
        document.body.classList.add('tg-webapp');
        console.log('[TG-Fix] ✅ Класс tg-webapp добавлен к body (был:', hadClass + ')');
        
        // Предотвращаем копирование и выделение текста (как в barsa)
        // ВАЖНО: Добавляем listeners только один раз
        if (!window._telegramCopyPreventionSetup) {
            const preventSelection = (e) => {
                if (e.target && e.target.closest && e.target.closest('input, textarea')) {
                    return; // Allow selection in inputs
                }
                e.preventDefault();
                return false;
            };
            
            const preventCopy = (e) => {
                if (e.target && e.target.closest && e.target.closest('input, textarea')) {
                    return; // Allow copy in inputs
                }
                e.preventDefault();
                if (e.clipboardData) {
                    e.clipboardData.clearData();
                }
                return false;
            };
            
            const preventContextMenu = (e) => {
                if (e.target && e.target.closest && e.target.closest('input, textarea')) {
                    return; // Allow context menu in inputs
                }
                e.preventDefault();
                return false;
            };
            
            // Добавляем event listeners для предотвращения копирования
            document.addEventListener('selectstart', preventSelection, { passive: false });
            document.addEventListener('copy', preventCopy, { passive: false });
            document.addEventListener('contextmenu', preventContextMenu, { passive: false });
            
            window._telegramCopyPreventionSetup = true;
            console.log('✅ Защита от копирования установлена');
        }
        
        // CSS fallback для user-select (более надежно)
        let styleEl = document.getElementById('telegram-user-select-fix');
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = 'telegram-user-select-fix';
            document.head.appendChild(styleEl);
        }
        
        styleEl.textContent = `
            body.tg-webapp, body.tg-webapp * {
                -webkit-user-select: none !important;
                -moz-user-select: none !important;
                -ms-user-select: none !important;
                user-select: none !important;
                -webkit-touch-callout: none !important;
            }
            body.tg-webapp input,
            body.tg-webapp textarea {
                -webkit-user-select: text !important;
                -moz-user-select: text !important;
                -ms-user-select: text !important;
                user-select: text !important;
            }
        `;
        
        // Обновляем CSS переменные с данными viewport из Telegram API
        const updateViewportVariables = () => {
            const vars = {};
            if (this.webApp.viewportHeight) {
                const value = this.webApp.viewportHeight + 'px';
                document.documentElement.style.setProperty('--tg-viewport-height', value);
                vars.viewportHeight = value;
            }
            if (this.webApp.viewportStableHeight) {
                const value = this.webApp.viewportStableHeight + 'px';
                document.documentElement.style.setProperty('--tg-viewport-stable-height', value);
                vars.viewportStableHeight = value;
            }
            
            // Обновляем safe area insets если доступны
            if (this.webApp.safeAreaInsets) {
                const top = (this.webApp.safeAreaInsets.top || 0) + 'px';
                const bottom = (this.webApp.safeAreaInsets.bottom || 0) + 'px';
                const left = (this.webApp.safeAreaInsets.left || 0) + 'px';
                const right = (this.webApp.safeAreaInsets.right || 0) + 'px';
                document.documentElement.style.setProperty('--tg-safe-area-inset-top', top);
                document.documentElement.style.setProperty('--tg-safe-area-inset-bottom', bottom);
                document.documentElement.style.setProperty('--tg-safe-area-inset-left', left);
                document.documentElement.style.setProperty('--tg-safe-area-inset-right', right);
                vars.safeAreaInsets = { top, bottom, left, right };
            }
            console.log('[TG-Fix] 📐 CSS переменные обновлены:', vars);
        };
        
        updateViewportVariables();
        
        // Слушаем изменения viewport (только один раз)
        if (!window._telegramViewportListenerSetup) {
            this.webApp.onEvent('viewportChanged', () => {
                console.log('[TG-Fix] 🔄 viewportChanged событие получено');
                updateViewportVariables();
            });
            window._telegramViewportListenerSetup = true;
            console.log('[TG-Fix] 👂 Слушатель viewportChanged установлен');
        }
        
        // Проверяем примененные стили
        const wrapper = document.querySelector('.main-wrapper');
        const container = document.querySelector('.main-container');
        if (wrapper) {
            const computed = window.getComputedStyle(wrapper);
            console.log('[TG-Fix] 📦 .main-wrapper стили:', {
                width: computed.width,
                height: computed.height,
                overflowY: computed.overflowY,
                transform: computed.transform,
                position: computed.position
            });
        }
        if (container) {
            const computed = window.getComputedStyle(container);
            console.log('[TG-Fix] 📦 .main-container стили:', {
                width: computed.width,
                height: computed.height
            });
        }
        
        console.log('[TG-Fix] ✅ Telegram Web App стили применены, копирование отключено');
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


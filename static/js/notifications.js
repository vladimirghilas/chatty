/**
 * Long Polling для уведомлений
 * Отправляет запрос на api/notifications/unread-count/ и ждет ответа
 * Сервер отвечает только если есть непрочитанные уведомления
 */

(() => {
    // Variabile private pentru polling
    let isPolling = false;
    let lastNotificationCount = 0;
    const BASE_URL = '/posts/api/notifications/unread-count';

    // Selectăm elementul de notificări doar după ce DOM-ul e gata
    function getNotificationCounter() {
        return document.getElementById('notification-count');
    }

    // Start polling
    function startPolling() {
        if (isPolling) return;
        isPolling = true;
        poll();
    }

    // Funcția principală de polling
    function poll() {
        if (!isPolling) return;

        const notificationCounter = getNotificationCounter();
        if (!notificationCounter) return; // dacă elementul nu există, ieșim

        fetch(`${BASE_URL}?last_count=${lastNotificationCount}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                notificationCounter.textContent = data.unread_count;
                lastNotificationCount = data.unread_count;
            }
        })
        .catch(error => {
            console.error('Ошибка при получении уведомлений:', error);
        })
        .finally(() => {
            if (isPolling) {
                setTimeout(poll, 1000);
            }
        });
    }

    // Inițializare după ce DOM-ul e gata
    document.addEventListener('DOMContentLoaded', () => {
        const isAuthElem = document.getElementById('isAuth');
        if (isAuthElem && isAuthElem.textContent === 'True') {
            startPolling();
        }
    });
})();
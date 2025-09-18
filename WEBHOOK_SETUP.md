# 🔗 Настройка Webhook для CryptoBot

Этот документ описывает настройку webhook'ов для автоматического получения уведомлений об оплаченных счетах от CryptoBot.

## 📋 Что такое Webhook?

Webhook - это HTTP endpoint, на который CryptoBot отправляет уведомления о статусе платежей. Когда пользователь оплачивает счет, CryptoBot автоматически уведомляет ваш сервер, и подписка активируется мгновенно.

## 🚀 Запуск Webhook сервера

### Вариант 1: Бот + Webhook в одном процессе (Рекомендуется)

```bash
python run_bot_with_webhook.py
```

Этот способ запускает и Telegram бота, и HTTP сервер для webhook'ов в одном процессе.

### Вариант 2: Отдельный webhook сервер

```bash
# Запуск основного бота
python main.py

# Запуск webhook сервера отдельно
python run_webhook.py
```

## ⚙️ Настройка окружения

Добавьте в ваш `.env` файл:

```env
# Настройки Webhook
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
WEBHOOK_URL=https://your-domain.com  # Ваш внешний URL
```

### Параметры:

- **WEBHOOK_HOST**: IP адрес для привязки сервера (0.0.0.0 = все интерфейсы)
- **WEBHOOK_PORT**: Порт для HTTP сервера (по умолчанию 8000)
- **WEBHOOK_URL**: Внешний URL вашего сервера (для production)

## 🌐 Настройка внешнего доступа

### Локальная разработка (ngrok)

Для тестирования на локальной машине используйте ngrok:

```bash
# Установите ngrok
# Запустите туннель
ngrok http 8000

# Получите URL вида: https://abc123.ngrok.io
# Установите в .env:
WEBHOOK_URL=https://abc123.ngrok.io
```

### Production сервер

На production сервере настройте:

1. **Nginx/Apache** для проксирования запросов
2. **SSL сертификат** (webhook'и работают только по HTTPS)
3. **Firewall** правила для порта webhook'а

Пример конфигурации Nginx:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /webhook/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Настройка в CryptoBot

1. Откройте @CryptoBot в Telegram
2. Перейдите в **Crypto Pay** → **My Apps**
3. Выберите ваше приложение
4. В разделе **Webhooks** укажите URL:
   ```
   https://your-domain.com/webhook/cryptobot
   ```
5. Сохраните настройки

## 🧪 Тестирование Webhook

### Проверка доступности

```bash
curl -X GET http://localhost:8000/health
```

Ответ должен быть:
```json
{"status": "healthy", "timestamp": 1234567890}
```

### Тестовый webhook

```bash
curl -X POST http://localhost:8000/webhook/cryptobot \
  -H "Content-Type: application/json" \
  -d '{
    "update_type": "invoice_paid",
    "payload": {
      "invoice_id": 12345,
      "status": "paid",
      "paid_at": "2023-12-01T10:00:00Z"
    }
  }'
```

## 📊 Мониторинг

Webhook сервер логирует все события:

- ✅ Получение webhook'ов
- 🔍 Проверка подписей
- 💰 Обработка платежей
- 📱 Активация подписок
- ❌ Ошибки обработки

Логи сохраняются в `logs/clubbot.log`.

## 🔒 Безопасность

1. **Проверка подписи**: Webhook проверяет HMAC-SHA256 подпись от CryptoBot
2. **HTTPS только**: В production webhook работает только по HTTPS
3. **Валидация данных**: Все входящие данные проверяются
4. **Логирование**: Все события записываются в логи

## 🚨 Troubleshooting

### Webhook не получает уведомления

1. Проверьте доступность URL извне:
   ```bash
   curl -I https://your-domain.com/webhook/cryptobot
   ```

2. Проверьте логи сервера:
   ```bash
   tail -f logs/clubbot.log
   ```

3. Убедитесь что URL в CryptoBot настроен правильно

### Ошибки обработки платежей

1. Проверьте что платеж существует в базе данных
2. Убедитесь что пользователь найден по UUID
3. Проверьте права доступа к базе данных

### Сетевые ошибки

1. Проверьте firewall правила
2. Убедитесь что порт открыт
3. Проверьте SSL сертификат (для HTTPS)

## 📈 Производительность

- Webhook сервер асинхронный (aiohttp)
- Поддерживает множественные соединения
- Автоматическое переподключение к базе данных
- Graceful shutdown при остановке

## 🔄 Обновление

После изменения кода webhook'а:

1. Остановите сервер (Ctrl+C)
2. Обновите код
3. Перезапустите сервер
4. Проверьте логи на ошибки

---

**🎯 Результат**: После настройки webhook'а подписки будут активироваться автоматически сразу после оплаты, без необходимости ручной проверки статуса платежа.

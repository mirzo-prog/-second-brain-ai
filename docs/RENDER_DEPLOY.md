# Инструкция по развертыванию Second Brain AI на Render.com

Этот документ содержит пошаговое руководство по размещению вашего проекта на бесплатном облачном сервере **Render.com** с постоянной ссылкой вида `https://second-brain-ai.onrender.com`.

---

## Что уже подготовлено в проекте

Мы полностью сконфигурировали проект для автоматического деплоя на Render:
1. **[`Dockerfile`](../Dockerfile)**: мульти-этапная сборка (Node 20 собирает React-фронтенд, Python 3.12 запускает FastAPI, устанавливает `g++` для песочницы C++).
2. **[`render.yaml`](../render.yaml)**: манифест автоматической настройки сервиса на Render.
3. **[`scripts/render_build.sh`](../scripts/render_build.sh)** и **[`scripts/render_start.sh`](../scripts/render_start.sh)**: скрипты на случай развертывания через Python Native Environment.

---

## Пошаговый план развертывания (занимает 3 минуты)

### Шаг 1. Загрузите проект на ваш GitHub

1. Перейдите на [github.com/new](https://github.com/new) и создайте новый репозиторий (например, с именем `second-brain-ai`, можно сделать его Private или Public).
2. В терминале вашего компьютера выполните:
   ```bash
   cd ~/Projects/second-brain-ai
   git remote add origin https://github.com/ВАШ_ЛОГИН_GITHUB/second-brain-ai.git
   git branch -M main
   git push -u origin main
   ```

---

### Шаг 2. Зарегистрируйтесь / Войдите на Render.com

1. Откройте сайт [dashboard.render.com](https://dashboard.render.com/).
2. Войдите через **GitHub** (кнопка *«Sign in with GitHub»*) — это позволит Render видеть ваши репозитории в 1 клик.

---

### Шаг 3. Создайте Web Service на Render

1. В панели Render нажмите синюю кнопку **«New +»** в правом верхнем углу.
2. Выберите пункт **«Web Service»**.
3. В списке выберите ваш репозиторий `second-brain-ai` и нажмите **«Connect»**.
4. Render автоматически увидит наш `Dockerfile` и `render.yaml`.
5. Параметры:
   - **Name:** `second-brain-ai` (или любое желаемое имя, например `second-brain-mirzo`)
   - **Region:** `Frankfurt (EU)` (ближайший сервер)
   - **Instance Type:** `Free` ($0/месяц)
6. В разделе **Environment Variables** (переменные окружения):
   - Добавьте переменную `GEMINI_API_KEY` и вставьте ваш ключ Google Gemini (если есть).
7. Нажмите внизу **«Create Web Service»**.

---

### Шаг 4. Готово! Получение постоянной ссылки

Render начнет автоматическую сборку проекта. Через 2-3 минуты вверху экрана появится ваша **постоянная ссылка**:

👉 **`https://second-brain-ai-xxxx.onrender.com`**

Эта ссылка:
- Работает **24/7**, даже когда ваш домашний компьютер выключен.
- Защищена бесплатным SSL-сертификатом (**HTTPS**).
- Доступна для вас, ваших друзей и коллег с любого смартфона или ноутбука в мире.
- При каждом вашем `git push` Render будет автоматически обновлять сайт!

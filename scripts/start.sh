#!/bin/bash

echo "🚀 Запуск HeyGen Avatar Bot..."

# Проверяем, установлены ли зависимости
if [ ! -d "node_modules" ]; then
    echo "📦 Устанавливаем зависимости..."
    npm install
fi

# Проверяем, существует ли .env файл
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаем из примера..."
    cp .env.example .env
    echo "✏️  Пожалуйста, отредактируйте файл .env и добавьте ваши API ключи"
    exit 1
fi

# Запускаем сервер
echo "🎭 Запускаем сервер на порту 3000..."
npm start
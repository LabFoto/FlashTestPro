.PHONY: help install test lint format clean build build-all

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help:
	@echo "Доступные команды:"
	@echo "  $(GREEN)install$(NC)    - Установить зависимости"
	@echo "  $(GREEN)test$(NC)       - Запустить все тесты"
	@echo "  $(GREEN)test-unit$(NC)  - Запустить unit-тесты"
	@echo "  $(GREEN)test-int$(NC)   - Запустить интеграционные тесты"
	@echo "  $(GREEN)lint$(NC)       - Проверить код линтерами"
	@echo "  $(GREEN)format$(NC)     - Форматировать код"
	@echo "  $(GREEN)coverage$(NC)   - Запустить тесты с покрытием"
	@echo "  $(GREEN)clean$(NC)      - Очистить временные файлы"
	@echo "  $(GREEN)build$(NC)      - Собрать для текущей ОС"
	@echo "  $(GREEN)build-all$(NC)  - Собрать все скрипты сборки"

install:
	@echo "$(YELLOW)Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	pip install pytest pytest-cov coverage flake8 black

test:
	@echo "$(YELLOW)Запуск всех тестов...$(NC)"
	python -m pytest -v --tb=short

test-unit:
	@echo "$(YELLOW)Запуск unit-тестов...$(NC)"
	python -m pytest test_main.py -v --tb=short

test-int:
	@echo "$(YELLOW)Запуск интеграционных тестов...$(NC)"
	python -m pytest test_integration.py -v --tb=short

lint:
	@echo "$(YELLOW)Проверка кода линтерами...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	black .

coverage:
	@echo "$(YELLOW)Запуск тестов с покрытием...$(NC)"
	python -m pytest --cov=. --cov-report=html --cov-report=term-missing

clean:
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov/ || true
	rm -rf sd-card-tester-pro/ || true
	rm -rf Dist/ || true

build:
	@echo "$(YELLOW)Сборка для текущей ОС...$(NC)"
	@if [ "$$(uname -s)" = "Linux" ]; then \
		chmod +x build_linux.sh; \
		./build_linux.sh; \
	elif [ "$$(uname -s)" = "Darwin" ]; then \
		chmod +x build_macos.sh; \
		./build_macos.sh; \
	else \
		./build_windows.bat; \
	fi

build-all:
	@echo "$(YELLOW)Создание всех скриптов сборки...$(NC)"
	@echo "Скрипты сборки созданы:"
	@echo "  - build_windows.bat"
	@echo "  - build_linux.sh"
	@echo "  - build_macos.sh"
	@echo "  - build_all.py"
	@echo ""
	@echo "Для сборки используйте:"
	@echo "  Windows: ./build_windows.bat"
	@echo "  Linux:   ./build_linux.sh"
	@echo "  macOS:   ./build_macos.sh"
	@echo "  Любая:   python build_all.py"

all: install lint test build
	@echo "$(GREEN)✅ Все задачи выполнены успешно!$(NC)"

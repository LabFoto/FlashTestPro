# locales.py
"""
Локализация для SD Card Tester Pro
"""

# Словари локализации
TRANSLATIONS = {
    "ru": {
        # Основные элементы интерфейса
        "app_title": "SD Card Tester Pro",
        "main_title": "🔧 SD CARD TESTER PRO",
        "subtitle": "Профессиональное тестирование накопителей",

        # Фреймы
        "drive_selection": "ВЫБОР НАКОПИТЕЛЯ",
        "test_settings": "НАСТРОЙКИ ТЕСТА",
        "progress": "ПРОГРЕСС ТЕСТА",

        # Кнопки
        "refresh_list": "🔄 Обновить список",
        "start_test": "🚀 НАЧАТЬ",
        "pause": "⏸ ПАУЗА",
        "resume": "▶ ПРОДОЛЖИТЬ",
        "stop": "⏹ ОСТАНОВИТЬ",
        "rename": "✏️ Переименовать диск",

        # Надписи
        "select_drive": "Выберите накопитель для тестирования",
        "system_drive_warning": "⚠️  ВНИМАНИЕ: Выбран СИСТЕМНЫЙ диск! Тестирование запрещено!",
        "selected_drive": "Выбран диск: {} (тип: {}, размер: {}, ФС: {})",
        "waiting": "Ожидание начала теста...",
        "remaining": "Осталось: {}",
        "time_remaining": "Осталось: --:--:--",

        # Настройки теста
        "passes_label": "Количество проходов:",
        "fast_pass": "Быстрый (1 проход)",
        "standard_pass": "Стандартный (3 прохода)",
        "full_pass": "Полный (7 проходов)",
        "or_label": "или:",
        "passes_suffix": "проходов",

        # Типы тестов - ВСЕ ГАЛОЧКИ СНЯТЫ ПО УМОЛЧАНИЮ
        "test_ones": "Запись единиц (0xFF)",
        "test_zeros": "Запись нулей (0x00)",
        "test_random": "Случайные данные",
        "test_verify": "Проверка после записи",
        "format_after": "Форматировать после теста",

        # Вкладки
        "tab_speed": "📈 ГРАФИК СКОРОСТИ",
        "tab_stats": "📊 СТАТИСТИКА",
        "tab_log": "📝 ЛОГ СОБЫТИЙ",
        "tab_info": "ℹ️ ИНФОРМАЦИЯ",

        # График
        "chart_title": "График скорости записи",
        "chart_xlabel": "Время (сек)",
        "chart_ylabel": "Скорость (MB/s)",
        "chart_avg": "Средняя: {:.1f} MB/s",
        "chart_max": "Макс: {:.1f} MB/s",

        # Меню
        "menu_file": "Файл",
        "menu_view": "Вид",
        "menu_test": "Тестирование",
        "menu_help": "Справка",

        "menu_save_log": "Сохранить лог...",
        "menu_export": "Экспорт отчета...",
        "menu_settings": "Настройки...",
        "menu_exit": "Выход",

        "menu_refresh": "Обновить список дисков",
        "menu_clear_log": "Очистить лог",
        "menu_reset_stats": "Сбросить статистику",

        "menu_fast_test": "Быстрый тест (1 проход)",
        "menu_standard_test": "Стандартный тест (3 прохода)",
        "menu_full_test": "Полный тест (7 проходов)",
        "menu_start_test": "Начать тест",
        "menu_pause_test": "Приостановить тест",
        "menu_stop_test": "Остановить тест",

        "menu_docs": "Документация",
        "menu_about": "О программе",
        "menu_updates": "Проверить обновления",

        "documentation": "Документация",
        "check_updates": "Проверить обновления",

        # СТАТИСТИКА
        "statistics": "📊 СТАТИСТИКА",
        "stats_total_size": "Общий размер:",
        "stats_tested": "Протестировано:",
        "stats_speed_avg": "Средняя скорость:",
        "stats_speed_max": "Макс. скорость:",
        "stats_speed_min": "Мин. скорость:",
        "stats_time_total": "Время теста:",
        "stats_bad_sectors": "Битых секторов:",
        "stats_passes_complete": "Проходов завершено:",
        "stats_passes_remaining": "Осталось проходов:",
        "stats_status": "Статус:",

        # ИНФОРМАЦИЯ О СИСТЕМЕ
        "system_info": "💻 ИНФОРМАЦИЯ О СИСТЕМЕ",
        "system_os": "ОС:",
        "system_python": "Версия Python:",
        "system_architecture": "Архитектура:",
        "system_processor": "Процессор:",
        "system_memory": "Память:",
        "system_disks": "Дисков:",
        "system_uptime": "Время работы:",
        "system_hostname": "Имя компьютера:",

        # О ПРОГРАММЕ
        "about_program": "ℹ️ О ПРОГРАММЕ",
        "program_version": "Версия:",
        "program_author": "Автор:",
        "program_license": "Лицензия:",
        "program_github": "GitHub:",
        "program_build": "Дата сборки:",

        # КНОПКИ ИНФОРМАЦИИ
        "btn_documentation": "📖 Открыть документацию",
        "btn_check_updates": "🔄 Проверить обновления",
        "btn_report_bug": "🐛 Сообщить об ошибке",
        "btn_error_log": "📋 Журнал ошибок",

        # Переименование диска
        "rename_drive_title": "Переименовать диск",
        "current_label": "Текущая метка",
        "new_name": "Новое имя",
        "enter_drive_name": "Введите имя диска!",
        "name_too_long": "Имя не должно превышать 11 символов!",
        "drive_renamed": "Диск переименован в",
        "drive": "Диск",
        "cancel": "Отмена",
        "success": "Успех",
        "warning": "Предупреждение",
        "error": "Ошибка",

        # Сообщения
        "test_complete": "Тестирование завершено",
        "test_paused": "Тест приостановлен",
        "test_resumed": "Тест продолжен",
        "test_stopped": "Тест остановлен",
        "log_cleared": "Лог очищен",
        "stats_reset": "Статистика сброшена",
        "log_copied": "Лог скопирован в буфер обмена",
        "log_saved": "Лог сохранен: {}",
        "report_saved": "Отчет экспортирован: {}",

        # Ошибки
        "error_no_drive": "Выберите диск для тестирования!",
        "error_system_drive": "Тестирование системных дисков запрещено!\nВыберите съемный носитель.",
        "error_invalid_passes": "Некорректное количество проходов. Введите число от 1 до 100.",
        "error_no_test_type": "Выберите хотя бы один тип теста!",

        # Диалоги
        "confirm_title": "ПОДТВЕРЖДЕНИЕ УНИЧТОЖЕНИЯ ДАННЫХ",
        "confirm_stop": "Прервать тестирование?\nТекущий проход будет завершен.",
        "confirm_exit": "Подтверждение",

        # Предупреждения
        "warning_admin": "⚠️  Предупреждение:\nДля полного доступа к устройствам рекомендуется запустить программу от имени администратора/root.\nНекоторые функции могут быть недоступны.",

        # Информация о программе
        "about_title": "SD Card Tester Pro",
        "about_text": """SD Card Tester Pro

Профессиональный инструмент для тестирования 
карт памяти и других накопителей.

Автор: Shum
Лицензия: MIT

ОС: {} {}
Python: {}

© 2024 Все права защищены.""",

        # Язык
        "language": "Язык / Language / 语言:",
        "type": "Тип",
        "size": "Размер",
        "filesystem": "ФС",
        "clear_log": "Очистить лог",
        "reset_stats": "Сбросить статистику",
    },

    "en": {
        # Основные элементы интерфейса
        "app_title": "SD Card Tester Pro",
        "main_title": "🔧 SD CARD TESTER PRO",
        "subtitle": "Professional Storage Testing",

        # Фреймы
        "drive_selection": "DRIVE SELECTION",
        "test_settings": "TEST SETTINGS",
        "progress": "TEST PROGRESS",

        # Кнопки
        "refresh_list": "🔄 Refresh List",
        "start_test": "🚀 START",
        "pause": "⏸ PAUSE",
        "resume": "▶ RESUME",
        "stop": "⏹ STOP",
        "rename": "✏️ Rename Drive",

        # Надписи
        "select_drive": "Select a drive for testing",
        "system_drive_warning": "⚠️  WARNING: SYSTEM drive selected! Testing is forbidden!",
        "selected_drive": "Selected drive: {} (type: {}, size: {}, FS: {})",
        "waiting": "Waiting for test to start...",
        "remaining": "Remaining: {}",
        "time_remaining": "Remaining: --:--:--",

        # Настройки теста
        "passes_label": "Number of passes:",
        "fast_pass": "Fast (1 pass)",
        "standard_pass": "Standard (3 passes)",
        "full_pass": "Full (7 passes)",
        "or_label": "or:",
        "passes_suffix": "passes",

        # Типы тестов - ALL CHECKBOXES UNCHECKED BY DEFAULT
        "test_ones": "Write ones (0xFF)",
        "test_zeros": "Write zeros (0x00)",
        "test_random": "Random data",
        "test_verify": "Read after write verification",
        "format_after": "Format after test",

        # Вкладки
        "tab_speed": "📈 SPEED CHART",
        "tab_stats": "📊 STATISTICS",
        "tab_log": "📝 EVENT LOG",
        "tab_info": "ℹ️ INFORMATION",

        # График
        "chart_title": "Write Speed Chart",
        "chart_xlabel": "Time (sec)",
        "chart_ylabel": "Speed (MB/s)",
        "chart_avg": "Average: {:.1f} MB/s",
        "chart_max": "Max: {:.1f} MB/s",

        # Меню
        "menu_file": "File",
        "menu_view": "View",
        "menu_test": "Testing",
        "menu_help": "Help",

        "menu_save_log": "Save Log...",
        "menu_export": "Export Report...",
        "menu_settings": "Settings...",
        "menu_exit": "Exit",

        "menu_refresh": "Refresh Drive List",
        "menu_clear_log": "Clear Log",
        "menu_reset_stats": "Reset Statistics",

        "menu_fast_test": "Quick Test (1 pass)",
        "menu_standard_test": "Standard Test (3 passes)",
        "menu_full_test": "Full Test (7 passes)",
        "menu_start_test": "Start Test",
        "menu_pause_test": "Pause Test",
        "menu_stop_test": "Stop Test",

        "menu_docs": "Documentation",
        "menu_about": "About",
        "menu_updates": "Check for Updates",

        "documentation": "Documentation",
        "check_updates": "Check for Updates",

        # STATISTICS
        "statistics": "📊 STATISTICS",
        "stats_total_size": "Total size:",
        "stats_tested": "Tested:",
        "stats_speed_avg": "Average speed:",
        "stats_speed_max": "Max speed:",
        "stats_speed_min": "Min speed:",
        "stats_time_total": "Test time:",
        "stats_bad_sectors": "Bad sectors:",
        "stats_passes_complete": "Passes completed:",
        "stats_passes_remaining": "Passes remaining:",
        "stats_status": "Status:",

        "system_info": "💻 SYSTEM INFORMATION",
        "system_os": "OS:",
        "system_python": "Python version:",
        "system_architecture": "Architecture:",
        "system_processor": "Processor:",
        "system_memory": "Memory:",
        "system_disks": "Disks:",
        "system_uptime": "Uptime:",
        "system_hostname": "Hostname:",

        "about_program": "ℹ️ ABOUT PROGRAM",
        "program_version": "Version:",
        "program_author": "Author:",
        "program_license": "License:",
        "program_github": "GitHub:",
        "program_build": "Build date:",

        "btn_documentation": "📖 Open Documentation",
        "btn_check_updates": "🔄 Check Updates",
        "btn_report_bug": "🐛 Report Bug",
        "btn_error_log": "📋 Error Log",

        # Rename drive
        "rename_drive_title": "Rename Drive",
        "current_label": "Current label",
        "new_name": "New name",
        "enter_drive_name": "Enter drive name!",
        "name_too_long": "Name must not exceed 11 characters!",
        "drive_renamed": "Drive renamed to",
        "drive": "Drive",
        "cancel": "Cancel",
        "success": "Success",
        "warning": "Warning",
        "error": "Error",

        # Сообщения
        "test_complete": "Testing completed",
        "test_paused": "Test paused",
        "test_resumed": "Test resumed",
        "test_stopped": "Test stopped",
        "log_cleared": "Log cleared",
        "stats_reset": "Statistics reset",
        "log_copied": "Log copied to clipboard",
        "log_saved": "Log saved: {}",
        "report_saved": "Report exported: {}",

        # Ошибки
        "error_no_drive": "Select a drive for testing!",
        "error_system_drive": "Testing system drives is forbidden!\nSelect a removable drive.",
        "error_invalid_passes": "Invalid number of passes. Enter a number from 1 to 100.",
        "error_no_test_type": "Select at least one test type!",

        # Диалоги
        "confirm_title": "CONFIRM DATA DESTRUCTION",
        "confirm_stop": "Interrupt testing?\nCurrent pass will be completed.",
        "confirm_exit": "Confirmation",

        # Предупреждения
        "warning_admin": "⚠️  Warning:\nFor full device access, it is recommended to run the program as administrator/root.\nSome features may be unavailable.",

        # Информация о программе
        "about_title": "SD Card Tester Pro",
        "about_text": """SD Card Tester Pro

Professional tool for testing 
memory cards and other storage devices.

Author: SD Card Tester Team
License: MIT

OS: {} {}
Python: {}

© 2024 All rights reserved.""",

        # Language
        "language": "Language / Язык / 语言:",
        "type": "Type",
        "size": "Size",
        "filesystem": "FS",
        "clear_log": "Clear Log",
        "reset_stats": "Reset Statistics",

    },

    "zh": {
        # Основные элементы интерфейса
        "app_title": "SD卡测试专业版",
        "main_title": "🔧 SD卡测试专业版",
        "subtitle": "专业存储设备测试",

        # Фреймы
        "drive_selection": "选择驱动器",
        "test_settings": "测试设置",
        "progress": "测试进度",

        # Кнопки
        "refresh_list": "🔄 刷新列表",
        "start_test": "🚀 开始",
        "pause": "⏸ 暂停",
        "resume": "▶ 继续",
        "stop": "⏹ 停止",
        "rename": "✏️ 重命名驱动器",

        # Надписи
        "select_drive": "选择要测试的驱动器",
        "system_drive_warning": "⚠️ 警告：选择了系统驱动器！禁止测试！",
        "selected_drive": "已选择驱动器：{} (类型：{}，大小：{}，文件系统：{})",
        "waiting": "等待测试开始...",
        "remaining": "剩余时间：{}",
        "time_remaining": "剩余时间：--:--:--",

        # Настройки теста
        "passes_label": "测试次数：",
        "fast_pass": "快速 (1次)",
        "standard_pass": "标准 (3次)",
        "full_pass": "完整 (7次)",
        "or_label": "或：",
        "passes_suffix": "次",

        # Типы тестов - 默认所有复选框均为未选中
        "test_ones": "写入1 (0xFF)",
        "test_zeros": "写入0 (0x00)",
        "test_random": "随机数据",
        "test_verify": "写入后验证",
        "format_after": "测试后格式化",

        # Вкладки
        "tab_speed": "📈 速度图表",
        "tab_stats": "📊 统计信息",
        "tab_log": "📝 事件日志",
        "tab_info": "ℹ️ 信息",

        # График
        "chart_title": "写入速度图表",
        "chart_xlabel": "时间 (秒)",
        "chart_ylabel": "速度 (MB/秒)",
        "chart_avg": "平均：{:.1f} MB/秒",
        "chart_max": "最大：{:.1f} MB/秒",

        # Меню
        "menu_file": "文件",
        "menu_view": "视图",
        "menu_test": "测试",
        "menu_help": "帮助",

        "menu_save_log": "保存日志...",
        "menu_export": "导出报告...",
        "menu_settings": "设置...",
        "menu_exit": "退出",

        "menu_refresh": "刷新驱动器列表",
        "menu_clear_log": "清除日志",
        "menu_reset_stats": "重置统计",

        "menu_fast_test": "快速测试 (1次)",
        "menu_standard_test": "标准测试 (3次)",
        "menu_full_test": "完整测试 (7次)",
        "menu_start_test": "开始测试",
        "menu_pause_test": "暂停测试",
        "menu_stop_test": "停止测试",

        "menu_docs": "文档",
        "menu_about": "关于",
        "menu_updates": "检查更新",

        "documentation": "文档",
        "check_updates": "检查更新",

        # 统计信息
        "statistics": "📊 统计信息",
        "stats_total_size": "总容量:",
        "stats_tested": "已测试:",
        "stats_speed_avg": "平均速度:",
        "stats_speed_max": "最大速度:",
        "stats_speed_min": "最小速度:",
        "stats_time_total": "测试时间:",
        "stats_bad_sectors": "坏扇区:",
        "stats_passes_complete": "已完成轮次:",
        "stats_passes_remaining": "剩余轮次:",
        "stats_status": "状态:",

        "system_info": "💻 系统信息",
        "system_os": "操作系统:",
        "system_python": "Python版本:",
        "system_architecture": "架构:",
        "system_processor": "处理器:",
        "system_memory": "内存:",
        "system_disks": "磁盘:",
        "system_uptime": "运行时间:",
        "system_hostname": "主机名:",

        "about_program": "ℹ️ 关于程序",
        "program_version": "版本:",
        "program_author": "作者:",
        "program_license": "许可证:",
        "program_github": "GitHub:",
        "program_build": "构建日期:",

        "btn_documentation": "📖 打开文档",
        "btn_check_updates": "🔄 检查更新",
        "btn_report_bug": "🐛 报告错误",
        "btn_error_log": "📋 错误日志",

        # 重命名驱动器
        "rename_drive_title": "重命名驱动器",
        "current_label": "当前卷标",
        "new_name": "新名称",
        "enter_drive_name": "请输入驱动器名称！",
        "name_too_long": "名称不能超过11个字符！",
        "drive_renamed": "驱动器重命名为",
        "drive": "驱动器",
        "cancel": "取消",
        "success": "成功",
        "warning": "警告",
        "error": "错误",

        # Сообщения
        "test_complete": "测试完成",
        "test_paused": "测试已暂停",
        "test_resumed": "测试已继续",
        "test_stopped": "测试已停止",
        "log_cleared": "日志已清除",
        "stats_reset": "统计已重置",
        "log_copied": "日志已复制到剪贴板",
        "log_saved": "日志已保存：{}",
        "report_saved": "报告已导出：{}",

        # Ошибки
        "error_no_drive": "请选择要测试的驱动器！",
        "error_system_drive": "禁止测试系统驱动器！\n请选择可移动驱动器。",
        "error_invalid_passes": "测试次数无效。请输入1到100之间的数字。",
        "error_no_test_type": "请至少选择一种测试类型！",

        # Диалоги
        "confirm_title": "确认数据销毁",
        "confirm_stop": "中断测试？\n当前测试周期将完成。",
        "confirm_exit": "确认",

        # Предупреждения
        "warning_admin": "⚠️ 警告：\n建议以管理员/root身份运行程序以获得完整的设备访问权限。\n某些功能可能不可用。",

        # Информация о программе
        "about_title": "SD卡测试专业版",
        "about_text": """SD卡测试专业版

专业的内存卡和其他存储设备测试工具。

作者：SD卡测试团队
许可证：MIT

操作系统：{} {}
Python：{}

© 2024 保留所有权利。""",

        # 语言
        "language": "语言 / Language / Язык:",
        "type": "类型",
        "size": "大小",
        "filesystem": "文件系统",
        "clear_log": "清除日志",
        "reset_stats": "重置统计",
    }
}

def get_translation(lang, key, *args):
    """
    Получить перевод по ключу

    Args:
        lang: язык ('ru', 'en', 'zh')
        key: ключ перевода
        *args: аргументы для форматирования

    Returns:
        Переведенная строка или оригинальный ключ, если перевод не найден
    """
    if lang not in TRANSLATIONS:
        lang = 'ru'  # По умолчанию русский

    if key in TRANSLATIONS[lang]:
        if args:
            return TRANSLATIONS[lang][key].format(*args)
        return TRANSLATIONS[lang][key]

    # Если перевод не найден, возвращаем ключ
    return key

def get_available_languages():
    """Получить список доступных языков"""
    return list(TRANSLATIONS.keys())
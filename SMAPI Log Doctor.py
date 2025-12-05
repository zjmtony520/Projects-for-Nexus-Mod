import re
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass, field
from typing import List, Optional


# =========================
# Translation dictionary
# =========================

TEXT = {
    "en": {
        # window
        "app_title": "SMAPI Log Doctor",
        "btn_open": "Open SMAPI Log",
        "btn_export": "Export Summary",
        "status_ready": "Ready. Open a SMAPI log to analyze.",
        "status_loaded": "Loaded log: {path}",
        "status_no_analysis": "No analysis yet. Open a log first.",
        "status_export_ok": "Summary exported to {path}",
        "status_export_fail": "Failed to export summary: {error}",
        "label_language": "Language:",
        "dialog_select_log_title": "Select SMAPI log",
        "dialog_export_title": "Export summary",
        "dialog_error_title": "Error",
        "dialog_info_title": "Info",
        "dialog_read_fail": "Failed to read file:\n{error}",
        "dialog_analyze_fail": "Failed to analyze log:\n{error}",
        "filetype_text": "Text files",
        "filetype_all": "All files",

        # tabs
        "tab_overview": "Overview",
        "tab_mod_health": "Mod Health",
        "tab_errors": "Errors",
        "tab_warnings": "Warnings",
        "tab_suggestions": "Suggestions",
        "tab_raw": "Raw Log",

        # overview
        "overview_title": "Stardew Valley / SMAPI Overview",
        "overview_game_version": "Game version",
        "overview_smapi_version": "SMAPI version",
        "overview_unknown": "Unknown",
        "overview_summary": "Summary",
        "overview_mod_count": "Mods loaded: {count}",
        "overview_content_pack_count": "Content packs loaded: {count}",
        "overview_error_count": "Errors: {count}",
        "overview_warning_count": "Warnings: {count}",
        "overview_slow_start": "Startup time: {seconds:.1f}s",
        "overview_hint": "Tip: fix errors first, then warnings, then consistency / cosmetic issues.",

        # mod health
        "mod_health_title": "Mod Health & Risk",
        "mod_health_patched_header": "Mods patching game code (higher risk):",
        "mod_health_save_header": "Mods changing save serializer (do NOT remove mid-playthrough):",
        "mod_health_console_header": "Mods with direct console access:",
        "mod_health_missing_dep_header": "Mods with missing dependencies:",
        "mod_health_missing_dep_item": "{mod} → missing: {missing}",
        "mod_health_none": "No risky mods detected in this log.",
        "mod_health_updates_header": "Mods with updates available:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Errors found in this log",
        "errors_none": "No SMAPI errors detected. 🎉",
        "errors_intro": "These are the most important issues reported by SMAPI:",

        # warnings
        "warnings_header": "Warnings",
        "warnings_none": "No warnings found.",
        "warnings_intro": "These may not break your game immediately, but are worth checking:",

        # suggestions
        "suggestions_header": "Suggested fixes",
        "suggestions_none": "No automatic suggestions. If the game still misbehaves, check Errors/Warn tabs.",

        # raw
        "raw_header": "Full SMAPI Log",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server detected. It can cause crashes with SMAPI; add an exception or disable it.",

        # suggestion types
        "sg.skipped_mod": "Fix mod \"{name}\": SMAPI skipped it ({reason}). Open its folder and ensure it has a valid manifest.json and is for your game/SMAPI version.",
        "sg.failed_mod": "Fix mod \"{name}\": SMAPI failed to load it ({reason}). Check the install instructions on its Nexus/Mod page.",
        "sg.missing_dep": "Install required dependency \"{missing}\" for \"{mod}\", or disable the dependent mod if you don't need it.",
        "sg.save_serializer": "\"{mod}\" changes the save serializer. Back up your saves and avoid removing this mod mid-playthrough.",
        "sg.patched_mods_many": "You have many mods patching game code ({count}). If you see weird crashes, try disabling utility/FX mods one by one.",
        "sg.rivatuner": "RivaTuner Statistics Server may conflict with SMAPI. Add an exception for Stardew Valley or close it while playing.",
        "sg.updates": "You can update {count} mods. Keeping frameworks and core mods updated often fixes crashes and invisible issues.",
        "sg.slow_start": "Game startup took about {seconds:.1f}s. Large content packs and many patching mods can increase load time; consider trimming heavy mods if this bothers you.",
    },
    "zh": {
        # window
        "app_title": "SMAPI 日志小医生",
        "btn_open": "打开 SMAPI 日志",
        "btn_export": "导出概览报告",
        "status_ready": "就绪。先打开一份 SMAPI 日志再分析。",
        "status_loaded": "已加载日志：{path}",
        "status_no_analysis": "还没有分析结果，请先打开一份日志。",
        "status_export_ok": "已导出总结到 {path}",
        "status_export_fail": "导出总结失败：{error}",
        "label_language": "语言：",
        "dialog_select_log_title": "选择 SMAPI 日志",
        "dialog_export_title": "导出概览",
        "dialog_error_title": "错误",
        "dialog_info_title": "提示",
        "dialog_read_fail": "读取文件失败：\n{error}",
        "dialog_analyze_fail": "分析日志失败：\n{error}",
        "filetype_text": "文本文件",
        "filetype_all": "所有文件",

        # tabs
        "tab_overview": "概览",
        "tab_mod_health": "模组健康",
        "tab_errors": "错误",
        "tab_warnings": "警告",
        "tab_suggestions": "解决方案",
        "tab_raw": "原始日志",

        # overview
        "overview_title": "星露谷 / SMAPI 概览",
        "overview_game_version": "游戏版本",
        "overview_smapi_version": "SMAPI 版本",
        "overview_unknown": "未知",
        "overview_summary": "总结",
        "overview_mod_count": "已加载模组数量：{count}",
        "overview_content_pack_count": "已加载内容包数量：{count}",
        "overview_error_count": "错误数：{count}",
        "overview_warning_count": "警告数：{count}",
        "overview_slow_start": "启动耗时：{seconds:.1f} 秒",
        "overview_hint": "小提示：先解决“错误”，再看“警告”，最后再收拾体验/外观类问题。",

        # mod health
        "mod_health_title": "模组健康与风险",
        "mod_health_patched_header": "直接修改游戏代码的模组（风险较高）：",
        "mod_health_save_header": "改变存档序列化的模组（请勿中途移除）：",
        "mod_health_console_header": "直接读写控制台的模组：",
        "mod_health_missing_dep_header": "缺少前置依赖的模组：",
        "mod_health_missing_dep_item": "{mod} → 缺少：{missing}",
        "mod_health_none": "本次日志中没有检测到明显高风险模组。",
        "mod_health_updates_header": "有可用更新的模组：",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "本日志中发现的错误",
        "errors_none": "未检测到 SMAPI 错误。🎉",
        "errors_intro": "下面是 SMAPI 报告的关键问题：",

        # warnings
        "warnings_header": "警告",
        "warnings_none": "未发现警告。",
        "warnings_intro": "这些问题不一定马上导致崩溃，但建议检查：",

        # suggestions
        "suggestions_header": "推荐解决方案",
        "suggestions_none": "暂时没有自动建议。如果游戏仍有问题，请优先查看“错误”和“警告”标签页。",

        # raw
        "raw_header": "完整 SMAPI 日志",

        # generic issues
        "warn_rivatuner": "检测到 RivaTuner Statistics Server，它可能与 SMAPI 冲突，建议为星露谷添加例外或在游玩时关闭。",

        # suggestion types
        "sg.skipped_mod": "修复模组“{name}”：该模组被 SMAPI 跳过（原因：{reason}）。请检查模组文件夹中是否有有效的 manifest.json，并确认模组版本支持当前游戏/SMAPI 版本。",
        "sg.failed_mod": "修复模组“{name}”：SMAPI 无法加载它（原因：{reason}）。请前往模组页面查看安装说明，必要时重新安装。",
        "sg.missing_dep": "为“{mod}”安装必需的前置模组“{missing}”，如果不需要该模组，也可以直接禁用它。",
        "sg.save_serializer": "“{mod}”更改了存档写入方式。请务必先备份存档，且不要在存档周目中途移除该模组。",
        "sg.patched_mods_many": "你当前有较多模组在修改游戏底层代码（共 {count} 个）。如果遇到奇怪的报错或崩溃，可以优先尝试禁用部分工具/特效类模组进行排查。",
        "sg.rivatuner": "RivaTuner Statistics Server 可能与 SMAPI 冲突。建议为星露谷添加例外或在游玩时暂时关闭该软件。",
        "sg.updates": "有 {count} 个模组可以更新。优先更新框架/核心模组，通常可以修复崩溃和一些看不见的兼容问题。",
        "sg.slow_start": "本次游戏启动大约耗时 {seconds:.1f} 秒。大量内容包和修改底层代码的模组会拉长加载时间，如有需要可以考虑精简大型模组。",
    },
    "ru": {
        # window
        "app_title": "Доктор логов SMAPI",
        "btn_open": "Открыть лог SMAPI",
        "btn_export": "Экспортировать сводку",
        "status_ready": "Готово. Сначала откройте лог SMAPI для анализа.",
        "status_loaded": "Лог загружен: {path}",
        "status_no_analysis": "Анализа ещё нет. Сначала откройте лог.",
        "status_export_ok": "Сводка сохранена в {path}",
        "status_export_fail": "Не удалось экспортировать сводку: {error}",
        "label_language": "Язык:",
        "dialog_select_log_title": "Выберите лог SMAPI",
        "dialog_export_title": "Экспорт сводки",
        "dialog_error_title": "Ошибка",
        "dialog_info_title": "Информация",
        "dialog_read_fail": "Не удалось прочитать файл:\n{error}",
        "dialog_analyze_fail": "Не удалось проанализировать лог:\n{error}",
        "filetype_text": "Текстовые файлы",
        "filetype_all": "Все файлы",

        # tabs
        "tab_overview": "Обзор",
        "tab_mod_health": "Состояние модов",
        "tab_errors": "Ошибки",
        "tab_warnings": "Предупреждения",
        "tab_suggestions": "Решения",
        "tab_raw": "Исходный лог",

        # overview
        "overview_title": "Обзор Stardew Valley / SMAPI",
        "overview_game_version": "Версия игры",
        "overview_smapi_version": "Версия SMAPI",
        "overview_unknown": "Неизвестно",
        "overview_summary": "Краткая сводка",
        "overview_mod_count": "Загружено модов: {count}",
        "overview_content_pack_count": "Загружено контент-паков: {count}",
        "overview_error_count": "Ошибок: {count}",
        "overview_warning_count": "Предупреждений: {count}",
        "overview_slow_start": "Время запуска: {seconds:.1f} с",
        "overview_hint": "Подсказка: сначала исправляйте ошибки, потом предупреждения, а уже затем косметику и оптимизацию.",

        # mod health
        "mod_health_title": "Состояние и риск модов",
        "mod_health_patched_header": "Моды, патчащие игровой код (повышенный риск):",
        "mod_health_save_header": "Моды, изменяющие сериализацию сохранений (нельзя удалять в середине прохождения):",
        "mod_health_console_header": "Моды с прямым доступом к консоли:",
        "mod_health_missing_dep_header": "Моды с отсутствующими зависимостями:",
        "mod_health_missing_dep_item": "{mod} → отсутствует: {missing}",
        "mod_health_none": "В этом логе не обнаружено явно рискованных модов.",
        "mod_health_updates_header": "Моды с доступными обновлениями:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Ошибки в этом логе",
        "errors_none": "Ошибок SMAPI не найдено. 🎉",
        "errors_intro": "Это наиболее важные проблемы, о которых сообщает SMAPI:",

        # warnings
        "warnings_header": "Предупреждения",
        "warnings_none": "Предупреждений не найдено.",
        "warnings_intro": "Они не всегда ломают игру сразу, но на них стоит взглянуть:",

        # suggestions
        "suggestions_header": "Рекомендуемые действия",
        "suggestions_none": "Автоматических рекомендаций нет. Если игра по-прежнему ведёт себя странно, загляните на вкладки «Ошибки» и «Предупреждения».",

        # raw
        "raw_header": "Полный лог SMAPI",

        # generic issues
        "warn_rivatuner": "Обнаружен RivaTuner Statistics Server. Он может вызывать вылеты с SMAPI; добавьте исключение или отключите его.",

        # suggestion types
        "sg.skipped_mod": "Исправьте мод {name}: SMAPI пропустил его (причина: {reason}). Откройте его папку и проверьте manifest.json и совместимость с вашей версией игры/SMAPI.",
        "sg.failed_mod": "Исправьте мод {name}: SMAPI не смог его загрузить (причина: {reason}). Проверьте инструкцию по установке на странице мода и при необходимости переустановите.",
        "sg.missing_dep": "Установите обязательную зависимость {missing} для мода {mod}, либо отключите этот мод, если он вам не нужен.",
        "sg.save_serializer": "{mod} изменяет способ сохранения. Обязательно сделайте резервную копию сейвов и не удаляйте этот мод посреди прохождения.",
        "sg.patched_mods_many": "У вас много модов, патчащих игровой код ({count}). Если видите странные вылеты, попробуйте временно отключать утилиты/FX-моды по одному.",
        "sg.rivatuner": "RivaTuner Statistics Server может конфликтовать с SMAPI. Добавьте для Stardew Valley исключение или закройте программу во время игры.",
        "sg.updates": "Доступны обновления для {count} мод(ов). Обновление фреймворков и базовых модов часто устраняет вылеты и скрытые проблемы.",
        "sg.slow_start": "Запуск игры занял около {seconds:.1f} с. Большие контент-паки и множество «тяжёлых» модов увеличивают время загрузки; при желании можно немного почистить сборку.",
    },
    "pt": {
        # window
        "app_title": "Doutor de Logs do SMAPI",
        "btn_open": "Abrir log do SMAPI",
        "btn_export": "Exportar resumo",
        "status_ready": "Pronto. Abra um log do SMAPI para analisar.",
        "status_loaded": "Log carregado: {path}",
        "status_no_analysis": "Ainda não há análise. Abra um log primeiro.",
        "status_export_ok": "Resumo exportado para {path}",
        "status_export_fail": "Falha ao exportar resumo: {error}",
        "label_language": "Idioma:",
        "dialog_select_log_title": "Selecionar log do SMAPI",
        "dialog_export_title": "Exportar resumo",
        "dialog_error_title": "Erro",
        "dialog_info_title": "Info",
        "dialog_read_fail": "Falha ao ler o arquivo:\n{error}",
        "dialog_analyze_fail": "Falha ao analisar o log:\n{error}",
        "filetype_text": "Arquivos de texto",
        "filetype_all": "Todos os arquivos",

        # tabs
        "tab_overview": "Visão geral",
        "tab_mod_health": "Saúde dos mods",
        "tab_errors": "Erros",
        "tab_warnings": "Avisos",
        "tab_suggestions": "Sugestões",
        "tab_raw": "Log bruto",

        # overview
        "overview_title": "Visão geral de Stardew Valley / SMAPI",
        "overview_game_version": "Versão do jogo",
        "overview_smapi_version": "Versão do SMAPI",
        "overview_unknown": "Desconhecida",
        "overview_summary": "Resumo",
        "overview_mod_count": "Mods carregados: {count}",
        "overview_content_pack_count": "Content packs carregados: {count}",
        "overview_error_count": "Erros: {count}",
        "overview_warning_count": "Avisos: {count}",
        "overview_slow_start": "Tempo de inicialização: {seconds:.1f}s",
        "overview_hint": "Dica: corrija primeiro os erros, depois os avisos e só então os detalhes cosméticos/otimização.",

        # mod health
        "mod_health_title": "Saúde e risco dos mods",
        "mod_health_patched_header": "Mods que alteram o código do jogo (risco maior):",
        "mod_health_save_header": "Mods que mudam o serializador de salvamento (não remova no meio de um save):",
        "mod_health_console_header": "Mods com acesso direto ao console:",
        "mod_health_missing_dep_header": "Mods com dependências ausentes:",
        "mod_health_missing_dep_item": "{mod} → faltando: {missing}",
        "mod_health_none": "Nenhum mod claramente arriscado foi detectado neste log.",
        "mod_health_updates_header": "Mods com atualizações disponíveis:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Erros encontrados neste log",
        "errors_none": "Nenhum erro do SMAPI foi encontrado. 🎉",
        "errors_intro": "Estes são os problemas mais importantes relatados pelo SMAPI:",

        # warnings
        "warnings_header": "Avisos",
        "warnings_none": "Nenhum aviso encontrado.",
        "warnings_intro": "Eles podem não quebrar o jogo na hora, mas valem a sua atenção:",

        # suggestions
        "suggestions_header": "Sugestões de correção",
        "suggestions_none": "Nenhuma sugestão automática por enquanto. Se o jogo ainda estiver estranho, confira as abas de Erros e Avisos.",

        # raw
        "raw_header": "Log completo do SMAPI",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server detectado. Ele pode causar crashes com o SMAPI; adicione uma exceção ou desative-o.",

        # suggestion types
        "sg.skipped_mod": "Corrija o mod {name}: o SMAPI pulou ele ({reason}). Abra a pasta do mod e verifique se o manifest.json é válido e se a versão é compatível com o seu jogo/SMAPI.",
        "sg.failed_mod": "Corrija o mod {name}: o SMAPI não conseguiu carregá-lo ({reason}). Veja as instruções de instalação na página do mod e reinstale se necessário.",
        "sg.missing_dep": "Instale a dependência obrigatória {missing} para o mod {mod}, ou desative o mod se não for usá-lo.",
        "sg.save_serializer": "{mod} altera a forma como o jogo salva. Faça backup dos saves e não remova esse mod no meio de um save.",
        "sg.patched_mods_many": "Você tem muitos mods alterando o código do jogo ({count}). Se aparecerem crashes estranhos, tente desativar utilidades/FX uma por vez.",
        "sg.rivatuner": "RivaTuner Statistics Server pode entrar em conflito com o SMAPI. Adicione uma exceção para Stardew Valley ou feche o programa enquanto joga.",
        "sg.updates": "{count} mod(s) podem ser atualizados. Manter frameworks e mods de base atualizados costuma resolver crashes e problemas invisíveis.",
        "sg.slow_start": "A inicialização do jogo levou cerca de {seconds:.1f}s. Muitos content packs e mods pesados aumentam o tempo de carregamento; se incomodar, considere enxugar um pouco a lista.",
    },
    "es": {
        # window
        "app_title": "Doctor de registros SMAPI",
        "btn_open": "Abrir registro SMAPI",
        "btn_export": "Exportar resumen",
        "status_ready": "Listo. Abre un registro de SMAPI para analizar.",
        "status_loaded": "Registro cargado: {path}",
        "status_no_analysis": "Aún no hay análisis. Abre un registro primero.",
        "status_export_ok": "Resumen exportado a {path}",
        "status_export_fail": "Error al exportar el resumen: {error}",
        "label_language": "Idioma:",
        "dialog_select_log_title": "Seleccionar registro de SMAPI",
        "dialog_export_title": "Exportar resumen",
        "dialog_error_title": "Error",
        "dialog_info_title": "Info",
        "dialog_read_fail": "Error al leer el archivo:\n{error}",
        "dialog_analyze_fail": "Error al analizar el registro:\n{error}",
        "filetype_text": "Archivos de texto",
        "filetype_all": "Todos los archivos",

        # tabs
        "tab_overview": "Resumen",
        "tab_mod_health": "Salud de mods",
        "tab_errors": "Errores",
        "tab_warnings": "Advertencias",
        "tab_suggestions": "Sugerencias",
        "tab_raw": "Registro bruto",

        # overview
        "overview_title": "Resumen de Stardew Valley / SMAPI",
        "overview_game_version": "Versión del juego",
        "overview_smapi_version": "Versión de SMAPI",
        "overview_unknown": "Desconocida",
        "overview_summary": "Resumen",
        "overview_mod_count": "Mods cargados: {count}",
        "overview_content_pack_count": "Packs de contenido cargados: {count}",
        "overview_error_count": "Errores: {count}",
        "overview_warning_count": "Advertencias: {count}",
        "overview_slow_start": "Tiempo de inicio: {seconds:.1f}s",
        "overview_hint": "Consejo: corrige primero los errores, luego las advertencias y después los problemas cosméticos.",

        # mod health
        "mod_health_title": "Salud y riesgo de mods",
        "mod_health_patched_header": "Mods que parchean el código del juego (riesgo elevado):",
        "mod_health_save_header": "Mods que cambian el serializador de guardado (NO quitar a mitad de partida):",
        "mod_health_console_header": "Mods con acceso directo a la consola:",
        "mod_health_missing_dep_header": "Mods con dependencias faltantes:",
        "mod_health_missing_dep_item": "{mod} → falta: {missing}",
        "mod_health_none": "No se detectaron mods arriesgados en este registro.",
        "mod_health_updates_header": "Mods con actualizaciones disponibles:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Errores encontrados en este registro",
        "errors_none": "No se detectaron errores de SMAPI. 🎉",
        "errors_intro": "Estos son los problemas más importantes que SMAPI reportó:",

        # warnings
        "warnings_header": "Advertencias",
        "warnings_none": "No se encontraron advertencias.",
        "warnings_intro": "Puede que no rompan el juego de inmediato, pero conviene revisarlas:",

        # suggestions
        "suggestions_header": "Soluciones sugeridas",
        "suggestions_none": "Sin sugerencias automáticas. Si el juego sigue raro, revisa las pestañas de Errores/Advertencias.",

        # raw
        "raw_header": "Registro completo de SMAPI",

        # generic issues
        "warn_rivatuner": "Se detectó RivaTuner Statistics Server. Puede causar bloqueos con SMAPI; añade una excepción o desactívalo.",

        # suggestion types
        "sg.skipped_mod": "Repara el mod \"{name}\": SMAPI lo omitió ({reason}). Abre su carpeta y verifica que tenga un manifest.json válido y sea compatible con tu versión del juego/SMAPI.",
        "sg.failed_mod": "Repara el mod \"{name}\": SMAPI no pudo cargarlo ({reason}). Revisa las instrucciones de instalación en su página y reinstala si es necesario.",
        "sg.missing_dep": "Instala la dependencia obligatoria \"{missing}\" para \"{mod}\" o desactiva el mod si no lo necesitas.",
        "sg.save_serializer": "\"{mod}\" cambia el serializador de guardado. Haz copia de tus partidas y evita quitarlo a mitad de partida.",
        "sg.patched_mods_many": "Tienes muchos mods parcheando el código del juego ({count}). Si ves fallos extraños, prueba desactivar utilidades/FX una por una.",
        "sg.rivatuner": "RivaTuner Statistics Server puede entrar en conflicto con SMAPI. Añade una excepción para Stardew Valley o cierra el programa mientras juegas.",
        "sg.updates": "Puedes actualizar {count} mod(s). Mantener frameworks y mods base al día suele arreglar fallos y problemas invisibles.",
        "sg.slow_start": "El inicio del juego tomó unos {seconds:.1f}s. Muchos packs de contenido y mods pesados aumentan el tiempo de carga; si molesta, considera recortar la lista.",
    },
    "fr": {
        # window
        "app_title": "Docteur des logs SMAPI",
        "btn_open": "Ouvrir un log SMAPI",
        "btn_export": "Exporter le résumé",
        "status_ready": "Prêt. Ouvrez un log SMAPI à analyser.",
        "status_loaded": "Log chargé : {path}",
        "status_no_analysis": "Pas encore d'analyse. Ouvrez d'abord un log.",
        "status_export_ok": "Résumé exporté vers {path}",
        "status_export_fail": "Échec de l'export du résumé : {error}",
        "label_language": "Langue :",
        "dialog_select_log_title": "Sélectionner un log SMAPI",
        "dialog_export_title": "Exporter le résumé",
        "dialog_error_title": "Erreur",
        "dialog_info_title": "Info",
        "dialog_read_fail": "Échec de lecture du fichier :\n{error}",
        "dialog_analyze_fail": "Échec de l'analyse du log :\n{error}",
        "filetype_text": "Fichiers texte",
        "filetype_all": "Tous les fichiers",

        # tabs
        "tab_overview": "Aperçu",
        "tab_mod_health": "Santé des mods",
        "tab_errors": "Erreurs",
        "tab_warnings": "Avertissements",
        "tab_suggestions": "Suggestions",
        "tab_raw": "Log brut",

        # overview
        "overview_title": "Aperçu Stardew Valley / SMAPI",
        "overview_game_version": "Version du jeu",
        "overview_smapi_version": "Version de SMAPI",
        "overview_unknown": "Inconnue",
        "overview_summary": "Résumé",
        "overview_mod_count": "Mods chargés : {count}",
        "overview_content_pack_count": "Packs de contenu chargés : {count}",
        "overview_error_count": "Erreurs : {count}",
        "overview_warning_count": "Avertissements : {count}",
        "overview_slow_start": "Temps de démarrage : {seconds:.1f}s",
        "overview_hint": "Astuce : corrigez d'abord les erreurs, puis les avertissements, puis les problèmes cosmétiques.",

        # mod health
        "mod_health_title": "Santé et risques des mods",
        "mod_health_patched_header": "Mods qui modifient le code du jeu (risque élevé) :",
        "mod_health_save_header": "Mods modifiant la sérialisation des sauvegardes (ne pas retirer en cours de partie) :",
        "mod_health_console_header": "Mods avec accès direct à la console :",
        "mod_health_missing_dep_header": "Mods avec dépendances manquantes :",
        "mod_health_missing_dep_item": "{mod} → manquant : {missing}",
        "mod_health_none": "Aucun mod risqué détecté dans ce log.",
        "mod_health_updates_header": "Mods avec mises à jour disponibles :",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Erreurs trouvées dans ce log",
        "errors_none": "Aucune erreur SMAPI détectée. 🎉",
        "errors_intro": "Voici les problèmes les plus importants signalés par SMAPI :",

        # warnings
        "warnings_header": "Avertissements",
        "warnings_none": "Aucun avertissement trouvé.",
        "warnings_intro": "Ils ne cassent pas forcément le jeu immédiatement, mais il vaut mieux les vérifier :",

        # suggestions
        "suggestions_header": "Corrections suggérées",
        "suggestions_none": "Aucune suggestion automatique. Si le jeu reste instable, consultez les onglets Erreurs/Avertissements.",

        # raw
        "raw_header": "Log SMAPI complet",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server détecté. Il peut provoquer des crashs avec SMAPI ; ajoutez une exception ou désactivez-le.",

        # suggestion types
        "sg.skipped_mod": "Corrigez le mod \"{name}\" : SMAPI l'a ignoré ({reason}). Ouvrez son dossier et vérifiez que manifest.json est valide et compatible avec votre version du jeu/SMAPI.",
        "sg.failed_mod": "Corrigez le mod \"{name}\" : SMAPI n'a pas pu le charger ({reason}). Consultez les instructions d'installation sur sa page et réinstallez si besoin.",
        "sg.missing_dep": "Installez la dépendance requise \"{missing}\" pour \"{mod}\" ou désactivez le mod si vous n'en avez pas besoin.",
        "sg.save_serializer": "\"{mod}\" modifie le sérialiseur de sauvegarde. Sauvegardez vos parties et évitez de retirer ce mod en cours de partie.",
        "sg.patched_mods_many": "Vous avez de nombreux mods qui modifient le code du jeu ({count}). En cas de crashs étranges, essayez de désactiver les utilitaires/FX un par un.",
        "sg.rivatuner": "RivaTuner Statistics Server peut entrer en conflit avec SMAPI. Ajoutez une exception pour Stardew Valley ou fermez le programme pendant que vous jouez.",
        "sg.updates": "Vous pouvez mettre à jour {count} mod(s). Garder les frameworks et mods de base à jour règle souvent les crashs et problèmes invisibles.",
        "sg.slow_start": "Le démarrage du jeu a pris environ {seconds:.1f}s. Les gros packs de contenu et les mods lourds rallongent le chargement ; si cela vous gêne, envisagez d'alléger votre liste.",
    },
    "de": {
        # window
        "app_title": "SMAPI-Logdoktor",
        "btn_open": "SMAPI-Log öffnen",
        "btn_export": "Zusammenfassung exportieren",
        "status_ready": "Bereit. Öffne einen SMAPI-Log zur Analyse.",
        "status_loaded": "Log geladen: {path}",
        "status_no_analysis": "Noch keine Analyse. Öffne zuerst einen Log.",
        "status_export_ok": "Zusammenfassung exportiert nach {path}",
        "status_export_fail": "Zusammenfassung konnte nicht exportiert werden: {error}",
        "label_language": "Sprache:",
        "dialog_select_log_title": "SMAPI-Log auswählen",
        "dialog_export_title": "Zusammenfassung exportieren",
        "dialog_error_title": "Fehler",
        "dialog_info_title": "Info",
        "dialog_read_fail": "Datei konnte nicht gelesen werden:\n{error}",
        "dialog_analyze_fail": "Log konnte nicht analysiert werden:\n{error}",
        "filetype_text": "Textdateien",
        "filetype_all": "Alle Dateien",

        # tabs
        "tab_overview": "Übersicht",
        "tab_mod_health": "Mod-Gesundheit",
        "tab_errors": "Fehler",
        "tab_warnings": "Warnungen",
        "tab_suggestions": "Vorschläge",
        "tab_raw": "Roh-Log",

        # overview
        "overview_title": "Übersicht Stardew Valley / SMAPI",
        "overview_game_version": "Spielversion",
        "overview_smapi_version": "SMAPI-Version",
        "overview_unknown": "Unbekannt",
        "overview_summary": "Zusammenfassung",
        "overview_mod_count": "Geladene Mods: {count}",
        "overview_content_pack_count": "Geladene Content-Packs: {count}",
        "overview_error_count": "Fehler: {count}",
        "overview_warning_count": "Warnungen: {count}",
        "overview_slow_start": "Startzeit: {seconds:.1f}s",
        "overview_hint": "Tipp: zuerst Fehler beheben, dann Warnungen, dann kosmetische/kleine Probleme.",

        # mod health
        "mod_health_title": "Mod-Gesundheit & Risiko",
        "mod_health_patched_header": "Mods, die den Spielcode patchen (höheres Risiko):",
        "mod_health_save_header": "Mods, die den Speicherserializer ändern (nicht mitten im Spiel entfernen!):",
        "mod_health_console_header": "Mods mit direktem Konsolenzugriff:",
        "mod_health_missing_dep_header": "Mods mit fehlenden Abhängigkeiten:",
        "mod_health_missing_dep_item": "{mod} → fehlt: {missing}",
        "mod_health_none": "Keine riskanten Mods in diesem Log gefunden.",
        "mod_health_updates_header": "Mods mit verfügbaren Updates:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Fehler in diesem Log",
        "errors_none": "Keine SMAPI-Fehler gefunden. 🎉",
        "errors_intro": "Dies sind die wichtigsten Probleme, die SMAPI meldet:",

        # warnings
        "warnings_header": "Warnungen",
        "warnings_none": "Keine Warnungen gefunden.",
        "warnings_intro": "Sie verursachen vielleicht nicht sofort Probleme, sollten aber überprüft werden:",

        # suggestions
        "suggestions_header": "Vorgeschlagene Lösungen",
        "suggestions_none": "Keine automatischen Vorschläge. Wenn das Spiel weiterhin spinnt, prüfe die Tabs Fehler/Warnungen.",

        # raw
        "raw_header": "Vollständiger SMAPI-Log",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server erkannt. Er kann mit SMAPI Abstürze verursachen; füge eine Ausnahme hinzu oder deaktiviere ihn.",

        # suggestion types
        "sg.skipped_mod": "Mod \"{name}\" reparieren: SMAPI hat ihn übersprungen ({reason}). Öffne den Mod-Ordner und stelle sicher, dass manifest.json gültig ist und die Version zu deinem Spiel/SMAPI passt.",
        "sg.failed_mod": "Mod \"{name}\" reparieren: SMAPI konnte ihn nicht laden ({reason}). Prüfe die Installationsanleitung auf der Mod-Seite und installiere ggf. neu.",
        "sg.missing_dep": "Benötigte Abhängigkeit \"{missing}\" für \"{mod}\" installieren oder den Mod deaktivieren, falls nicht gebraucht.",
        "sg.save_serializer": "\"{mod}\" ändert den Speicherserializer. Sichere deine Spielstände und entferne den Mod nicht mitten im Durchgang.",
        "sg.patched_mods_many": "Du hast viele Mods, die den Spielcode patchen ({count}). Bei seltsamen Abstürzen deaktiviere Dienst-/FX-Mods nacheinander.",
        "sg.rivatuner": "RivaTuner Statistics Server kann mit SMAPI kollidieren. Füge eine Ausnahme für Stardew Valley hinzu oder schließe das Programm beim Spielen.",
        "sg.updates": "Du kannst {count} Mods aktualisieren. Aktuelle Frameworks und Basismods beheben oft Abstürze und versteckte Probleme.",
        "sg.slow_start": "Der Spielstart dauerte etwa {seconds:.1f}s. Viele Content-Packs und schwere Mods verlängern die Ladezeit; wenn es stört, reduziere die Modliste etwas.",
    },
    "it": {
        # window
        "app_title": "Dottore dei log SMAPI",
        "btn_open": "Apri log SMAPI",
        "btn_export": "Esporta riepilogo",
        "status_ready": "Pronto. Apri un log SMAPI da analizzare.",
        "status_loaded": "Log caricato: {path}",
        "status_no_analysis": "Nessuna analisi ancora. Apri prima un log.",
        "status_export_ok": "Riepilogo esportato in {path}",
        "status_export_fail": "Esportazione del riepilogo non riuscita: {error}",
        "label_language": "Lingua:",
        "dialog_select_log_title": "Seleziona log SMAPI",
        "dialog_export_title": "Esporta riepilogo",
        "dialog_error_title": "Errore",
        "dialog_info_title": "Info",
        "dialog_read_fail": "Impossibile leggere il file:\n{error}",
        "dialog_analyze_fail": "Impossibile analizzare il log:\n{error}",
        "filetype_text": "File di testo",
        "filetype_all": "Tutti i file",

        # tabs
        "tab_overview": "Panoramica",
        "tab_mod_health": "Salute mod",
        "tab_errors": "Errori",
        "tab_warnings": "Avvisi",
        "tab_suggestions": "Suggerimenti",
        "tab_raw": "Log grezzo",

        # overview
        "overview_title": "Panoramica Stardew Valley / SMAPI",
        "overview_game_version": "Versione del gioco",
        "overview_smapi_version": "Versione SMAPI",
        "overview_unknown": "Sconosciuta",
        "overview_summary": "Riepilogo",
        "overview_mod_count": "Mod caricati: {count}",
        "overview_content_pack_count": "Content pack caricati: {count}",
        "overview_error_count": "Errori: {count}",
        "overview_warning_count": "Avvisi: {count}",
        "overview_slow_start": "Tempo di avvio: {seconds:.1f}s",
        "overview_hint": "Suggerimento: correggi prima gli errori, poi gli avvisi e infine i problemi cosmetici.",

        # mod health
        "mod_health_title": "Salute e rischio mod",
        "mod_health_patched_header": "Mod che modificano il codice di gioco (rischio elevato):",
        "mod_health_save_header": "Mod che cambiano il serializzatore di salvataggio (NON rimuovere a metà partita):",
        "mod_health_console_header": "Mod con accesso diretto alla console:",
        "mod_health_missing_dep_header": "Mod con dipendenze mancanti:",
        "mod_health_missing_dep_item": "{mod} → mancante: {missing}",
        "mod_health_none": "Nessun mod rischioso rilevato in questo log.",
        "mod_health_updates_header": "Mod con aggiornamenti disponibili:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Errori trovati in questo log",
        "errors_none": "Nessun errore SMAPI rilevato. 🎉",
        "errors_intro": "Questi sono i problemi più importanti segnalati da SMAPI:",

        # warnings
        "warnings_header": "Avvisi",
        "warnings_none": "Nessun avviso trovato.",
        "warnings_intro": "Potrebbero non rompere subito il gioco, ma è meglio controllarli:",

        # suggestions
        "suggestions_header": "Soluzioni suggerite",
        "suggestions_none": "Nessun suggerimento automatico. Se il gioco continua a dare problemi, controlla le schede Errori/Avvisi.",

        # raw
        "raw_header": "Log completo SMAPI",

        # generic issues
        "warn_rivatuner": "Rilevato RivaTuner Statistics Server. Può causare crash con SMAPI; aggiungi un'eccezione o disattivalo.",

        # suggestion types
        "sg.skipped_mod": "Correggi il mod \"{name}\": SMAPI lo ha saltato ({reason}). Apri la cartella e assicurati che manifest.json sia valido e compatibile con la tua versione del gioco/SMAPI.",
        "sg.failed_mod": "Correggi il mod \"{name}\": SMAPI non è riuscito a caricarlo ({reason}). Controlla le istruzioni di installazione sulla pagina del mod e reinstalla se necessario.",
        "sg.missing_dep": "Installa la dipendenza obbligatoria \"{missing}\" per \"{mod}\" oppure disattiva il mod se non ti serve.",
        "sg.save_serializer": "\"{mod}\" modifica il serializzatore di salvataggio. Fai un backup dei salvataggi ed evita di rimuovere il mod a metà partita.",
        "sg.patched_mods_many": "Hai molti mod che modificano il codice di gioco ({count}). Se vedi crash strani, prova a disattivare utility/FX una alla volta.",
        "sg.rivatuner": "RivaTuner Statistics Server può entrare in conflitto con SMAPI. Aggiungi un'eccezione per Stardew Valley o chiudi il programma mentre giochi.",
        "sg.updates": "Puoi aggiornare {count} mod. Mantenere aggiornati framework e mod base spesso risolve crash e problemi nascosti.",
        "sg.slow_start": "L'avvio del gioco ha impiegato circa {seconds:.1f}s. Molti content pack e mod pesanti aumentano i tempi di caricamento; se è un problema, riduci un po' la lista.",
    },
    "ja": {
        # window
        "app_title": "SMAPI ログドクター",
        "btn_open": "SMAPI ログを開く",
        "btn_export": "概要をエクスポート",
        "status_ready": "準備完了。SMAPI ログを開いて分析してください。",
        "status_loaded": "ログを読み込みました: {path}",
        "status_no_analysis": "まだ分析していません。まずログを開いてください。",
        "status_export_ok": "概要を {path} に書き出しました",
        "status_export_fail": "概要の書き出しに失敗しました: {error}",
        "label_language": "言語:",
        "dialog_select_log_title": "SMAPI ログを選択",
        "dialog_export_title": "概要をエクスポート",
        "dialog_error_title": "エラー",
        "dialog_info_title": "情報",
        "dialog_read_fail": "ファイルの読み込みに失敗しました:\n{error}",
        "dialog_analyze_fail": "ログの分析に失敗しました:\n{error}",
        "filetype_text": "テキストファイル",
        "filetype_all": "すべてのファイル",

        # tabs
        "tab_overview": "概要",
        "tab_mod_health": "Mod の状態",
        "tab_errors": "エラー",
        "tab_warnings": "警告",
        "tab_suggestions": "提案",
        "tab_raw": "生ログ",

        # overview
        "overview_title": "Stardew Valley / SMAPI の概要",
        "overview_game_version": "ゲームバージョン",
        "overview_smapi_version": "SMAPI バージョン",
        "overview_unknown": "不明",
        "overview_summary": "概要",
        "overview_mod_count": "読み込んだ Mod 数: {count}",
        "overview_content_pack_count": "読み込んだコンテンツパック数: {count}",
        "overview_error_count": "エラー: {count}",
        "overview_warning_count": "警告: {count}",
        "overview_slow_start": "起動時間: {seconds:.1f}秒",
        "overview_hint": "ヒント: まずエラーを直し、その後警告、最後に見た目や軽微な問題を確認しましょう。",

        # mod health
        "mod_health_title": "Mod の健全性とリスク",
        "mod_health_patched_header": "ゲームコードをパッチする Mod（リスク高）:",
        "mod_health_save_header": "セーブのシリアライザーを変更する Mod（プレイ途中で削除しないで）:",
        "mod_health_console_header": "コンソールへ直接アクセスする Mod:",
        "mod_health_missing_dep_header": "依存関係が欠けている Mod:",
        "mod_health_missing_dep_item": "{mod} → 不足: {missing}",
        "mod_health_none": "このログにはリスクの高い Mod は見つかりませんでした。",
        "mod_health_updates_header": "更新が利用できる Mod:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "このログで見つかったエラー",
        "errors_none": "SMAPI エラーは見つかりませんでした。 🎉",
        "errors_intro": "SMAPI が報告した重要な問題はこちらです:",

        # warnings
        "warnings_header": "警告",
        "warnings_none": "警告は見つかりませんでした。",
        "warnings_intro": "すぐにゲームが壊れるとは限りませんが、確認をおすすめします:",

        # suggestions
        "suggestions_header": "提案された修正",
        "suggestions_none": "自動提案はありません。まだ問題がある場合はエラー/警告タブを確認してください。",

        # raw
        "raw_header": "SMAPI ログ全体",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server を検出しました。SMAPI と衝突しクラッシュの原因になることがあります。例外を追加するか無効にしてください。",

        # suggestion types
        "sg.skipped_mod": "Mod \"{name}\" を修正してください: SMAPI がスキップしました（理由: {reason}）。フォルダーを開き、manifest.json が有効でゲーム/SMAPI のバージョンに対応しているか確認してください。",
        "sg.failed_mod": "Mod \"{name}\" を修正してください: SMAPI が読み込めませんでした（理由: {reason}）。Mod ページのインストール手順を確認し、必要なら再インストールしてください。",
        "sg.missing_dep": "Mod \"{mod}\" に必要な依存関係 \"{missing}\" をインストールするか、不要なら Mod を無効化してください。",
        "sg.save_serializer": "\"{mod}\" はセーブのシリアライザーを変更します。セーブのバックアップを取り、プレイ中にこの Mod を削除しないでください。",
        "sg.patched_mods_many": "ゲームコードをパッチする Mod が多くあります（{count} 件）。奇妙なクラッシュが起きる場合、ユーティリティ/FX Mod を一つずつ無効化して試してください。",
        "sg.rivatuner": "RivaTuner Statistics Server は SMAPI と競合する可能性があります。Stardew Valley 用の例外を追加するか、プレイ中は終了してください。",
        "sg.updates": "{count} 個の Mod を更新できます。フレームワークや基盤 Mod を最新に保つとクラッシュや見えない問題がよく解消されます。",
        "sg.slow_start": "ゲームの起動に約 {seconds:.1f} 秒かかりました。大きなコンテンツパックや重い Mod はロード時間を延ばします。気になる場合は少し減らしてください。",
    },
    "ko": {
        # window
        "app_title": "SMAPI 로그 닥터",
        "btn_open": "SMAPI 로그 열기",
        "btn_export": "요약 내보내기",
        "status_ready": "준비 완료. 분석할 SMAPI 로그를 열어주세요.",
        "status_loaded": "로그 불러옴: {path}",
        "status_no_analysis": "아직 분석 전입니다. 먼저 로그를 여세요.",
        "status_export_ok": "요약을 {path}에 저장했습니다",
        "status_export_fail": "요약 내보내기에 실패했습니다: {error}",
        "label_language": "언어:",
        "dialog_select_log_title": "SMAPI 로그 선택",
        "dialog_export_title": "요약 내보내기",
        "dialog_error_title": "오류",
        "dialog_info_title": "정보",
        "dialog_read_fail": "파일을 읽지 못했습니다:\n{error}",
        "dialog_analyze_fail": "로그 분석에 실패했습니다:\n{error}",
        "filetype_text": "텍스트 파일",
        "filetype_all": "모든 파일",

        # tabs
        "tab_overview": "개요",
        "tab_mod_health": "모드 상태",
        "tab_errors": "오류",
        "tab_warnings": "경고",
        "tab_suggestions": "제안",
        "tab_raw": "원본 로그",

        # overview
        "overview_title": "Stardew Valley / SMAPI 개요",
        "overview_game_version": "게임 버전",
        "overview_smapi_version": "SMAPI 버전",
        "overview_unknown": "알 수 없음",
        "overview_summary": "요약",
        "overview_mod_count": "불러온 모드: {count}",
        "overview_content_pack_count": "불러온 콘텐츠 팩: {count}",
        "overview_error_count": "오류: {count}",
        "overview_warning_count": "경고: {count}",
        "overview_slow_start": "시작 시간: {seconds:.1f}초",
        "overview_hint": "팁: 먼저 오류를 고치고, 그다음 경고, 마지막으로 외형/최적화 문제를 처리하세요.",

        # mod health
        "mod_health_title": "모드 상태와 위험도",
        "mod_health_patched_header": "게임 코드를 패치하는 모드(위험 높음):",
        "mod_health_save_header": "세이브 직렬화를 변경하는 모드(플레이 중간에 제거 금지):",
        "mod_health_console_header": "콘솔에 직접 접근하는 모드:",
        "mod_health_missing_dep_header": "누락된 의존성이 있는 모드:",
        "mod_health_missing_dep_item": "{mod} → 누락: {missing}",
        "mod_health_none": "이 로그에서 위험한 모드는 감지되지 않았습니다.",
        "mod_health_updates_header": "업데이트 가능한 모드:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "이 로그에서 발견된 오류",
        "errors_none": "SMAPI 오류가 없습니다. 🎉",
        "errors_intro": "SMAPI가 보고한 가장 중요한 문제들입니다:",

        # warnings
        "warnings_header": "경고",
        "warnings_none": "경고가 없습니다.",
        "warnings_intro": "당장은 문제를 일으키지 않을 수 있지만 확인하는 게 좋습니다:",

        # suggestions
        "suggestions_header": "제안된 해결책",
        "suggestions_none": "자동 제안이 없습니다. 문제가 계속되면 오류/경고 탭을 확인하세요.",

        # raw
        "raw_header": "SMAPI 전체 로그",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server가 감지되었습니다. SMAPI와 충돌해 크래시를 일으킬 수 있으니 예외를 추가하거나 종료하세요.",

        # suggestion types
        "sg.skipped_mod": "모드 \"{name}\"를 수정하세요: SMAPI가 건너뛰었습니다(이유: {reason}). 폴더를 열어 manifest.json이 올바르고 게임/SMAPI 버전에 맞는지 확인하세요.",
        "sg.failed_mod": "모드 \"{name}\"를 수정하세요: SMAPI가 로드하지 못했습니다(이유: {reason}). 모드 페이지의 설치 방법을 확인하고 필요하면 다시 설치하세요.",
        "sg.missing_dep": "모드 \"{mod}\"에 필요한 의존성 \"{missing}\"을 설치하거나 필요 없다면 모드를 비활성화하세요.",
        "sg.save_serializer": "\"{mod}\"가 세이브 직렬화를 변경합니다. 세이브를 백업하고 플레이 중간에 이 모드를 제거하지 마세요.",
        "sg.patched_mods_many": "게임 코드를 패치하는 모드가 많습니다({count}개). 이상한 크래시가 발생하면 유틸리티/FX 모드를 하나씩 끄면서 확인하세요.",
        "sg.rivatuner": "RivaTuner Statistics Server가 SMAPI와 충돌할 수 있습니다. Stardew Valley에 대한 예외를 추가하거나 플레이 중 종료하세요.",
        "sg.updates": "{count}개의 모드를 업데이트할 수 있습니다. 프레임워크와 기본 모드를 최신으로 유지하면 크래시와 숨은 문제를 자주 해결합니다.",
        "sg.slow_start": "게임 시작에 약 {seconds:.1f}초가 걸렸습니다. 대형 콘텐츠 팩과 무거운 모드가 로딩 시간을 늘립니다. 불편하면 목록을 조금 줄여보세요.",
    },
    "pl": {
        # window
        "app_title": "Doktor logów SMAPI",
        "btn_open": "Otwórz log SMAPI",
        "btn_export": "Eksportuj podsumowanie",
        "status_ready": "Gotowe. Otwórz log SMAPI do analizy.",
        "status_loaded": "Wczytano log: {path}",
        "status_no_analysis": "Brak analizy. Najpierw otwórz log.",
        "status_export_ok": "Podsumowanie zapisano w {path}",
        "status_export_fail": "Nie udało się wyeksportować podsumowania: {error}",
        "label_language": "Język:",
        "dialog_select_log_title": "Wybierz log SMAPI",
        "dialog_export_title": "Eksport podsumowania",
        "dialog_error_title": "Błąd",
        "dialog_info_title": "Informacja",
        "dialog_read_fail": "Nie udało się odczytać pliku:\n{error}",
        "dialog_analyze_fail": "Nie udało się przeanalizować logu:\n{error}",
        "filetype_text": "Pliki tekstowe",
        "filetype_all": "Wszystkie pliki",

        # tabs
        "tab_overview": "Przegląd",
        "tab_mod_health": "Stan modów",
        "tab_errors": "Błędy",
        "tab_warnings": "Ostrzeżenia",
        "tab_suggestions": "Sugestie",
        "tab_raw": "Surowy log",

        # overview
        "overview_title": "Przegląd Stardew Valley / SMAPI",
        "overview_game_version": "Wersja gry",
        "overview_smapi_version": "Wersja SMAPI",
        "overview_unknown": "Nieznana",
        "overview_summary": "Podsumowanie",
        "overview_mod_count": "Załadowane mody: {count}",
        "overview_content_pack_count": "Załadowane paczki zawartości: {count}",
        "overview_error_count": "Błędy: {count}",
        "overview_warning_count": "Ostrzeżenia: {count}",
        "overview_slow_start": "Czas startu: {seconds:.1f}s",
        "overview_hint": "Wskazówka: napraw najpierw błędy, potem ostrzeżenia, na końcu kwestie kosmetyczne.",

        # mod health
        "mod_health_title": "Stan i ryzyko modów",
        "mod_health_patched_header": "Mody modyfikujące kod gry (większe ryzyko):",
        "mod_health_save_header": "Mody zmieniające serializator zapisu (nie usuwać w trakcie rozgrywki):",
        "mod_health_console_header": "Mody z bezpośrednim dostępem do konsoli:",
        "mod_health_missing_dep_header": "Mody z brakującymi zależnościami:",
        "mod_health_missing_dep_item": "{mod} → brak: {missing}",
        "mod_health_none": "Nie wykryto ryzykownych modów w tym logu.",
        "mod_health_updates_header": "Mody z dostępnymi aktualizacjami:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Błędy w tym logu",
        "errors_none": "Nie znaleziono błędów SMAPI. 🎉",
        "errors_intro": "To najważniejsze problemy zgłoszone przez SMAPI:",

        # warnings
        "warnings_header": "Ostrzeżenia",
        "warnings_none": "Nie znaleziono ostrzeżeń.",
        "warnings_intro": "Nie muszą od razu psuć gry, ale warto je sprawdzić:",

        # suggestions
        "suggestions_header": "Proponowane rozwiązania",
        "suggestions_none": "Brak automatycznych sugestii. Jeśli gra dalej sprawia problemy, sprawdź karty Błędy/Ostrzeżenia.",

        # raw
        "raw_header": "Pełny log SMAPI",

        # generic issues
        "warn_rivatuner": "Wykryto RivaTuner Statistics Server. Może powodować awarie ze SMAPI; dodaj wyjątek lub wyłącz program.",

        # suggestion types
        "sg.skipped_mod": "Napraw mod \"{name}\": SMAPI pominął go (powód: {reason}). Otwórz folder moda i upewnij się, że manifest.json jest poprawny i zgodny z twoją wersją gry/SMAPI.",
        "sg.failed_mod": "Napraw mod \"{name}\": SMAPI nie mógł go załadować (powód: {reason}). Sprawdź instrukcję instalacji na stronie moda i w razie potrzeby zainstaluj ponownie.",
        "sg.missing_dep": "Zainstaluj wymaganą zależność \"{missing}\" dla moda \"{mod}\" lub wyłącz mod, jeśli go nie potrzebujesz.",
        "sg.save_serializer": "\"{mod}\" zmienia sposób zapisu. Zrób kopię zapasową zapisów i nie usuwaj moda w trakcie gry.",
        "sg.patched_mods_many": "Masz wiele modów modyfikujących kod gry ({count}). Przy dziwnych awariach wyłączaj narzędzia/FX po kolei.",
        "sg.rivatuner": "RivaTuner Statistics Server może kolidować ze SMAPI. Dodaj wyjątek dla Stardew Valley lub zamknij program podczas gry.",
        "sg.updates": "Możesz zaktualizować {count} mod(ów). Aktualne frameworki i bazowe mody często rozwiązują awarie i ukryte problemy.",
        "sg.slow_start": "Uruchomienie gry trwało około {seconds:.1f}s. Duże paczki zawartości i ciężkie mody wydłużają ładowanie; jeśli przeszkadza, ogranicz listę modów.",
    },
    "pt-BR": {
        # window
        "app_title": "Doutor de Logs do SMAPI",
        "btn_open": "Abrir log do SMAPI",
        "btn_export": "Exportar resumo",
        "status_ready": "Pronto. Abra um log do SMAPI para analisar.",
        "status_loaded": "Log carregado: {path}",
        "status_no_analysis": "Ainda não há análise. Abra um log primeiro.",
        "status_export_ok": "Resumo exportado para {path}",
        "status_export_fail": "Falha ao exportar resumo: {error}",
        "label_language": "Idioma:",
        "dialog_select_log_title": "Selecionar log do SMAPI",
        "dialog_export_title": "Exportar resumo",
        "dialog_error_title": "Erro",
        "dialog_info_title": "Informação",
        "dialog_read_fail": "Falha ao ler o arquivo:\n{error}",
        "dialog_analyze_fail": "Falha ao analisar o log:\n{error}",
        "filetype_text": "Arquivos de texto",
        "filetype_all": "Todos os arquivos",

        # tabs
        "tab_overview": "Visão geral",
        "tab_mod_health": "Saúde dos mods",
        "tab_errors": "Erros",
        "tab_warnings": "Avisos",
        "tab_suggestions": "Sugestões",
        "tab_raw": "Log bruto",

        # overview
        "overview_title": "Visão geral de Stardew Valley / SMAPI",
        "overview_game_version": "Versão do jogo",
        "overview_smapi_version": "Versão do SMAPI",
        "overview_unknown": "Desconhecida",
        "overview_summary": "Resumo",
        "overview_mod_count": "Mods carregados: {count}",
        "overview_content_pack_count": "Content packs carregados: {count}",
        "overview_error_count": "Erros: {count}",
        "overview_warning_count": "Avisos: {count}",
        "overview_slow_start": "Tempo de inicialização: {seconds:.1f}s",
        "overview_hint": "Dica: corrija primeiro os erros, depois os avisos e só então os detalhes cosméticos/otimização.",

        # mod health
        "mod_health_title": "Saúde e risco dos mods",
        "mod_health_patched_header": "Mods que alteram o código do jogo (risco maior):",
        "mod_health_save_header": "Mods que mudam o serializador de salvamento (não remova no meio de um save):",
        "mod_health_console_header": "Mods com acesso direto ao console:",
        "mod_health_missing_dep_header": "Mods com dependências ausentes:",
        "mod_health_missing_dep_item": "{mod} → faltando: {missing}",
        "mod_health_none": "Nenhum mod claramente arriscado foi detectado neste log.",
        "mod_health_updates_header": "Mods com atualizações disponíveis:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Erros encontrados neste log",
        "errors_none": "Nenhum erro do SMAPI foi encontrado. 🎉",
        "errors_intro": "Estes são os problemas mais importantes relatados pelo SMAPI:",

        # warnings
        "warnings_header": "Avisos",
        "warnings_none": "Nenhum aviso encontrado.",
        "warnings_intro": "Eles podem não quebrar o jogo na hora, mas valem a sua atenção:",

        # suggestions
        "suggestions_header": "Sugestões de correção",
        "suggestions_none": "Nenhuma sugestão automática por enquanto. Se o jogo ainda estiver estranho, confira as abas de Erros e Avisos.",

        # raw
        "raw_header": "Log completo do SMAPI",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server detectado. Ele pode causar crashes com o SMAPI; adicione uma exceção ou desative-o.",

        # suggestion types
        "sg.skipped_mod": "Corrija o mod \"{name}\": o SMAPI pulou ele ({reason}). Abra a pasta do mod e verifique se o manifest.json é válido e se a versão é compatível com o seu jogo/SMAPI.",
        "sg.failed_mod": "Corrija o mod \"{name}\": o SMAPI não conseguiu carregá-lo ({reason}). Veja as instruções de instalação na página do mod e reinstale se necessário.",
        "sg.missing_dep": "Instale a dependência obrigatória \"{missing}\" para o mod \"{mod}\", ou desative o mod se não for usá-lo.",
        "sg.save_serializer": "{mod} altera a forma como o jogo salva. Faça backup dos saves e não remova esse mod no meio de um save.",
        "sg.patched_mods_many": "Você tem muitos mods alterando o código do jogo ({count}). Se aparecerem crashes estranhos, tente desativar utilidades/FX uma por vez.",
        "sg.rivatuner": "RivaTuner Statistics Server pode entrar em conflito com o SMAPI. Adicione uma exceção para Stardew Valley ou feche o programa enquanto joga.",
        "sg.updates": "{count} mod(s) podem ser atualizados. Manter frameworks e mods de base atualizados costuma resolver crashes e problemas invisíveis.",
        "sg.slow_start": "A inicialização do jogo levou cerca de {seconds:.1f}s. Muitos content packs e mods pesados aumentam o tempo de carregamento; se incomodar, considere enxugar um pouco a lista.",
    },
    "tr": {
        # window
        "app_title": "SMAPI Log Doktoru",
        "btn_open": "SMAPI günlüğünü aç",
        "btn_export": "Özeti dışa aktar",
        "status_ready": "Hazır. Analiz için bir SMAPI günlüğü açın.",
        "status_loaded": "Günlük yüklendi: {path}",
        "status_no_analysis": "Henüz analiz yok. Önce bir günlük açın.",
        "status_export_ok": "Özet {path} konumuna aktarıldı",
        "status_export_fail": "Özet dışa aktarılamadı: {error}",
        "label_language": "Dil:",
        "dialog_select_log_title": "SMAPI günlüğünü seç",
        "dialog_export_title": "Özeti dışa aktar",
        "dialog_error_title": "Hata",
        "dialog_info_title": "Bilgi",
        "dialog_read_fail": "Dosya okunamadı:\n{error}",
        "dialog_analyze_fail": "Günlük analiz edilemedi:\n{error}",
        "filetype_text": "Metin dosyaları",
        "filetype_all": "Tüm dosyalar",

        # tabs
        "tab_overview": "Genel bakış",
        "tab_mod_health": "Mod sağlığı",
        "tab_errors": "Hatalar",
        "tab_warnings": "Uyarılar",
        "tab_suggestions": "Öneriler",
        "tab_raw": "Ham günlük",

        # overview
        "overview_title": "Stardew Valley / SMAPI genel bakış",
        "overview_game_version": "Oyun sürümü",
        "overview_smapi_version": "SMAPI sürümü",
        "overview_unknown": "Bilinmiyor",
        "overview_summary": "Özet",
        "overview_mod_count": "Yüklenen modlar: {count}",
        "overview_content_pack_count": "Yüklenen içerik paketleri: {count}",
        "overview_error_count": "Hatalar: {count}",
        "overview_warning_count": "Uyarılar: {count}",
        "overview_slow_start": "Başlatma süresi: {seconds:.1f}s",
        "overview_hint": "İpucu: Önce hataları, sonra uyarıları, ardından kozmetik/uyumluluk sorunlarını düzeltin.",

        # mod health
        "mod_health_title": "Mod sağlığı ve risk",
        "mod_health_patched_header": "Oyun kodunu yamalayan modlar (daha yüksek risk):",
        "mod_health_save_header": "Kayıt serileştiricisini değiştiren modlar (oyun ortasında kaldırmayın):",
        "mod_health_console_header": "Konsola doğrudan erişen modlar:",
        "mod_health_missing_dep_header": "Eksik bağımlılıkları olan modlar:",
        "mod_health_missing_dep_item": "{mod} → eksik: {missing}",
        "mod_health_none": "Bu günlükte riskli mod bulunamadı.",
        "mod_health_updates_header": "Güncellemesi olan modlar:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Bu günlükteki hatalar",
        "errors_none": "SMAPI hatası bulunamadı. 🎉",
        "errors_intro": "SMAPI'nin bildirdiği en önemli sorunlar:",

        # warnings
        "warnings_header": "Uyarılar",
        "warnings_none": "Uyarı bulunamadı.",
        "warnings_intro": "Hemen hataya yol açmayabilirler ancak göz atmaya değer:",

        # suggestions
        "suggestions_header": "Önerilen çözümler",
        "suggestions_none": "Otomatik öneri yok. Oyun hâlâ sorunluysa Hatalar/Uyarılar sekmelerini kontrol edin.",

        # raw
        "raw_header": "SMAPI günlüğünün tamamı",

        # generic issues
        "warn_rivatuner": "RivaTuner Statistics Server algılandı. SMAPI ile çakışıp çökme yaratabilir; bir istisna ekleyin veya devre dışı bırakın.",

        # suggestion types
        "sg.skipped_mod": "\"{name}\" modunu düzeltin: SMAPI modü atladı (neden: {reason}). Klasörünü açın ve manifest.json'un geçerli ve oyun/SMAPI sürümünüzle uyumlu olduğundan emin olun.",
        "sg.failed_mod": "\"{name}\" modunu düzeltin: SMAPI yükleyemedi (neden: {reason}). Mod sayfasındaki kurulum talimatlarını kontrol edin ve gerekirse yeniden kurun.",
        "sg.missing_dep": "\"{mod}\" için gerekli bağımlılık \"{missing}\"'i kurun veya mod gerekli değilse devre dışı bırakın.",
        "sg.save_serializer": "\"{mod}\" kayıt serileştiricisini değiştiriyor. Kayıtlarınızı yedekleyin ve oyunun ortasında modu kaldırmayın.",
        "sg.patched_mods_many": "Oyun kodunu yamalayan çok sayıda modunuz var ({count}). Garip çökmeler görürseniz yardımcı/FX modlarını teker teker devre dışı bırakmayı deneyin.",
        "sg.rivatuner": "RivaTuner Statistics Server, SMAPI ile çakışabilir. Stardew Valley için istisna ekleyin veya oynarken programı kapatın.",
        "sg.updates": "{count} mod'u güncelleyebilirsiniz. Çerçeve ve temel modları güncel tutmak, çökmeleri ve görünmeyen sorunları sıkça çözer.",
        "sg.slow_start": "Oyunun başlaması yaklaşık {seconds:.1f}s sürdü. Büyük içerik paketleri ve ağır modlar yükleme süresini uzatır; rahatsız ediyorsa listeyi biraz azaltın.",
    },
    "uk": {
        # window
        "app_title": "Лікар логів SMAPI",
        "btn_open": "Відкрити лог SMAPI",
        "btn_export": "Експортувати підсумок",
        "status_ready": "Готово. Відкрийте лог SMAPI для аналізу.",
        "status_loaded": "Лог завантажено: {path}",
        "status_no_analysis": "Аналізу ще немає. Спочатку відкрийте лог.",
        "status_export_ok": "Підсумок експортовано до {path}",
        "status_export_fail": "Не вдалося експортувати підсумок: {error}",
        "label_language": "Мова:",
        "dialog_select_log_title": "Виберіть лог SMAPI",
        "dialog_export_title": "Експорт підсумку",
        "dialog_error_title": "Помилка",
        "dialog_info_title": "Інформація",
        "dialog_read_fail": "Не вдалося прочитати файл:\n{error}",
        "dialog_analyze_fail": "Не вдалося проаналізувати лог:\n{error}",
        "filetype_text": "Текстові файли",
        "filetype_all": "Усі файли",

        # tabs
        "tab_overview": "Огляд",
        "tab_mod_health": "Стан модів",
        "tab_errors": "Помилки",
        "tab_warnings": "Попередження",
        "tab_suggestions": "Пропозиції",
        "tab_raw": "Сирий лог",

        # overview
        "overview_title": "Огляд Stardew Valley / SMAPI",
        "overview_game_version": "Версія гри",
        "overview_smapi_version": "Версія SMAPI",
        "overview_unknown": "Невідомо",
        "overview_summary": "Підсумок",
        "overview_mod_count": "Завантажено модів: {count}",
        "overview_content_pack_count": "Завантажено паків контенту: {count}",
        "overview_error_count": "Помилок: {count}",
        "overview_warning_count": "Попереджень: {count}",
        "overview_slow_start": "Час запуску: {seconds:.1f} с",
        "overview_hint": "Порада: спершу виправте помилки, потім попередження, а вже тоді косметичні дрібниці.",

        # mod health
        "mod_health_title": "Стан і ризики модів",
        "mod_health_patched_header": "Моди, що змінюють код гри (підвищений ризик):",
        "mod_health_save_header": "Моди, що змінюють серіалізацію збережень (не видаляйте під час проходження):",
        "mod_health_console_header": "Моди з прямим доступом до консолі:",
        "mod_health_missing_dep_header": "Моди з відсутніми залежностями:",
        "mod_health_missing_dep_item": "{mod} → відсутнє: {missing}",
        "mod_health_none": "У цьому логу не знайдено ризикованих модів.",
        "mod_health_updates_header": "Моди з доступними оновленнями:",
        "mod_health_update_item": "{name} {current} → {latest}",

        # errors
        "errors_header": "Помилки в цьому логу",
        "errors_none": "Помилок SMAPI не виявлено. 🎉",
        "errors_intro": "Найважливіші проблеми, про які повідомляє SMAPI:",

        # warnings
        "warnings_header": "Попередження",
        "warnings_none": "Попереджень не знайдено.",
        "warnings_intro": "Вони можуть не зламати гру одразу, але варто звернути увагу:",

        # suggestions
        "suggestions_header": "Рекомендовані дії",
        "suggestions_none": "Немає автоматичних пропозицій. Якщо гра й далі глючить, перегляньте вкладки Помилки/Попередження.",

        # raw
        "raw_header": "Повний лог SMAPI",

        # generic issues
        "warn_rivatuner": "Виявлено RivaTuner Statistics Server. Він може спричиняти збої зі SMAPI; додайте виключення або вимкніть його.",

        # suggestion types
        "sg.skipped_mod": "Виправте мод \"{name}\": SMAPI пропустив його (причина: {reason}). Відкрийте його теку та переконайтеся, що manifest.json коректний і сумісний із вашою версією гри/SMAPI.",
        "sg.failed_mod": "Виправте мод \"{name}\": SMAPI не зміг його завантажити (причина: {reason}). Перевірте інструкцію з установки на сторінці мода та за потреби перевстановіть.",
        "sg.missing_dep": "Встановіть потрібну залежність \"{missing}\" для \"{mod}\" або вимкніть мод, якщо він не потрібен.",
        "sg.save_serializer": "\"{mod}\" змінює серіалізатор збережень. Зробіть резервні копії та не видаляйте цей мод посеред проходження.",
        "sg.patched_mods_many": "У вас багато модів, що змінюють код гри ({count}). Якщо трапляються дивні збої, спробуйте вимикати утиліти/FX по одному.",
        "sg.rivatuner": "RivaTuner Statistics Server може конфліктувати зі SMAPI. Додайте виключення для Stardew Valley або закрийте програму під час гри.",
        "sg.updates": "Доступно {count} оновлень модів. Оновлення фреймворків і базових модів часто усуває збої та приховані проблеми.",
        "sg.slow_start": "Запуск гри зайняв приблизно {seconds:.1f} с. Великі пакети контенту та важкі моди збільшують час завантаження; за потреби скоротіть список модів.",
    },
}


# =========================
# Data classes
# =========================

@dataclass
class SkippedMod:
    name: str
    reason: str


@dataclass
class MissingDependency:
    mod_name: str
    missing: str


@dataclass
class UpdateInfo:
    name: str
    latest: str
    current: str
    url: str


@dataclass
class SmapiAnalysis:
    game_version: Optional[str] = None
    smapi_version: Optional[str] = None
    mod_count: int = 0
    content_pack_count: int = 0
    skipped_mods: List[SkippedMod] = field(default_factory=list)
    failed_mods: List[SkippedMod] = field(default_factory=list)
    save_serializer_mods: List[str] = field(default_factory=list)
    patched_mods: List[str] = field(default_factory=list)
    direct_console_mods: List[str] = field(default_factory=list)
    missing_dependencies: List[MissingDependency] = field(default_factory=list)
    external_conflicts: List[str] = field(default_factory=list)
    update_infos: List[UpdateInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    slow_start_seconds: Optional[float] = None
    raw_log: str = ""


# =========================
# Parsing logic
# =========================

def _parse_time_to_seconds(time_str: str) -> Optional[float]:
    # format like 00:00:14.3893574
    try:
        parts = time_str.split(":")
        if len(parts) != 3:
            return None
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    except Exception:
        return None


def analyze_smapi_log(text: str) -> SmapiAnalysis:
    analysis = SmapiAnalysis(raw_log=text)
    lines = text.splitlines()

    current_loading_mod: Optional[str] = None
    in_skipped_section = False
    in_save_serializer_section = False
    in_patched_section = False
    in_console_section = False

    for line in lines:
        # Versions
        if "SMAPI" in line and "with Stardew Valley" in line:
            m = re.search(r"SMAPI\s+([0-9.]+)\s+with Stardew Valley\s+([0-9.]+)", line)
            if m:
                analysis.smapi_version = m.group(1)
                analysis.game_version = m.group(2)

        # Counts
        if "Loaded" in line and "mods:" in line:
            m = re.search(r"Loaded\s+(\d+)\s+mods", line)
            if m:
                analysis.mod_count = int(m.group(1))
        if "Loaded" in line and "content packs:" in line:
            m = re.search(r"Loaded\s+(\d+)\s+content packs", line)
            if m:
                analysis.content_pack_count = int(m.group(1))

        # Startup time
        if "Instance_LoadContent() finished, elapsed =" in line:
            m = re.search(r"elapsed\s*=\s*'([^']+)'", line)
            if m:
                seconds = _parse_time_to_seconds(m.group(1))
                if seconds is not None:
                    analysis.slow_start_seconds = seconds

        # Track which mod is currently being loaded
        m_load = re.search(r"]\s+(.+?)\s+\(from\s+Mods", line)
        if m_load:
            current_loading_mod = m_load.group(1)

        # "Failed:" lines (TRACE section)
        if "Failed:" in line:
            reason = line.split("Failed:", 1)[1].strip()
            if current_loading_mod:
                analysis.failed_mods.append(SkippedMod(current_loading_mod, reason))
                # Missing dependency info
                if "requires mods which aren't installed" in reason:
                    m_dep = re.search(r"\(([^)]+)\)", reason)
                    if m_dep:
                        missing = m_dep.group(1)
                        analysis.missing_dependencies.append(
                            MissingDependency(current_loading_mod, missing)
                        )

        # Skipped mods header
        if "Skipped mods" in line:
            in_skipped_section = True
            continue

        if in_skipped_section:
            if "- " in line:
                m = re.search(r"]\s+-\s+(.+?)\s+because\s+(.+)$", line)
                if m:
                    name = m.group(1).strip()
                    reason = m.group(2).strip()
                    analysis.skipped_mods.append(SkippedMod(name, reason))
                    if "requires mods which aren't installed" in reason:
                        m_dep = re.search(r"\(([^)]+)\)", reason)
                        if m_dep:
                            analysis.missing_dependencies.append(
                                MissingDependency(name, m_dep.group(1))
                            )
            elif line.strip() == "" or "These mods could not be added" in line:
                # stay in section
                pass
            else:
                in_skipped_section = False

        # Save serializer section
        if "Changed save serializer" in line:
            in_save_serializer_section = True
            continue
        if in_save_serializer_section:
            if "- " in line:
                m = re.search(r"-\s+(.+)$", line)
                if m:
                    analysis.save_serializer_mods.append(m.group(1).strip())
            elif line.strip() == "" or "These mods change the save serializer" in line:
                pass
            else:
                in_save_serializer_section = False

        # Patched game code section
        if "Patched game code" in line:
            in_patched_section = True
            continue
        if in_patched_section:
            if "- " in line:
                m = re.search(r"-\s+(.+)$", line)
                if m:
                    analysis.patched_mods.append(m.group(1).strip())
            elif line.strip() == "" or "These mods directly change the game code" in line:
                pass
            else:
                in_patched_section = False

        # Direct console access
        if "Direct console access" in line:
            in_console_section = True
            continue
        if in_console_section:
            if "- " in line:
                m = re.search(r"-\s+(.+)$", line)
                if m:
                    analysis.direct_console_mods.append(m.group(1).strip())
            elif line.strip() == "" or "These mods access the SMAPI console window" in line:
                pass
            else:
                in_console_section = False

        # External conflicts (RivaTuner etc.)
        if "RivaTuner Statistics Server" in line:
            analysis.external_conflicts.append("RivaTuner Statistics Server")

        # Generic SMAPI [ERROR]/[WARN] lines
        if "ERROR SMAPI" in line and "Skipped mods" not in line:
            msg = re.sub(r"^\[.*?\]\s*", "", line).strip()
            if msg:
                analysis.errors.append(msg)
        if "WARN  SMAPI" in line and "Changed save serializer" not in line:
            msg = re.sub(r"^\[.*?\]\s*", "", line).strip()
            if msg:
                analysis.warnings.append(msg)

        # Update infos (alert details)
        if "ALERT SMAPI" in line and "You can update" not in line:
            m = re.search(r"]\s+(.+?)\s+([0-9.]+):\s+(\S+)\s+\(you have\s+([0-9.]+)\)", line)
            if m:
                name = m.group(1).strip()
                latest = m.group(2).strip()
                url = m.group(3).strip()
                current = m.group(4).strip()
                analysis.update_infos.append(
                    UpdateInfo(name=name, latest=latest, current=current, url=url)
                )

    return analysis


# =========================
# Suggestions builder
# =========================

def build_suggestions(analysis: SmapiAnalysis, lang: str) -> List[str]:
    t = lambda key, **kw: TEXT[lang][key].format(**kw)
    suggestions: List[str] = []

    # Skipped mods
    for sm in analysis.skipped_mods:
        suggestions.append(t("sg.skipped_mod", name=sm.name, reason=sm.reason))

    # Failed mods
    for fm in analysis.failed_mods:
        suggestions.append(t("sg.failed_mod", name=fm.name, reason=fm.reason))

    # Missing dependencies
    for dep in analysis.missing_dependencies:
        suggestions.append(t("sg.missing_dep", mod=dep.mod_name, missing=dep.missing))

    # Save serializer
    for mname in analysis.save_serializer_mods:
        suggestions.append(t("sg.save_serializer", mod=mname))

    # Many patched mods
    if len(analysis.patched_mods) >= 15:
        suggestions.append(t("sg.patched_mods_many", count=len(analysis.patched_mods)))

    # External conflicts
    if any("RivaTuner" in x for x in analysis.external_conflicts):
        suggestions.append(t("sg.rivatuner"))

    # Updates
    if analysis.update_infos:
        suggestions.append(t("sg.updates", count=len(analysis.update_infos)))

    # Slow startup
    if analysis.slow_start_seconds and analysis.slow_start_seconds > 20:
        suggestions.append(t("sg.slow_start", seconds=analysis.slow_start_seconds))

    return suggestions


# =========================
# Helpers: SMAPI dir + config
# =========================

def detect_smapi_log_dir() -> Optional[str]:
    """
    Try to auto-detect the SMAPI ErrorLogs folder.
    Windows: %APPDATA%\StardewValley\ErrorLogs
    Linux:   ~/.local/share/StardewValley/ErrorLogs
    macOS:   ~/Library/Application Support/StardewValley/ErrorLogs
    """
    candidates: List[str] = []

    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            candidates.append(os.path.join(appdata, "StardewValley", "ErrorLogs"))
    else:
        home = os.path.expanduser("~")
        candidates.append(
            os.path.join(home, "Library", "Application Support", "StardewValley", "ErrorLogs")
        )
        candidates.append(
            os.path.join(home, ".local", "share", "StardewValley", "ErrorLogs")
        )

    for path in candidates:
        if os.path.isdir(path):
            return path

    return None


# =========================
# Tkinter UI app
# =========================

class SmapiLogDoctorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang = "en"
        self.analysis: Optional[SmapiAnalysis] = None
        self.current_path: Optional[str] = None

        # remember last folder + language
        self.config_path = self._compute_config_path()
        self.last_dir: Optional[str] = None
        self._load_config()

        # language dropdown options: (code, label)
        self.lang_options = [
            ("en", "EN"),
            ("zh", "中文"),
            ("ru", "RU"),
            ("pt", "PT"),
            ("es", "ES"),
            ("fr", "FR"),
            ("de", "DE"),
            ("it", "IT"),
            ("ja", "日本語"),
            ("ko", "한국어"),
            ("pl", "PL"),
            ("pt-BR", "PT-BR"),
            ("tr", "TR"),
            ("uk", "UA"),
        ]
        self.lang_var = tk.StringVar()

        self.root.title(TEXT[self.lang]["app_title"])
        self.root.geometry("1000x700")

        self._build_ui()

    # ---------- Config helpers ----------

    def _compute_config_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        return os.path.join(base_dir, "smapi_log_doctor_config.json")

    def _load_config(self) -> None:
        try:
            if os.path.isfile(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                lang = data.get("lang")
                if lang in TEXT:
                    self.lang = lang
                last_dir = data.get("last_dir")
                if last_dir and os.path.isdir(last_dir):
                    self.last_dir = last_dir
        except Exception:
            # ignore config errors, fall back to defaults
            pass

    def _save_config(self) -> None:
        data = {
            "lang": self.lang,
            "last_dir": self.last_dir,
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            # don't crash app on save failure
            pass

    # ---------- Translation helper ----------

    def _t(self, key: str, **kwargs) -> str:
        return TEXT[self.lang][key].format(**kwargs)

    # ---------- UI building ----------

    def _build_ui(self) -> None:
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side="top", fill="x", padx=4, pady=4)

        self.btn_open = ttk.Button(toolbar, text=self._t("btn_open"), command=self.open_log)
        self.btn_open.pack(side="left")

        self.btn_export = ttk.Button(toolbar, text=self._t("btn_export"), command=self.export_summary)
        self.btn_export.pack(side="left", padx=(4, 0))

        # Language dropdown (right side)
        lang_frame = ttk.Frame(toolbar)
        lang_frame.pack(side="right")

        self.lang_label = ttk.Label(lang_frame, text=self._t("label_language"))
        self.lang_label.pack(side="left", padx=(0, 4))

        # set initial dropdown label from current lang code
        initial_label = next(
            (label for code, label in self.lang_options if code == self.lang),
            "EN",
        )
        self.lang_var.set(initial_label)

        self.lang_combobox = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            state="readonly",
            values=[label for _, label in self.lang_options],
            width=6,
        )
        self.lang_combobox.pack(side="left")
        self.lang_combobox.bind("<<ComboboxSelected>>", self._on_lang_selected)

        # Notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=4)

        self.overview_text = self._create_text_tab("tab_overview")
        self.mod_health_text = self._create_text_tab("tab_mod_health")
        self.errors_text = self._create_text_tab("tab_errors")
        self.warnings_text = self._create_text_tab("tab_warnings")
        self.suggestions_text = self._create_text_tab("tab_suggestions")
        self.raw_log_text = self._create_text_tab("tab_raw")

        # Status bar
        self.status_var = tk.StringVar(value=self._t("status_ready"))
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def _create_text_tab(self, title_key: str) -> tk.Text:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=self._t(title_key))

        text = tk.Text(
            frame,
            wrap="word",
            font=("Consolas", 10),
            undo=False,
        )
        text.pack(fill="both", expand=True)
        self._configure_text_tags(text)
        text.config(state="disabled")
        return text

    def _configure_text_tags(self, text: tk.Text) -> None:
        text.tag_configure(
            "header",
            font=("Consolas", 11, "bold"),
            spacing3=6,
        )
        text.tag_configure(
            "subheader",
            font=("Consolas", 10, "bold"),
            spacing3=4,
        )
        text.tag_configure(
            "error",
            foreground="#d22",
        )
        text.tag_configure(
            "warning",
            foreground="#b36b00",
        )
        text.tag_configure(
            "info",
            foreground="#005caa",
        )
        text.tag_configure(
            "bullet",
            lmargin1=20,
            lmargin2=20,
        )
        text.tag_configure(
            "muted",
            foreground="#666666",
        )
        text.tag_configure(
            "emphasis",
            font=("Consolas", 10, "italic"),
        )

    # ---------- Language dropdown logic ----------

    def _on_lang_selected(self, event=None) -> None:
        label = self.lang_var.get()
        for code, lbl in self.lang_options:
            if lbl == label:
                self.set_language(code)
                break

    def set_language(self, lang: str) -> None:
        if lang == self.lang:
            return
        self.lang = lang
        self.root.title(TEXT[self.lang]["app_title"])
        # Update button labels & tab titles
        self.btn_open.config(text=self._t("btn_open"))
        self.btn_export.config(text=self._t("btn_export"))

        if hasattr(self, "lang_label"):
            self.lang_label.config(text=self._t("label_language"))

        # Update dropdown label if needed
        if hasattr(self, "lang_var"):
            label = next((lbl for code, lbl in self.lang_options if code == self.lang), "EN")
            self.lang_var.set(label)

        # Re-label tabs
        for tab, key in zip(
            self.notebook.tabs(),
            [
                "tab_overview",
                "tab_mod_health",
                "tab_errors",
                "tab_warnings",
                "tab_suggestions",
                "tab_raw",
            ],
        ):
            self.notebook.tab(tab, text=self._t(key))

        # Rerender content
        if self.analysis:
            self.render_all()
            if self.current_path:
                self.status_var.set(self._t("status_loaded", path=self.current_path))
        else:
            self.status_var.set(self._t("status_ready"))

        # remember language
        self._save_config()

    # ---------- File handling ----------

    def _get_initial_open_dir(self) -> str:
        # 1) last folder if still exists
        if self.last_dir and os.path.isdir(self.last_dir):
            return self.last_dir

        # 2) auto-detected SMAPI ErrorLogs folder
        detected = detect_smapi_log_dir()
        if detected:
            return detected

        # 3) fallback: home directory
        return os.path.expanduser("~")

    def open_log(self) -> None:
        initial_dir = self._get_initial_open_dir()
        path = filedialog.askopenfilename(
            title=self._t("dialog_select_log_title"),
            filetypes=[
                (self._t("filetype_text"), "*.txt"),
                (self._t("filetype_all"), "*.*"),
            ],
            initialdir=initial_dir,
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror(
                self._t("dialog_error_title"),
                self._t("dialog_read_fail", error=e),
            )
            return

        try:
            self.analysis = analyze_smapi_log(text)
        except Exception as e:
            messagebox.showerror(
                self._t("dialog_error_title"),
                self._t("dialog_analyze_fail", error=e),
            )
            return

        self.current_path = path
        # remember folder for next time
        self.last_dir = os.path.dirname(path)
        self._save_config()

        self.render_all()
        self.status_var.set(self._t("status_loaded", path=path))

    def export_summary(self) -> None:
        if not self.analysis:
            messagebox.showinfo(
                self._t("dialog_info_title"), self._t("status_no_analysis")
            )
            return
        path = filedialog.asksaveasfilename(
            title=self._t("dialog_export_title"),
            defaultextension=".txt",
            filetypes=[(self._t("filetype_text"), "*.txt")],
        )
        if not path:
            return

        try:
            summary_text = self._build_plain_summary()
            with open(path, "w", encoding="utf-8") as f:
                f.write(summary_text)
            self.status_var.set(self._t("status_export_ok", path=path))
        except Exception as e:
            self.status_var.set(self._t("status_export_fail", error=e))

    # ---------- Rendering ----------

    def _clear_and_enable(self, text: tk.Text) -> None:
        text.config(state="normal")
        text.delete("1.0", tk.END)

    def render_all(self) -> None:
        if not self.analysis:
            return
        self._render_overview()
        self._render_mod_health()
        self._render_errors()
        self._render_warnings()
        self._render_suggestions()
        self._render_raw()

    def _render_overview(self) -> None:
        a = self.analysis
        t = self._t
        text = self.overview_text
        self._clear_and_enable(text)

        text.insert(tk.END, t("overview_title") + "\n", ("header",))

        # Versions
        text.insert(
            tk.END,
            f"{t('overview_game_version')}: {a.game_version or t('overview_unknown')}\n",
            ("info",),
        )
        text.insert(
            tk.END,
            f"{t('overview_smapi_version')}: {a.smapi_version or t('overview_unknown')}\n\n",
            ("info",),
        )

        # Summary
        text.insert(tk.END, t("overview_summary") + "\n", ("subheader",))

        text.insert(
            tk.END,
            "• " + t("overview_mod_count", count=a.mod_count) + "\n",
            ("bullet",),
        )
        text.insert(
            tk.END,
            "• " + t("overview_content_pack_count", count=a.content_pack_count) + "\n",
            ("bullet",),
        )
        text.insert(
            tk.END,
            "• " + t("overview_error_count", count=len(a.errors)) + "\n",
            ("bullet", "error") if a.errors else ("bullet",),
        )
        text.insert(
            tk.END,
            "• " + t("overview_warning_count", count=len(a.warnings)) + "\n",
            ("bullet", "warning") if a.warnings else ("bullet",),
        )
        if a.slow_start_seconds is not None:
            text.insert(
                tk.END,
                "• " + t("overview_slow_start", seconds=a.slow_start_seconds) + "\n",
                ("bullet", "muted"),
            )

        text.insert(tk.END, "\n" + t("overview_hint") + "\n", ("muted",))

        text.config(state="disabled")

    def _render_mod_health(self) -> None:
        a = self.analysis
        t = self._t
        text = self.mod_health_text
        self._clear_and_enable(text)

        text.insert(tk.END, t("mod_health_title") + "\n", ("header",))

        sections_written = False

        # Patched game code
        if a.patched_mods:
            sections_written = True
            text.insert(
                tk.END, "\n" + t("mod_health_patched_header") + "\n", ("subheader",)
            )
            for m in a.patched_mods:
                text.insert(
                    tk.END,
                    "• " + m + "\n",
                    ("bullet", "warning"),
                )

        # Save serializer
        if a.save_serializer_mods:
            sections_written = True
            text.insert(
                tk.END, "\n" + t("mod_health_save_header") + "\n", ("subheader",)
            )
            for m in a.save_serializer_mods:
                text.insert(
                    tk.END,
                    "• " + m + "\n",
                    ("bullet", "error"),
                )

        # Direct console access
        if a.direct_console_mods:
            sections_written = True
            text.insert(
                tk.END,
                "\n" + t("mod_health_console_header") + "\n",
                ("subheader",),
            )
            for m in a.direct_console_mods:
                text.insert(
                    tk.END,
                    "• " + m + "\n",
                    ("bullet", "muted"),
                )

        # Missing dependencies
        if a.missing_dependencies:
            sections_written = True
            text.insert(
                tk.END,
                "\n" + t("mod_health_missing_dep_header") + "\n",
                ("subheader",),
            )
            for dep in a.missing_dependencies:
                text.insert(
                    tk.END,
                    "• "
                    + t(
                        "mod_health_missing_dep_item",
                        mod=dep.mod_name,
                        missing=dep.missing,
                    )
                    + "\n",
                    ("bullet", "error"),
                )

        # Updates
        if a.update_infos:
            sections_written = True
            text.insert(
                tk.END,
                "\n" + t("mod_health_updates_header") + "\n",
                ("subheader",),
            )
            for u in a.update_infos:
                text.insert(
                    tk.END,
                    "• "
                    + t(
                        "mod_health_update_item",
                        name=u.name,
                        current=u.current,
                        latest=u.latest,
                    )
                    + "\n",
                    ("bullet", "info"),
                )

        if not sections_written:
            text.insert(tk.END, "\n" + t("mod_health_none") + "\n", ("muted",))

        text.config(state="disabled")

    def _render_errors(self) -> None:
        a = self.analysis
        t = self._t
        text = self.errors_text
        self._clear_and_enable(text)

        text.insert(tk.END, t("errors_header") + "\n", ("header",))

        if not a.errors and not a.skipped_mods and not a.failed_mods:
            text.insert(tk.END, t("errors_none") + "\n", ("info",))
            text.config(state="disabled")
            return

        text.insert(tk.END, t("errors_intro") + "\n\n", ("muted",))

        # Skipped / failed mods as "hard errors"
        for sm in a.skipped_mods:
            text.insert(
                tk.END,
                f"• [Skipped] {sm.name} — {sm.reason}\n",
                ("bullet", "error"),
            )
        for fm in a.failed_mods:
            text.insert(
                tk.END,
                f"• [Failed] {fm.name} — {fm.reason}\n",
                ("bullet", "error"),
            )

        # Raw ERROR lines
        for e in a.errors:
            text.insert(
                tk.END,
                "• " + e + "\n",
                ("bullet", "error"),
            )

        text.config(state="disabled")

    def _render_warnings(self) -> None:
        a = self.analysis
        t = self._t
        text = self.warnings_text
        self._clear_and_enable(text)

        text.insert(tk.END, t("warnings_header") + "\n", ("header",))

        if not a.warnings and not a.external_conflicts:
            text.insert(tk.END, t("warnings_none") + "\n", ("info",))
            text.config(state="disabled")
            return

        text.insert(tk.END, t("warnings_intro") + "\n\n", ("muted",))

        for w in a.warnings:
            text.insert(
                tk.END,
                "• " + w + "\n",
                ("bullet", "warning"),
            )

        # External conflicts like RivaTuner
        for x in a.external_conflicts:
            if "RivaTuner" in x:
                text.insert(
                    tk.END,
                    "• " + TEXT[self.lang]["warn_rivatuner"] + "\n",
                    ("bullet", "warning"),
                )

        text.config(state="disabled")

    def _render_suggestions(self) -> None:
        a = self.analysis
        text = self.suggestions_text
        self._clear_and_enable(text)

        t = self._t
        text.insert(tk.END, t("suggestions_header") + "\n", ("header",))

        suggestions = build_suggestions(a, self.lang)
        if not suggestions:
            text.insert(tk.END, t("suggestions_none") + "\n", ("info",))
            text.config(state="disabled")
            return

        for s in suggestions:
            # Light severity coloring heuristic
            tags = ["bullet"]
            if ("save" in s.lower() or "存档" in s or "сейв" in s.lower() or "salva" in s.lower()):
                tags.append("error")
            elif ("update" in s.lower() or "更新" in s or "обнов" in s.lower() or "atualiz" in s.lower()):
                tags.append("info")
            elif "RivaTuner" in s:
                tags.append("warning")

            text.insert(tk.END, "• " + s + "\n\n", tuple(tags))

        text.config(state="disabled")

    def _render_raw(self) -> None:
        a = self.analysis
        t = self._t
        text = self.raw_log_text
        self._clear_and_enable(text)

        text.insert(tk.END, t("raw_header") + "\n\n", ("header",))
        text.insert(tk.END, a.raw_log)
        text.config(state="disabled")

    # ---------- Export summary (plain text) ----------

    def _build_plain_summary(self) -> str:
        if not self.analysis:
            return ""
        a = self.analysis
        t = self._t

        parts: List[str] = []

        parts.append(t("overview_title"))
        parts.append("=" * 60)
        parts.append(f"{t('overview_game_version')}: {a.game_version or t('overview_unknown')}")
        parts.append(f"{t('overview_smapi_version')}: {a.smapi_version or t('overview_unknown')}")
        parts.append(t("overview_mod_count", count=a.mod_count))
        parts.append(t("overview_content_pack_count", count=a.content_pack_count))
        if a.slow_start_seconds is not None:
            parts.append(t("overview_slow_start", seconds=a.slow_start_seconds))
        parts.append("")

        # Errors
        parts.append(t("errors_header"))
        parts.append("-" * 60)
        if not a.errors and not a.skipped_mods and not a.failed_mods:
            parts.append(t("errors_none"))
        else:
            for sm in a.skipped_mods:
                parts.append(f"[Skipped] {sm.name} — {sm.reason}")
            for fm in a.failed_mods:
                parts.append(f"[Failed] {fm.name} — {fm.reason}")
            for e in a.errors:
                parts.append(e)
        parts.append("")

        # Warnings
        parts.append(t("warnings_header"))
        parts.append("-" * 60)
        if not a.warnings and not a.external_conflicts:
            parts.append(t("warnings_none"))
        else:
            for w in a.warnings:
                parts.append(w)
            for x in a.external_conflicts:
                if "RivaTuner" in x:
                    parts.append(TEXT[self.lang]["warn_rivatuner"])
        parts.append("")

        # Mod health
        parts.append(t("mod_health_title"))
        parts.append("-" * 60)

        if a.patched_mods:
            parts.append(t("mod_health_patched_header"))
            for m in a.patched_mods:
                parts.append("  - " + m)
        if a.save_serializer_mods:
            parts.append(t("mod_health_save_header"))
            for m in a.save_serializer_mods:
                parts.append("  - " + m)
        if a.direct_console_mods:
            parts.append(t("mod_health_console_header"))
            for m in a.direct_console_mods:
                parts.append("  - " + m)
        if a.missing_dependencies:
            parts.append(t("mod_health_missing_dep_header"))
            for dep in a.missing_dependencies:
                parts.append(
                    "  - "
                    + t(
                        "mod_health_missing_dep_item",
                        mod=dep.mod_name,
                        missing=dep.missing,
                    )
                )
        if a.update_infos:
            parts.append(t("mod_health_updates_header"))
            for u in a.update_infos:
                parts.append(
                    "  - "
                    + t(
                        "mod_health_update_item",
                        name=u.name,
                        current=u.current,
                        latest=u.latest,
                    )
                )

        if (
            not a.patched_mods
            and not a.save_serializer_mods
            and not a.direct_console_mods
            and not a.missing_dependencies
            and not a.update_infos
        ):
            parts.append(t("mod_health_none"))
        parts.append("")

        # Suggestions
        parts.append(t("suggestions_header"))
        parts.append("-" * 60)
        suggestions = build_suggestions(a, self.lang)
        if not suggestions:
            parts.append(t("suggestions_none"))
        else:
            for s in suggestions:
                parts.append(" - " + s)
        parts.append("")

        return "\n".join(parts)


# =========================
# Main entry
# =========================

def main() -> None:
    root = tk.Tk()
    app = SmapiLogDoctorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

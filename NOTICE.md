# Происхождение и лицензии / Provenance

| Компонент | Включённая версия | Оригинальный проект | Назначение |
| --- | --- | --- | --- |
| KRdp | 6.7.4 | https://invent.kde.org/plasma/krdp | RDP transport, graphics, input, redirection |
| Plasma Login Manager | 6.7.4 | https://invent.kde.org/plasma/plasma-login-manager | PAM login and persistent user sessions |
| KPipeWire | 6.7.4 | https://invent.kde.org/plasma/kpipewire | Capture and software encoding |
| Apache Guacamole Server | 1.6.0 | https://github.com/apache/guacamole-server | Optional browser gateway/display fix |

`upstream/` содержит неизменённые содержательные файлы официальных source-архивов.
Список архивов и их SHA-256 — `upstream-sources.json`, контрольные суммы каждого
включённого файла — `upstream-files.sha256`.
`upstream-links.json` фиксирует цели включённых символических ссылок.
Изменяемая копия создаётся скриптом
`scripts/prepare.py`; оригинальные деревья не редактируются.

Единственное изменение раскладки хранения — upstream `.gitattributes` хранится
в `upstream-metadata/` и возвращается на исходное место в подготовленной копии.
Это предотвращает применение upstream `export-ignore` к GitHub ZIP/tar download.
Содержимое не изменено; отображение путей записано в `upstream-metadata.json`,
проверка использует прежние SHA-256 оригинальных файлов.

Сборка рабочего стенда начиналась с Debian source packages
`krdp=6.7.4-1`, `plasma-login-manager=6.7.4-3`, `kpipewire=6.7.4-1`.
В публикации используются оригинальные source-архивы этих версий и полная
восстановленная серия локальных изменений. Перед публикацией полученные
из этой серии C/C++-исходники сверены с исходниками рабочей сборки.

## Лицензионные границы

- Файлы KRdp имеют собственные SPDX-заголовки: в том числе LGPL-2.1-only OR
  LGPL-3.0-only OR LicenseRef-KDE-Accepted-LGPL, а `VideoStream.cpp` —
  GPL-2.0-or-later. Сохраняются все исходные заголовки и `LICENSES/`.
- Файлы Plasma Login Manager сохраняют исходные GPL/LGPL/BSD и другие лицензии,
  перечисленные непосредственно в дереве компонента. Изменяемый `Display.cpp`
  — GPL-2.0-or-later.
- Изменяемые файлы KPipeWire — LGPL-2.1-only OR LGPL-3.0-only OR
  LicenseRef-KDE-Accepted-LGPL. Полные тексты оставлены в исходном дереве.
- Guacamole и патч его `display-layer.c` — Apache-2.0. Оригинальные `LICENSE`
  и `NOTICE` сохранены в `upstream/guacamole-server-1.6.0/`.
- Локальные изменения файлов upstream распространяются на условиях соответствующих
  изменяемых файлов. Лицензия корня не перелицензирует их.
- Только новый самостоятельный код в `runtime/`, `scripts/`, `tests/` и новая
  документация этого репозитория распространяются по MIT из корня.

Патчи могут затрагивать файлы с разными лицензиями; смотрите соответствующие
оригинальные файлы в `upstream/`, а не только расширение `.patch`.

## Зависимости и заимствования

FreeRDP (https://github.com/FreeRDP/FreeRDP), Qt, KDE Frameworks, KWin, PipeWire,
FFmpeg, Cairo и системные пакеты используются как зависимости. Их библиотеки
и бинарные файлы не включены в публикацию. Их собственные лицензии применяются
при сборке/распространении соответствующих компонентов.

KRdp `VideoStream.cpp` уже содержит признание GNOME Remote Desktop и Pascal
Nowack в исходном авторском заголовке. Оно сохранено. Этот проект не заявляет
авторство исходного RDP-стека, композитора, кодеков или менеджера входа.

Авторство локальной разработки ChatGPT/Codex и роль владельца стенда указаны
в [AUTHORS.md](AUTHORS.md). Локальная серия не заявляется принятой upstream.

# Plasma RDP Terminal Server — experimental lab

An experimental KDE Plasma terminal-server prototype: one RDP endpoint,
Plasma Login Manager authentication, separate persistent Wayland sessions,
reconnection to running applications, and dynamic display resolution.

Экспериментальный сервер сеансов KDE Plasma: один RDP-адрес, вход через
Plasma Login Manager без автологина, отдельные Wayland-сеансы и возврат к
открытым приложениям после обрыва. Это исследовательский стенд, пока не готовое
решение для эксплуатации в сети.

## Основа и авторство / Upstream and authorship

Основа — **KDE KRdp 6.7.4**, **Plasma Login Manager 6.7.4**,
**KPipeWire 6.7.4**, **FreeRDP** и **Apache Guacamole 1.6.0**.
Полные исходники четырёх изменяемых компонентов включены в `upstream/`.
Версии, ссылки на оригинальные архивы и SHA-256 записаны в
[upstream-sources.json](upstream-sources.json). Авторские заголовки и лицензии
оригинальных проектов сохранены.

**Доработки этого стенда, диагностика, патчи, интеграционные скрипты и инструкции
подготовлены ChatGPT/Codex (OpenAI) по заданию Владимира Гурьева
([babah1983](https://github.com/babah1983)).** Владимир сформулировал требования,
предоставил стенд и участвовал в клиентских испытаниях. Код сгенерирован и
изменён AI-ассистентом; независимая проверка человеком не заявляется.

The integration and modifications in this repository were implemented by
ChatGPT/Codex (OpenAI), at Vladimir Guriev's request. Upstream KDE, GNOME,
FreeRDP and Apache authors retain credit for their original work. This is an
independent experiment, not an official KDE or OpenAI product.

[Подробное происхождение и лицензии](NOTICE.md) · [Участники и роли](AUTHORS.md)

## Что добавлено

- Системный RDP-диспетчер с одноразовой маршрутизацией после PAM-входа.
- Headless greeter и два отдельных виртуальных сеанса KWin, `native-a` и `native-b`.
- Повторное подключение к существующему сеансу вместо перезапуска приложений.
- RDP Display Control и реальное изменение режима виртуального экрана KWin.
- Исправления времени жизни кадров и пула буферов программного энкодера KPipeWire.
- Исправление потерянных уведомлений рабочих потоков KPipeWire при остановке и смене разрешения; [диагностика ALT K](docs/ALT-K-RESIZE-FIX.md).
- Работа с PipeWire из потока владельца, полный первый Progressive-кадр,
  сохранение кадра при backpressure и отбрасывание старых поколений захвата.
- Исправление инвалидации заменяемого внешнего буфера Guacamole/libguac.

## Сборка и проверка

[Инструкция для Debian sid](docs/BUILD.md) · [Архитектура и ограничения](docs/ARCHITECTURE.md)
· [Проверки и известные проблемы](docs/TESTING.md)
· [Проверка публикационной сборки](docs/BUILD-VERIFICATION.md)
· [Матрица дистрибутивов: ARM64 и будущий этап x86_64](docs/DISTRIBUTIONS.md)

Короткий путь **только для сборки**, без установки и перезапуска служб:

```sh
python3 scripts/prepare.py
bash scripts/build-kde.sh
bash scripts/stage-kde.sh
bash scripts/check-regressions.sh
```

`prepare.py` проверяет контрольные суммы исходников, копирует их в
`build/sources/` и применяет патчи. Отдельный каталог `build/stage/` содержит
готовый набор файлов для проверки перед установкой. Зависимости и применение
конфигурации описаны в инструкции; команды выше не устанавливают зависимости.

## Состояние

Испытано в отдельной ARM64 ВМ UTM на Debian sid. Проверены Windows App и
Guacamole. Последний отдельный часовой прогон: два одновременных сеанса,
шесть TCP-обрывов, возврат к несохранённым документам Kate и смены разрешения.

Постоянные чёрные/устаревшие области в проверенном пути Guacamole устранены.
Один неполный переходный кадр восстановился самостоятельно; полностью
бесшовный resize не заявляется. Медиана активного RSS за час выросла на
3,57 МиБ в A и 10,16 МиБ в B; отключённый уровень после трёх обрывов не рос.
Отсутствие всех утечек памяти не доказано. [Числа и границы проверки](docs/TESTING.md).

Пока используются два заданных Linux-пользователя, один общий greeter и общий
тестовый транспортный секрет. Последовательность входа в greeter обслуживается
по одному клиенту. Внутренние порты закрыты для обычных процессов гостя и
слушают только loopback. Прямое открытие этих портов в LAN/Internet не проверено.

В репозитории нет образов ВМ, рабочих паролей, сертификатов/ключей стенда,
сетевых реквизитов или сырых эксплуатационных журналов.

## Лицензии

Новый самостоятельный интеграционный код и документация — [MIT](LICENSE).
Исходники и изменения файлов KDE сохраняют соответствующие GPL/LGPL/BSD-лицензии;
Guacamole — Apache-2.0. MIT не заменяет лицензии upstream. См. [NOTICE.md](NOTICE.md).

# ALT «Рабочая станция К» 11.4 → 11.5 x86_64 / Proxmox VE

> Повторная диагностика и исправления зависания при resize: [ALT-K-RESIZE-FIX.md](ALT-K-RESIZE-FIX.md). Ниже сохранены условия первого прогона; раздел с результатами первоначального теста не является результатом повторной проверки.

## Установочный образ и ВМ

Использован официальный установочный ISO `alt-kworkstation-11.4-install-x86_64.iso`
со [страницы BaseALT](https://www.basealt.ru/alt-workstation-k/download),
сборка 11 июня 2026 года. Опубликованные MD5 и SHA1 совпали; дополнительно
записан SHA-256:
`2529f98bca03a652709434a6a17cd4aac5df20c0793927abdf784e8f9388243a`.
Это проверка сумм и загрузки через HTTPS, а не проверка PGP-подписи ISO.

Отдельная ВМ: OVMF EFI, VirtIO SCSI, один диск 48 ГиБ, 4 ГиБ RAM,
4 vCPU с ограничением CPU до двух ядер, VirtIO GPU и сеть, balloon выключен.
Установлен штатный профиль Workstation с рекомендованной Plasma.
Разметка Timeshift-compatible: EFI 511 МиБ, swap 128 МиБ, Btrfs p3
около 47 ГиБ с подтомами `@` и `@home`. Автологин выключен.

На ISO: Plasma/KRdp 6.6.5, Qt 6.10.3, KF6 CoreAddons 6.26.
Для сборки прототипа нужны более новые компоненты Plasma; использована
только ветка **p11**, без подключения Sisyphus.

## Особенности подготовки p11

Сохранены исходные каналы x86_64 `classic gostcrypto`, x86_64-i586 `classic`
и noarch `classic`; для загрузки использовано HTTPS-зеркало
`https://mirror.truenetwork.ru/altlinux`. Штатная проверка пакетов сохранена.

Список BuildRequires взят из SRPM KRdp, PLM и KPipeWire 6.7.5 ветки p11.
Служебные требования `rpmlib(...)` из списка исключаются перед передачей APT.
Список сохранён в [srpm-build-requirements.txt](evidence/alt-workstation-k-x86_64/srpm-build-requirements.txt).
Дополнительно нужны CMake, make, gcc-c++, Python, patch, git, gettext-tools,
libffi-devel, nftables, PipeWire/WirePlumber и `plasma6-libkscreen-utils`.

**Сначала проверяйте симуляцию APT.** На свежем ISO первоначальный план
предлагал удалить Plasma и essential-метапакеты KDE. Он не применялся.
Явное сохранение уже установленных метапакетов в той же команде установки
сохранило окружение. Возможные имена:

```text
kde kde-big kde-small kde-mini plasma-desktop plasma-workspace
```

Пример подготовки аргументов в Bash из корня репозитория (root-shell):

```bash
mapfile -t build_deps < <(grep -v '^rpmlib(' docs/evidence/alt-workstation-k-x86_64/srpm-build-requirements.txt)
packages=("${build_deps[@]}" cmake make gcc-c++ python3 patch git gettext-tools
          libffi-devel nftables pipewire wireplumber plasma6-libkscreen-utils
          plasma-login-manager krdp plasma6-integration acl)
# Сохраняем только установленные метапакеты: установка отсутствующих kde/kde-big
# существенно расширяет окружение и не нужна для сборки.
for meta in kde kde-big kde-small kde-mini plasma-desktop plasma-workspace; do
    if rpm -q "$meta" >/dev/null 2>&1; then packages+=("$meta"); fi
done
apt-get update
apt-get -s install "${packages[@]}"
# Только после проверки плана и создания снимка тестовой ВМ:
apt-get install "${packages[@]}"
```

Список BuildRequires — снимок конкретных SRPM p11, а не обещание совместимости
с будущим состоянием ветки. Если APT предлагает удаления окружения или смену
ветки, остановитесь и разберите план.

В проверенной транзакции было 368 обновлений, 160 новых пакетов и одна
замена ABI: `libprocesscore10` на `libprocesscore11`. Перед применением
создан снимок только тестовой ВМ. Это не универсальная команда для любого
состояния p11: проверяйте фактические удаления на своей системе.

После транзакции: Plasma Workspace/KWin/PLM 6.7.5, Qt 6.11.2,
KF6 CoreAddons 6.31, FreeRDP/WinPR 3.32.2, Mesa 26.1.8.
Пакет `plasma6-integration` обновлён вместе с Qt/KDE.
При последующем старте штатный PackageKit завершил offline-update и сам
перезагрузил ВМ; перед GUI-проверкой `/etc/altlinux-release` уже сообщает
**ALT Workstation K 11.5 (Nemorosa)**. Результат ниже относится к этому
обновлённому состоянию p11, а не к неизменённому ISO 11.4.

## Сборка и включение прототипа

Исходники проекта закреплены на коммите `f0483a7` (код KDE на базе 6.7.4).
Сборка выполняется обычным пользователем в приватном записываемом TMPDIR:

```sh
export LANG=C.UTF-8
export TMPDIR="$PWD/build/tmp"
install -d -m 0700 "$TMPDIR"
export PLASMA_RDP_INSTALL_PAM_CONFIGURATION=OFF
export PLASMA_RDP_LIBEXECDIR=libexec
export PLASMA_RDP_SESSION_COMMAND=/etc/X11/Xsession
export JOBS=2
python3 scripts/prepare.py --output build/alt-k-sources
bash scripts/build-kde.sh build/alt-k-sources
bash scripts/check-regressions.sh build/alt-k-sources
bash scripts/stage-kde.sh build/alt-k-sources build/alt-k-stage
```

Все три регрессии прошли, включая отрицательный контроль старого поведения
кодека. Штатные `/etc/pam.d/plasmalogin*` установлены пакетом p11 и не
заменяются PAM-конфигурацией Debian из исходников.

Для runtime использованы общие скрипты проекта и
[особенности ALT](ALT.md). LightDM отключён, включены PLM, dispatcher,
изоляция backend-портов, пользовательские PipeWire/WirePlumber.
Все три библиотеки KPipeWire каждого варианта перенесены вместе.

Первый прогон использовал VirtIO `/dev/dri/renderD128` без VGEM. Повторная
диагностика выявила отказ `CREATE_DUMB` на этом узле и остановку отрисовки
после resize. Само наличие render-node и OpenGL недостаточно для этого
программного headless-сеанса. В исправленном стенде загружается VGEM;
KWin использует его первичный узел с узким ACL для `plasma-rdp-render`.
Правило не затрагивает физические GPU. Для `/dev/udmabuf` используется
отдельный узкий ACL. Подробности и проверка буфера — в
[разборе исправления](ALT-K-RESIZE-FIX.md). Номера DRM-устройств нужно
определять по `/sys/class/drm` и дескрипторам KWin на конкретной машине.

Команды включения выполняются **в отдельной тестовой гостевой ОС**, не на
хосте PVE. Нужны заранее созданные обычные пользователи `native-a` и
`native-b` с личными паролями и приватными одноимёнными группами; PLM
должен быть установлен из p11. После сборки в root-shell проекта:

```sh
set -e
. /etc/os-release
test "$ID" = altlinux
test "$VARIANT_ID" = kworkstation
test "$ALT_BRANCH_ID" = p11
test ! -e /root/plasma-rdp-before
install -d -m 0700 /root/plasma-rdp-before
cp -a /etc/pam.d/plasmalogin* /root/plasma-rdp-before/
sha256sum /etc/pam.d/plasmalogin* > /root/plasma-rdp-before/pam.sha256
readlink /etc/systemd/system/display-manager.service > /root/plasma-rdp-before/display-manager.txt
systemctl disable --now lightdm.service
systemctl --global enable pipewire.socket wireplumber.service
groupadd -f plasma-rdp-render
for account in plasmalogin native-a native-b; do
    usermod -aG plasma-rdp-render "$account"
done
modprobe vgem
printf 'vgem\n' > /etc/modules-load.d/plasma-rdp-lab.conf
install -m 0644 runtime/altlinux/99-plasma-rdp-vgem.rules /etc/udev/rules.d/
install -m 0644 runtime/fedora/99-plasma-rdp-udmabuf.rules /etc/udev/rules.d/
udevadm control --reload-rules
# Применяем правило только к проверенному программному устройству VGEM.
for device in /sys/class/drm/card[0-9]*; do
    if grep -qx 'MODALIAS=platform:vgem' "$device/device/uevent" 2>/dev/null; then
        udevadm trigger --action=add "$device"
    fi
done
udevadm trigger --action=add /sys/class/misc/udmabuf
udevadm settle
cp -a build/alt-k-stage/opt/. /opt/
bash runtime/install-handover.sh --apply-to-disposable-vm
sha256sum -c /root/plasma-rdp-before/pam.sha256
```

Имя каталога `runtime/fedora` историческое: использованное правило задаёт
только ACL для выделенной группы и не меняет владельца или режим устройства.
Доступ к VirtIO render-node в этом образе уже разрешён штатными правами;
это нужно проверить отдельно на иной виртуальной видеокарте.
После перезагрузки проверяйте активность PLM/dispatcher/isolation и отсутствие
личных пользовательских сеансов до первого входа. Runtime слушает только
loopback гостя; для клиента используется SSH-forward к `127.0.0.1:3389`.
Первичная NLA-авторизация: имя `greeter`, приватный транспортный пароль из
`/var/lib/plasmalogin/.local/state/plasma-rdp/password`; затем PLM проверяет
личный пароль выбранного пользователя через штатный PAM/TCB. Транспортный
пароль не следует добавлять в репозиторий или публичный `.rdp`-файл.

## Результаты пользовательской проверки

21 ноября 2026 года в Windows App **11.4.1 (3092)** на macOS подтверждены:

- Вход через PLM без автологина после перезагрузки; до входа активен только greeter.
- Два независимых пользователя `native-a` и `native-b` через один frontend `127.0.0.1:3389` в госте. На Mac используется один loopback SSH-forward; названия `127.0.0.1` и `localhost` позволяют открыть два профиля клиента к одному listener.
- Два намеренных обрыва этого туннеля и повторный вход обоих пользователей через PLM. Kate, KWin и KRdp сохранили PID: A `4665/3884/3888`, B `5366/4894/4899`.
- Несохранённые `altka001` и `altkb001` остались в Kate после обоих обрывов. После второго возврата в каждом документе дописан `2`; ввод и обновляющийся счётчик Konsole видны на [снимке A](evidence/alt-workstation-k-x86_64/a-cut2.png) и [снимке B](evidence/alt-workstation-k-x86_64/b-cut2.png).
- Update session resolution on resize включён в обоих профилях. KWin через D-Bus подтвердил 1920×1080 при полном экране и оконные 960×1018/960×600; после первого возврата оба сеанса вновь достигли 1920×1080. [Геометрия и события](evidence/alt-workstation-k-x86_64/geometry-events.txt).

**Полная приёмка динамического разрешения — частичная.** После второго
возврата и очередного размещения окна A на половине экрана KWin подтвердил
960×1018, но изображение Windows App перестало обновляться: счётчик остался
на 16:30:31 UTC. Проверка Konsole через D-Bus в 16:32:20 UTC показала живой
счётчик frame=9469 внутри гостя. Новый символ `3` в Kate не был виден на
клиенте до повторного перехода A в полный экран около 16:32:39 UTC; после
него появился текст `altka00123` и актуальные кадры. Сеанс и ввод работали,
но отображение остановилось. Повторная проверка спустя более минуты
снова показала прежний кадр 16:32:39; в 16:34:32 счётчик внутри гостя уже
дошёл до frame=11050. Таким образом, переход в полный экран дал временное
обновление, а не устойчивое исправление. [Последний кадр клиента](evidence/alt-workstation-k-x86_64/a-resize-stall.png),
[проверка внутри гостя](evidence/alt-workstation-k-x86_64/final-health.txt).
Причина между KRdp/кодеком/клиентом ещё не локализована; этот результат
нельзя обозначать как отсутствие зависаний.

При намеренном обрыве Windows App показал ошибки 0x4/0x204. Закрытие последнего окна ошибки вызвало тайм-аут инструмента автоматизации Mac; перезапуск клиента восстановил управление. Это ограничение данного прогона: штатное закрытие диалогов клиентом отдельно не подтверждено. Серверные процессы продолжали работать, повторный вход вернул существующие приложения. Наблюдалась задержка между щелчком выбора пользователя и отрисовкой результата: перед вводом пароля нужно дождаться выбранного имени.

Завершены **900 секунд** сбора памяти при запущенной нагрузке двух сеансов
и **120 секунд** после остановки счётчиков и отключения клиента. Проверены
два цикла обрыва. Все PID Kate/KWin/KRdp сохранились; после отключения в
каждом KRdp осталось 4 потока и 20 FD.

| KRdp | PSS после первого обрыва, КиБ | Максимум PSS в прогоне, КиБ | Финальный idle PSS, КиБ | Финальный Private_Dirty, КиБ | Финальный swap, КиБ |
| --- | ---: | ---: | ---: | ---: | ---: |
| native-a | 54534 | 137286 | 53761 | 39260 | 0 |
| native-b | 55123 | 133769 | 52689 | 38104 | 96 |

Финальный PSS ниже спокойного состояния после первого обрыва; в этих двух
циклах нарастающего остатка не обнаружено. Это не доказательство отсутствия
утечек: геометрия менялась, а в последней части остановилось отображение,
что ограничивает сопоставимость активной нагрузки. Часовой тест на этой
системе не выполнен. [Исходный CSV](evidence/alt-workstation-k-x86_64/two-session-memory.csv),
[idle CSV](evidence/alt-workstation-k-x86_64/idle-memory.csv),
[сводка](evidence/alt-workstation-k-x86_64/memory-summary.json).

## Очистка стенда

21 ноября 2026 года после сохранения результатов тестовая ВМ штатно
остановлена и удалена вместе с её снимком и двумя собственными дисками.
Read-only loop-mount установочного ISO снят, тестовый ISO и временные
файлы подготовки на PVE удалены. Остальные ВМ и контейнеры не изменялись.
Логи, CSV и инструкции сохранены в этом репозитории; обнаруженное зависание
динамического изображения остаётся открытым ограничением прототипа.

# ALT Linux: ход проверки ARM64

Проверку ведёт ChatGPT/Codex (OpenAI) по заданию Владимира Гурьева.
На 19 ноября 2026 года подтверждена первая загрузка ALT Regular JeOS в UTM
и доступ по SSH. Plasma установлена, изменённые компоненты собраны;
регрессии кодека, потока callback и координат нажатий прошли.
Подтверждены вход после перезагрузки без автологина, два личных сеанса
Windows App через общий порт и два обрыва с возвратом к прежним Kate/KWin/KRdp.
Ограниченный замер памяти завершён; это лабораторный прототип.

| Образ | Состояние |
| --- | --- |
| Regular JeOS systemd ARM64 + установка Plasma | Два RDP-сеанса, возврат к Kate и динамическое разрешение подтверждены; результат ограниченного замера памяти приведён ниже |
| Regular KDE ARM64 | Образ скачан, SHA-512 совпал; тест ВМ ещё не выполнен |
| Starter Kit p11 KDE ARM64 | SHA-512 совпал; read-only осмотр образа: Plasma 6.7.4, Qt 6.10.3, KF 6.27; загрузка и RDP ещё не проверены |
| «Рабочая станция К» | x86_64, отложенный этап на PVE |

Regular и Starter Kit проверяются отдельно. Установка Plasma в JeOS и
появление пакета branding не означают проверку установочного образа
«Рабочая станция К». Ветки p11 и Sisyphus не смешиваются.

## Подтверждённая исходная среда Regular JeOS

Образ `regular-jeos-systemd-latest-aarch64.img.xz` получен с
[зеркала Regular aarch64](https://mirror.truenetwork.ru/altlinux-nightly/sisyphus-aarch64/tested/).
SHA-512:
`23b4dd90b1f4c18a3acccab35df94324fe8fb63cf808eed8a0ae865e8db4c7c0f00d410c5d1b33dd10c2f23bb4c87b2e8e8762f99b8c35e4f3429e17ef7d62b7`.
Сумма совпала со свежим SHA512SUM этого зеркала. Имя `latest` меняется:
для воспроизведения нужно сохранять конкретную сумму, а не только URL.

В `/etc/os-release`: ALT Regular, BUILD_ID `Sisyphus 20260806`;
фактическое ядро `6.18.62-6.18-alt1.aarch64`. Образ диска увеличен до
40 ГиБ вместе с разделом и ext4; у ВМ 4 CPU и 8 ГиБ RAM.
Для администрирования до первой загрузки добавлен лабораторный
SSH public key, SSH password login отключён. После загрузки пароли
лабораторных аккаунтов заданы штатным `chpasswd`, который учитывает TCB ALT.
Изменения одного `/etc/shadow` недостаточно: ALT хранит пользовательские
shadow-файлы также в `/etc/tcb/`.
Перед GUI-входом после перезагрузки активен только greeter; личные
пользователи не вошли. Автологин отключён установщиком.

В ядре есть `CONFIG_DRM_VGEM=m`, `CONFIG_UDMABUF=y` и модуль vgem.
Штатный `/dev/udmabuf` принадлежит `root:vmusers`, режим 0660.
Не следует переносить владельца устройства или PAM-файлы из Fedora:
это отдельные настройки ALT.

## Репозитории и сборочные зависимости

Штатный адрес `http://ftp.altlinux.org/...` оказался недоступен со стенда.
Работает HTTPS-зеркало **той же** ветки:

```text
rpm [alt] https://mirror.yandex.ru/altlinux Sisyphus/aarch64 classic
rpm [alt] https://mirror.yandex.ru/altlinux Sisyphus/noarch classic
rpm-src [alt] https://mirror.yandex.ru/altlinux Sisyphus/aarch64 classic
rpm-src [alt] https://mirror.yandex.ru/altlinux Sisyphus/noarch classic
```

Существующие активные строки заменяются, а не дублируются; исходные файлы
сохранены перед изменением. Используется штатный vendor `[alt]` и его ключи.
После `apt-get update` выполнен `apt-get -y dist-upgrade` свежей одноразовой
ВМ: 9 обновлений, без удаления пакетов. Это не инструкция по обновлению
рабочего компьютера до Sisyphus.

Кандидаты в этом срезе: Plasma/PLM/KRdp/KPipeWire 6.7.6, Qt 6.11.3,
Frameworks 6.32.0, FreeRDP 3.33.1. Исходники нашего проекта закреплены на 6.7.4.
Сборка изменённых компонентов 6.7.4 с этими заголовками прошла.
Системные greeter, helper, KWin и Plasma остаются пакетными 6.7.6.

`apt-get build-dep krdp plasma-login-manager plasma6-kpipewire` в этой
среде завершается ошибкой поиска `rpmlib(FileDigests)` как пакета. Это
внутренняя возможность RPM. Для проверки использован список требований
соответствующих SRPM, с исключением только внутренних `rpmlib(...)`:

```sh
mkdir matrix-srpms
cd matrix-srpms
apt-get -y --download-only source krdp plasma-login-manager plasma6-kpipewire
rpm -qp --requires ./*.src.rpm
```

Использованы SRPM `krdp-6.7.6-alt1`, `plasma-login-manager-6.7.6-alt1`,
`plasma6-kpipewire-6.7.6-alt1`. Их подписи дополнительно проверены штатным
ключом Sisyphus `DF6C02E5F174D7CDF792A9CDFF979DEDDA2773BB` из alt-gpgkeys
в отдельной временной базе RPM. Простая `rpm -K` без этой базы сообщала
MISSING KEYS; это не было принято за успешную проверку подписи.

Реальные BuildRequires из этих SRPM и runtime пакеты устанавливаются
через обычный APT. Общий набор на чистой JeOS: 1142 новых пакета,
около 782 МБ загрузки и 4242 МБ после распаковки. В него включены
`plasma-login-manager plasma-workspace plasma-desktop krdp kate konsole`,
`nftables openssl cmake make gcc-c++ python3 patch git qemu-guest-agent`
и `plasma6-libkscreen-devel`.

## Пути и PAM

Из подписанного штатного пакета PLM подтверждены:

- helper `/usr/libexec/plasmalogin-helper`;
- Wayland session script `/etc/plasmalogin/wayland-session`;
- X11 session script в пакетной сборке `/etc/X11/Xsession`;
- units `/usr/lib/systemd/system/plasmalogin.service` и
  `/usr/lib/systemd/user/plasma-login-kwin_wayland.service`;
- PAM `/etc/pam.d/plasmalogin`, `plasmalogin-greeter`, `plasmalogin-autologin`.

ALT добавляет собственный профиль PAM `alt` в пакетную сборку. В исходном
upstream 6.7.4 этого профиля нет. Наш daemon должен использовать **штатный
установленный PAM ALT**, без подстановки Debian/Fedora-правил. Параметры
сборки приведены ниже и проверены в этой ВМ.

## Проверенная сборка

После основного набора зависимостей потребовались `gettext-tools` и
`libffi-devel`. Runtime дополнительно требует **`pipewire wireplumber
plasma6-libkscreen-utils`**. Одних `pipewire-libs` и `plasma6-libkscreen-devel`
недостаточно: в JeOS отсутствовали конфигурация/служба PipeWire и плагины
KScreen, хотя компиляция уже завершалась успешно.

```sh
# root, внутри одноразовой ALT Regular JeOS
apt-get -y install gettext-tools libffi-devel pipewire wireplumber plasma6-libkscreen-utils
systemctl --global enable pipewire.socket wireplumber.service
```

Сборка выполняется обычным пользователем из корня checkout:

```sh
mkdir -p "$HOME/.cache/plasma-rdp-build-tmp"
chmod 700 "$HOME/.cache/plasma-rdp-build-tmp"
export TMPDIR="$HOME/.cache/plasma-rdp-build-tmp"
export LANG=C.UTF-8
python3 scripts/prepare.py --output build/alt-sources
PLASMA_RDP_INSTALL_PAM_CONFIGURATION=OFF \
PLASMA_RDP_LIBEXECDIR=libexec \
PLASMA_RDP_SESSION_COMMAND=/etc/X11/Xsession \
JOBS=4 bash scripts/build-kde.sh "$PWD/build/alt-sources"
bash scripts/check-regressions.sh "$PWD/build/alt-sources"
bash scripts/stage-kde.sh "$PWD/build/alt-sources" "$PWD/build/alt-stage"
```

Отдельный `TMPDIR` нужен и при запуске через `runuser`: у root в ALT он
может указывать на `/tmp/.private/root`, куда обычный пользователь не может
создавать временные файлы GNU make. Не следует менять права root-каталога.
`INSTALL_PAM_CONFIGURATION=OFF` оставляет штатные правила ALT; профиль
`debian` из upstream не устанавливается поверх них.

Проверены ELF без `RPATH/RUNPATH` и разрешение `KPipeWire`,
`KPipeWireDmaBuf`, `KPipeWireRecord` из согласованного staging 6.7.4.
Регрессионная проверка кодека воспроизводит ошибку старого варианта и
проходит на исправленном; проверки владельца потока и положения кнопок
тоже проходят. Старый InputHandler отдельно проваливает тест координат.

## Устройства, привилегированные интерфейсы и применение

```sh
# root, только тестовая ВМ; native-a/native-b созданы, пароли заданы через passwd/chpasswd
modprobe vgem
printf 'vgem\n' > /etc/modules-load.d/plasma-rdp-lab.conf
groupadd -f plasma-rdp-render
for u in plasmalogin native-a native-b; do usermod -aG plasma-rdp-render "$u"; done
install -m 0644 runtime/fedora/99-plasma-rdp-udmabuf.rules /etc/udev/rules.d/
udevadm control --reload-rules
udevadm trigger --action=add /sys/class/misc/udmabuf
```

`udmabuf` встроен в это ядро: отдельная загрузка модуля не нужна. Правило
с именем `fedora` использует `setfacl` для отдельной группы и подходит этому
стенду ALT: исходные root/vmusers и режим 0660 устройства сохранены.
Наличие `setfacl` и итоговый ACL следует проверить перед запуском.

У KWin 6.7 проверка привилегированных Wayland-интерфейсов учитывает
**канонический путь executable из desktop entry**. Для greeter и личного
KRdp установщик размещает два отдельных NoDisplay desktop entry с точными
`Exec`/`TryExec` из `/opt` и разрешениями `org_kde_kwin_fake_input` и
`zkde_screencast_unstable_v1`. Одного entry пользовательского бинарника
недостаточно для greeter: до исправления первая попытка подключиться
заканчивалась SIGSEGV при недоступном screencast interface.
Глобальное отключение проверки разрешений KWin не применялось.

После просмотра staging и runtime применяются обычные команды из BUILD.md:

```sh
cp -a build/alt-stage/opt/. /opt/
bash runtime/install-handover.sh --apply-to-disposable-vm
reboot
```

PAM ALT и пользовательские пароли остаются обязательными. В Windows App
выполняется транспортный вход `greeter`, затем личный вход в Plasma.
Оба профиля идут через один SSH-forward к guest `3389`, а backend-порты
`3390–3410` закрыты для пользовательского доступа правилами nftables.
`Update session resolution on resize` включён в обоих профилях.

## GUI-проверка, 19 ноября 2026

В UTM ARM64 подтверждены два разных пользователя, несохранённые документы
`altjeosa001` и `altjeosb001`, движущийся счётчик в Konsole в каждом сеансе.
Два раза принудительно завершён **клиент Windows App**, без выхода из Plasma.
После повторного личного входа возвращались прежние процессы:

| Пользователь | Kate PID | KWin PID | KRdp PID |
| --- | ---: | ---: | ---: |
| native-a | 2904 | 2307 | 2311 |
| native-b | 3596 | 3113 | 3117 |

Геометрия KWin проверена через `supportInformation`, а не по размеру
картинки клиента: исходно 1280×800, окна 1280×1378, полный экран 2560×1440.
После первого обрыва полный экран A тоже реально дал 2560×1440; после
второго оба окна вернулись к 1280×1378. Картинка счётчиков обновлялась.

В журнале повторного входа есть предупреждение про невозможный VT 0 для
headless-сеанса и сообщение PAM о закрытии неоткрытой новой сессии: это
путь повторной проверки пароля и перехода в уже существующий сеанс.
Возврат и сохранение PID подтверждены, однако эти предупреждения остаются
известной особенностью прототипа.

### Память: границы результата

Часовой тест на ALT в рамках этого этапа **не выполнялся**. Сохранены два
замера по 900 секунд с перекрытием около 16,5 секунды: общая временная
полоса 07:58:24–08:28:07 UTC, примерно **29 мин 44 с**. Нагрузка — вывод
движущихся счётчиков в Konsole, два общих обрыва Windows App и изменения
разрешения. Это не полный CPU/RAM stress test и не проверка Guacamole на ALT.

| Сеанс | Private Dirty после обрыва 1, КиБ | После обрыва 2, КиБ | Разница, КиБ |
| --- | ---: | ---: | ---: |
| A | 60328 | 55496 | −4832 |
| B | 62864 | 63584 | +720 |

В отключённом состоянии возвращаются 4 потока и 20 дескрипторов; при
подключении — 34 и 68. PID KRdp/KWin/Kate в обоих CSV неизменны. Swap
KRdp во всех выборках равен нулю. Устойчивое накопление на **этих двух
циклах** не подтверждено; отсутствие утечек этим не доказано.

Конечная активная память не равна исходной: Private Dirty A — 129860 КиБ,
B — 124120 КиБ; AnonHugePages A — 83968 КиБ, B — 49152 КиБ. Особенно
в A меняется объём больших страниц. Эти показатели сами по себе не
устанавливают владельца удерживаемой памяти и не доказывают причину роста.
Нужны дополнительные одинаковые циклы и измерения после отключения.

Перед переносом ноутбука нагрузка остановлена, `utmctl suspend` вернул
состояние paused. После возвращения ВМ оказалась stopped и при запуске
получила новый boot ID; прежние пользовательские процессы отсутствовали.
Поэтому заключительный замер старых процессов после паузы невозможен.
Приостановку UTM нельзя считать подтверждённым сохранением сеансов после
выключения хоста. Причина перехода из paused в stopped не установлена.

[CSV, события, регрессии и сводка](evidence/alt-regular-jeos-arm64/) сохранены
отдельно от диска ВМ. Очистка этой тестовой ВМ пока не завершена: из неё
экспортируется отдельно подготовленный диск следующей Regular KDE ВМ.

## Starter Kit p11 KDE: предварительный осмотр образа

Образ `alt-p11-kde-20260912-aarch64.img.xz` проверен по SHA-512 и подключён
через read-only NBD; ext4 смонтирована с `ro,noload`. Это **не** загрузка
Starter Kit в ВМ и не проверка RDP. В установленной базе пакетов:

| Компонент | Версия в образе |
| --- | --- |
| Ветка | p11, ALT Starterkit 11 |
| Ядро | 6.12.103-6.12-alt1, ARM64 |
| Plasma Workspace / KPipeWire | 6.7.4-alt1 |
| Qt Core | 6.10.3-alt5 |
| KDE Frameworks CoreAddons | 6.27.0-alt1 |
| PipeWire / WirePlumber | 1.4.7-alt1 / 0.5.13-alt1 |
| Display manager | LightDM 1.32.0-alt15 |

Версии Qt и Frameworks соответствуют заявленным минимумам исходников
KRdp/PLM 6.7.4 (Qt 6.10, KF 6.26); Plasma соответствует минимуму PLM 6.7.
Это только предварительная проверка требований: сборка, пакет PLM и
фактическая работа Wayland/RDP ещё не проверены. KRdp, FreeRDP3 и PLM
в списке установленных пакетов образа не обнаружены. Зависимости следует
получать из **p11**, без подключения Sisyphus или использования его RPM-кэша.

[Вывод read-only проверки](evidence/alt-starter-p11-arm64/offline-preflight.txt).

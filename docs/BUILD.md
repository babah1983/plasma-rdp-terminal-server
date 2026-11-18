# Сборка и применение на отдельной Debian sid ВМ

Проверенная среда: ARM64, Debian sid, Plasma/KRdp/KPipeWire 6.7.4,
Qt не ниже 6.10, KDE Frameworks не ниже 6.26, FreeRDP 3.33.1.
На других версиях/архитектурах требуется самостоятельная проверка.
Образы ВМ и зависимости не включены; полные исходники изменяемых проектов включены.

## 1. Зависимости

Включите `deb-src` для используемого Debian-репозитория. Нужны пакеты той же
ветки Plasma; при изменении sid может понадобиться исторический snapshot или
согласованная сборочная среда. Точные исходники 6.7.4 уже находятся в репозитории.

```sh
sudo apt-get update
sudo apt-get install build-essential cmake ninja-build pkg-config python3 patch dpkg-dev \
    plasma-login-manager plasma-workspace plasma-desktop kwin-wayland krdp \
    nftables openssl libkscreen-dev
sudo apt-get build-dep krdp plasma-login-manager kpipewire
```

Дистрибутивный Plasma Login Manager обязателен: он предоставляет системного
пользователя `plasmalogin`, PAM-правила, systemd units, greeter, helper и сессии.
Мы собираем изменяемый daemon, а не устанавливаем все компоненты с нуля.

## 2. Подготовка и сборка без изменения системы

Из корня репозитория:

```sh
python3 scripts/prepare.py
JOBS=2 bash scripts/build-kde.sh
bash scripts/stage-kde.sh
find build/stage -type f -o -type l
```

`prepare.py` проверяет `upstream-files.sha256`. Каталог назначения должен быть
новым; staging-каталог также должен быть новым, чтобы исключить старые файлы.
Для повторной независимой подготовки можно указать другой путь:

```sh
python3 scripts/prepare.py --output build/second-sources
bash scripts/build-kde.sh "$PWD/build/second-sources"
bash scripts/stage-kde.sh "$PWD/build/second-sources" "$PWD/build/second-stage"
```

Скрипт создаёт две сборки KRdp: greeter с первым NLA/redirection-патчем и
пользовательскую с дополнительными Display Control/Progressive-исправлениями.
Это сохраняет схему проверенного стенда. Порядок всей серии записан в
`scripts/prepare.py` и в создаваемом `applied-series.json`.

## 3. Применение только в одноразовой ВМ

Следующие команды меняют систему: копируют файлы в `/opt`, меняют запуск
Plasma Login Manager, systemd/nftables, отключают autologin и блокировку экрана
тестовых пользователей, перезапускают диспетчер и менеджер входа. Сначала
сделайте снимок ВМ. Локальная графическая сессия при перезапуске PLM может завершиться.

Создайте двух Linux-пользователей и задайте им пароли интерактивно:

```sh
sudo adduser native-a
sudo adduser native-b
sudo modprobe vgem
```

`vgem` должен присутствовать в ядре; для воспроизведения загрузки без автологина
его также нужно загружать при старте, например через `/etc/modules-load.d/`.
Рабочий стенд использовал Debian kernel 6.12.117 с этим модулем.

Просмотрите `runtime/`, затем примените:

```sh
sudo cp -a build/stage/opt/. /opt/
sudo bash runtime/install-handover.sh --apply-to-disposable-vm
```

Секрет и самоподписанный сертификат генерируются локально при первом применении.
Никаких фиксированных паролей в репозитории нет. Транспортный логин — `greeter`;
после RDP-аутентификации вводится персональный Linux-пароль на экране Plasma.
Файл транспортного секрета расположен в
`/var/lib/plasmalogin/.local/state/plasma-rdp/password` и закрыт правами каталога.
Проверьте отпечаток созданного сертификата до доверия ему на клиенте.

Пользовательские backend-порты 3390–3410 должны оставаться loopback/root-only.
Для доступа с компьютера клиента используйте SSH-туннель (замените host/user):

```sh
ssh -N -L 127.0.0.1:13393:127.0.0.1:3389 labadmin@VM_HOST
```

В Windows App подключитесь к `127.0.0.1:13393`, включите динамическое разрешение
для проверки Display Control. Для двух окон можно использовать два профиля с
`127.0.0.1:13393` и `localhost:13393`; убедитесь, что localhost разрешается в IPv4.
Входы через общий greeter выполняйте по очереди.

Для возврата к исходной системе используйте сделанный снимок ВМ. Автоматический
удалённый rollback менеджера входа этим набором не реализован.

## 4. Guacamole: отдельное необязательное исправление

Проверялся guacd/libguac **1.6.0** с FreeRDP **3.24.2** и frontend **1.5.5**.
Доступ к тестовому RDP-адресу и доверие к его сертификату настраиваются отдельно.
Не отключайте certificate validation для воспроизведения рабочего теста.

Основной исходный патч уже применяется к копии
`build/sources/guacamole-server-1.6.0/src/libguac/display-layer.c`.
Он предназначен для включения в вашу пакетную сборку libguac. Полная сборка
RDP-плагина Guacamole 1.6.0 с FreeRDP 3.33.1 этим проектом не подтверждена:
старый RDP-плагин обращается к API, изменённому в новых FreeRDP.

Проверенный в часовом тесте вариант — отдельный adapter через публичные
raw-context API libguac. Он загружается только в лабораторный guacd 1.6.0,
не затрагивая основной сервис. Собирайте на ОС/архитектуре этого guacd:

```sh
sudo apt-get install build-essential pkg-config libcairo2-dev
bash scripts/build-guacamole-adapter.sh
```

На ALT или другом дистрибутиве установите соответствующие C/Cairo development
пакеты. Библиотека создаётся в `build/libguac-external-buffer-resize.so`.
Она рассчитана на RDP-plugin с одним raw-context на поток, не на произвольные
плагины libguac и не на другие версии API.

Просмотрите `runtime/guacamole-resize-lab.service.example`: замените путь к
adapter и HOME/пользователя guacd на свою конфигурацию. Отдельный daemon должен
слушать только loopback, например 14822. В двух собственных тестовых профилях
Guacamole задайте этот guacd server/port; RDP server/port остаются одинаковыми.
Предоставленный unit — образец со стенда, он сам никуда не устанавливается.

Полное отключение dirty-оптимизации и PNG-обход не входят в действующее
исправление. Обычные кадры после замены буфера остаются инкрементальными.

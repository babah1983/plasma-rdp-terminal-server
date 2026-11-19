# Fedora 45 ARM64: проверенный лабораторный профиль

Проверено ChatGPT/Codex (OpenAI) по заданию Владимира Гурьева 19 ноября
2026 года в отдельной UTM ВМ: 4 CPU, 8 ГиБ RAM, диск 40 ГиБ.
Это Fedora Cloud Base Generic с установленной Plasma, а не приёмка KDE Live ISO.
Результат экспериментальный: он не означает готовность к эксплуатации.

## Образ и версии

Официальный образ: `Fedora-Cloud-Base-Generic-45-1.4.aarch64.qcow2`.
SHA-256: `1632acc8bc14d45b6c9596a0acc71b070d3748d1abdcf1a519be5c983bb0286c`.
CHECKSUM проверен также по PGP-подписи. Отпечаток ключа Fedora 45:
`4F50A6114CD5C6976A7F1179655A4B02F577861E`.
Образ, CHECKSUM и ключ берутся с [Fedora Cloud](https://fedoraproject.org/cloud/download/)
и [официального набора ключей](https://fedoraproject.org/fedora.gpg).

В проверенной системе: kernel `7.3.4-300.fc45.aarch64`, Qt `6.11.2-3.fc45`,
Frameworks `6.32.0-1.fc45`, Plasma/PLM/KRdp/KPipeWire `6.8.3-1.fc45`,
FreeRDP `3.33.1-1.fc45`, Mesa `26.2.7`, LLVM `23.1.5`.
Изменяемые исходники проекта остаются 6.7.4. Смешивания репозиториев выпусков
или подключения RPM Fusion в этой проверке не было.

## Зависимости и сборка

В свежей одноразовой ВМ с настроенным администраторским доступом:

```sh
sudo dnf -y install dnf5-plugins cmake ninja-build gcc-c++ make python3 patch git pkgconf-pkg-config \
    plasma-login-manager plasma-workspace plasma-desktop kwin-wayland krdp kate konsole \
    nftables openssl libkscreen-devel kernel-modules-extra
sudo dnf -y builddep krdp plasma-login-manager kpipewire
sudo dnf -y install policycoreutils-python-utils acl
```

Пакетный Plasma Login Manager обязателен: используются его системный
пользователь, greeter, helper, units и PAM. Перед сборкой проверьте пути:
`/usr/libexec/plasmalogin-helper` и `/usr/share/plasmalogin/scripts/Xsession`.
Из корня этого репозитория:

```sh
python3 scripts/prepare.py --output build/fedora-sources
PLASMA_RDP_PAM_CONFIGURATION=fedora \
PLASMA_RDP_LIBEXECDIR=libexec \
PLASMA_RDP_SESSION_COMMAND=/usr/share/plasmalogin/scripts/Xsession \
JOBS=4 bash scripts/build-kde.sh "$PWD/build/fedora-sources"
bash scripts/stage-kde.sh "$PWD/build/fedora-sources" "$PWD/build/fedora-stage"
bash scripts/check-regressions.sh "$PWD/build/fedora-sources"
```

Важно сохранять согласованные пары библиотек: greeter использует собственные
`krdpserver` + `libKRdp`, а оба варианта KPipeWire — собственные
`libKPipeWire` **и** `libKPipeWireRecord`. Подстановка системного Record 6.8
к нашему core 6.7 вызывала реальную ошибку undefined symbol. Staging теперь
содержит обе библиотеки. Полезно проверить `ldd -r` с соответствующим
`LD_LIBRARY_PATH` до переключения менеджера входа.

## Применение в одноразовой ВМ

Сначала сделайте снимок. Следующие команды меняют системный менеджер входа
и могут завершить локальную графическую сессию. Создайте `native-a` и
`native-b` через `useradd -m`, задайте каждому пароль командой `passwd`.
Дальнейший порядок предполагает новый стенд без ранее добавленных fcontext
правил; при повторном применении сверяйте существующие записи.

```sh
sudo cp -a build/fedora-stage/opt/. /opt/
sudo semanage fcontext -a -t xdm_exec_t '/opt/system-plasma-login/plasmalogin'
sudo semanage fcontext -a -t bin_t '/opt/system-krdp(-display)?/bin(/.*)?'
sudo semanage fcontext -a -t lib_t '/opt/system-krdp(-display)?/lib(/.*)?'
sudo semanage fcontext -a -t lib_t '/opt/system-kpipewire-(shm|pool)/lib(/.*)?'
sudo semanage fcontext -a -t xdm_var_run_t '/run/plasma-rdp-dispatch(/.*)?'
sudo restorecon -RFv /opt/system-plasma-login /opt/system-krdp \
    /opt/system-krdp-display /opt/system-kpipewire-shm /opt/system-kpipewire-pool
```

SELinux оставлен **Enforcing**, изменённый PLM работает в `xdm_t`.
Метка `xdm_var_run_t` нужна для управляющего сокета диспетчера: без неё
SELinux блокировал передачу после успешной персональной аутентификации.
Дополнительный разрешающий SELinux-модуль не понадобился.

В штатном libavcodec-free этой Fedora доступен encoder `libopenh264`, а
`libx264` отсутствует. Для **обоих** units создайте drop-in:

```sh
for service in greeter user; do
    sudo mkdir -p "/etc/systemd/user/plasma-rdp-$service.service.d"
    printf '[Service]\nEnvironment=KPIPEWIRE_FORCE_ENCODER=libopenh264\n' |
        sudo tee "/etc/systemd/user/plasma-rdp-$service.service.d/fedora-encoder.conf" >/dev/null
done
```

KWin 6.8 в проверенной конфигурации использует `/dev/udmabuf` для программного
рендеринга. Устройство принадлежит `root:kvm`, а seat ACL был выдан только
greeter. У пользователей из `video,render` не было доступа, и KWin выдавал
`Rendering a layer failed`: после handoff оставался старый кадр greeter.
Исправление — выделенная группа и адресный ACL, с сохранением владельца,
группы `kvm`, режима и штатных seat ACL:

```sh
sudo groupadd --system plasma-rdp-render
sudo usermod -aG plasma-rdp-render native-a
sudo usermod -aG plasma-rdp-render native-b
sudo install -D -m 0644 runtime/fedora/99-plasma-rdp-udmabuf.rules \
    /etc/udev/rules.d/99-plasma-rdp-udmabuf.rules
sudo udevadm control --reload
sudo udevadm trigger --action=add /sys/class/misc/udmabuf
sudo udevadm settle
getfacl /dev/udmabuf
printf 'vgem\n' | sudo tee /etc/modules-load.d/plasma-rdp-lab.conf
sudo modprobe vgem
```

В этом ядре `CONFIG_UDMABUF=y`: udmabuf встроен. Не добавляйте его в
modules-load и не считайте ошибку `modprobe udmabuf` доказательством отсутствия
устройства. `vgem` загружается модулем из kernel-modules-extra.

Теперь примените общий набор и перезагрузите ВМ:

```sh
sudo bash runtime/install-handover.sh --apply-to-disposable-vm
sudo restorecon -RFv /run/plasma-rdp-dispatch
sudo reboot
```

`WAYLAND_DISPLAY` пользовательского KRdp должен наследоваться от user manager.
У обоих пользователей Fedora фактический сокет был `wayland-1` в разных
`XDG_RUNTIME_DIR`; жёстко заданный `wayland-0` приводил к отказу Qt подключиться
к compositor. Эта константа удалена из unit и нагрузочного теста.
QPainter и отключение overlays не являются частью итоговой настройки:
проверен штатный OpenGL ES/llvmpipe без изменений KWin.

После reboot проверьте `getenforce`, `ps -eZ` для PLM, `ls -lZ` для сокета,
`getfacl /dev/udmabuf`, состояние units и отсутствие native-сессий до входа.
Доступ клиента и транспортный секрет описаны в [BUILD.md](BUILD.md).
В Windows App включите **Update session resolution on resize**. Логины через
общий greeter выполняются последовательно; затем рабочие столы независимы.

## Фактическая проверка Windows App

- После reboot автологин отсутствовал, до входа работали greeter и SSH.
- Два пользователя вошли через один guest endpoint `127.0.0.1:3389`.
  На Mac использованы профили `127.0.0.1:13461` и `localhost:13461` через
  IPv4/IPv6 SSH forwarding к тому же endpoint; разные backend-порты не
  указывались в клиентских профилях.
- Мышь и клавиатура проверены в GUI. Удержание синтетической клавиши на
  120–180 мс давало полный ввод; быстрый автоматический ввод терял символы.
  Мгновенный screenshot после клика иногда показывал состояние до обработки
  события; этот факт не считался зависанием RDP.
- Два раза прерван транспорт обоих окон завершением только Windows App.
  После каждого повторного входа сохранились прежние Kate, KWin и KRdp PID,
  а также несохранённые строки `fedoraa001` / `fedorab001`, дополненные `2`
  при проверке ввода после первого возврата. Консольный счётчик продолжал
  менять кадры. Перезагрузок и выхода пользователей между этими циклами не было.
- Display Control реально менял геометрию Plasma: исходные 1280×800,
  половина экрана 1280×1378 у обоих, полный экран 2560×1440.
  Геометрия подтверждена через KWin DBus supportInformation, отдельно от
  масштабирования картинки в Windows App.
- Сборщик RSS/PSS работал ровно 900 секунд с шагом 10 секунд. Этот интервал
  включал оба отключения, первый возврат и смены размеров; второй возврат
  завершён уже после окончания CSV. Это **15-минутное наблюдение, не часовой
  тест Fedora**. Диапазон RSS: A 147.69–255.50 МиБ, B 146.12–299.17 МиБ.
  После отключений оба процесса возвращались к 4 потокам и 21 FD; после
  второго отключения наблюдались RSS около 147.69/147.40 МиБ и PSS около
  55/54 МиБ. Величина остатка после отключения также менялась; этих двух циклов
  недостаточно для утверждения об отсутствии медленной утечки. Сравнивать пик большого разрешения с
  исходным малым разрешением как «утечку» некорректно.

В заключительном дополнительном наблюдении 120 секунд, после остановки
нагрузки и отключения клиента, swap оставался нулевым. У B private dirty
держался на 41272 КиБ; у A он вырос с 41824 до 56080 КиБ одновременно с
ростом AnonHugePages с 10240 до 38912 КиБ. Это повод отдельно проверить
влияние transparent huge pages; имеющихся измерений недостаточно, чтобы
приписать весь остаток shared pages, allocator или утечке KRdp.
Итог по памяти в этой строке матрицы: **ограниченное наблюдение, длительная
стабильность ещё не подтверждена**.

[CSV памяти и проверки PID/геометрии](evidence/fedora-45-arm64/) сохранены отдельно.

Регрессии Progressive/full-first-frame и принадлежности encoder callback
прошли на этой Fedora. Guacamole на Fedora в этой строке матрицы не проверялся;
предыдущие результаты Debian/Guacamole приведены отдельно в [TESTING.md](TESTING.md).

После сохранения результатов тестовая Fedora ВМ остановлена, удалена из UTM
и с внешнего SSD. Три ранее существовавших лабораторных ВМ оставлены работающими.

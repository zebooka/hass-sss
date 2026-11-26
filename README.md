[English](/README.en.md) | [Русский](/README.md)

# Интеграция Saved Snapshot Size для Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5)](https://hacs.xyz)
[![Release](https://img.shields.io/github/v/release/zebooka/hass-sss?label=release&color=blue)](https://github.com/zebooka/hass-zkhnso/releases/latest)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.12%2B-blue?logo=home-assistant)
[![License](https://img.shields.io/github/license/zebooka/hass-sss?color=green)](https://github.com/zebooka/hass-zkhnso/blob/master/LICENSE)
![Custom Integration](https://img.shields.io/badge/Custom%20Integration-orange)
[![Спонсировать на Cloudtips](https://img.shields.io/badge/donate-cloudtips-FFDD2D.svg)](https://pay.cloudtips.ru/p/34ce579c)
[![Русский язык](https://img.shields.io/badge/Русский%20язык-ДА-red)](https://ru.wikipedia.org/wiki/%D0%9F%D1%83%D1%88%D0%BA%D0%B8%D0%BD,_%D0%90%D0%BB%D0%B5%D0%BA%D1%81%D0%B0%D0%BD%D0%B4%D1%80_%D0%A1%D0%B5%D1%80%D0%B3%D0%B5%D0%B5%D0%B2%D0%B8%D1%87)

<img src="https://github.com/zebooka/hass-sss/blob/master/custom_components/sss/brand/icon@2x.png?raw=true" alt="Saved Snapshot Size" width="128"/>

Интеграция, решающая проблему с размером стопкадра видеопотока в автоматизациях. 

В стандартном Home Assistant отсутствует выбор размера снимка при вызове действия `camera.snapshot`. Размер изображения выбирается автоматически, исходя из параметров видеопотока. Однако некоторые видеопотоки имеют несколько вариантов разных размеров и не всегда камеры возможно настраивать. Например, если устройство камеры предоставляется сторонней интеграцией. Эта интеграция позволяет жестко задать требуемые размеры изображения при вызове функции `async_get_image`.

## Установка

### Marketplace или HACS (рекомендуется)

[![Откройте свой экземпляр Home Assistant и перейдите к репозиторию в магазине Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=zebooka&repository=hass-sss&category=integration)

1. Откройте Настройки → **Marketplace** (для Home Assistant 2026.11+) или **HACS** и выполните поиск **Saved Snapshot Size** (или воспользуйтесь кнопкой выше).
2. Откройте **Saved Snapshot Size**, выберите **Скачать** (Download) и подтвердите действие.
3. Перезапустите Home Assistant, а затем добавьте интеграцию через **Настройки → Устройства и службы**.

### HACS: пользовательский репозиторий

1. В HACS откройте **⋮ → Пользовательские репозитории**.
2. Добавьте `https://github.com/zebooka/hass-sss` с типом **Integration**.
3. Найдите **Saved Snapshot Size** и установите интеграцию.
4. Перезапустите Home Assistant.
5. Добавьте интеграцию через **Настройки → Устройства и службы**.

### Ручная установка

1. Скопируйте папку `sss` в папку `custom_components` в вашем Home Assistant.
2. Перезапустите Home Assistant.
3. Добавьте интеграцию через **Настройки → Устройства и службы**.

## Действие `sss.snapshot`

После добавления интеграции используйте действие в автоматизациях и скриптах:

```yaml
action: sss.snapshot
data:
  entity_id: camera.front_door
  filename: /config/www/front_door.jpg
  width: 1280
  height: 720
  timeout: 15
```

`entity_id` и `filename` обязательны. `filename` поддерживает шаблоны, а файл при повторном вызове перезаписывается. Каталог назначения должен быть разрешён в `allowlist_external_dirs` (папка конфигурации обычно разрешена). Подкаталоги создаются автоматически.

`width`, `height` (пиксели) и `timeout` (секунды, по умолчанию 10) необязательны и должны быть положительными целыми числами. Размер передаётся интеграции камеры; его соблюдение зависит от камеры и формата снимка. Для JPEG Home Assistant также пытается изменить размер, когда указаны обе стороны. Действие принимает одну камеру за вызов.

## Поддержка

Отчёты об ошибках и предложения, направляйте через [репозиторий на GitHub](https://github.com/zebooka/hass-sss).

## Лицензия

Этот проект распространяется под открытой лицензией MIT.

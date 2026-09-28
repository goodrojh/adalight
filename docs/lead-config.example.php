<?php
/**
 * Настройки приёма заявок. Скопируйте этот файл в lead-config.php (рядом с lead.php) и заполните.
 * lead-config.php НЕ выкладывать в открытый доступ и не отправлять в репозиторий — в нём ключ CRM.
 */
return [
    // Битрикс24 → Разработчикам → Другое → Входящий вебхук, права: CRM (crm).
    // Ссылка вида https://ИМЯ.bitrix24.ru/rest/1/xxxxxxxxxxxxxxxx/
    'webhook' => '',

    // ID сотрудника, на которого назначать лиды (из адреса его профиля в Битрикс24). Пусто — на автора вебхука.
    'assigned_by_id' => '',

    // Источник лида в CRM (WEB = «Веб-сайт»).
    'source_id' => 'WEB',

    // Почта: запасной путь, если CRM недоступна. email_copy = true — присылать копию каждой заявки.
    'email' => 'damir@adalight.ru',
    'email_copy' => false,
    'email_from' => 'noreply@adalight.ru',

    // С каких адресов сайта принимать заявки.
    'allowed_origins' => ['https://adalight.ru', 'https://www.adalight.ru'],
];

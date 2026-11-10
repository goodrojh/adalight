<?php
/**
 * ADALIGHT — приём заявок с сайта и передача в CRM Битрикс24 (лид).
 *
 * Лежит на хостинге рядом с сайтом: https://adalight.ru/lead.php
 * Ключ Битрикс24 хранится в lead-config.php (рядом с этим файлом), в код страниц он не попадает.
 * Если Битрикс24 недоступен — заявка уходит письмом на LEAD_EMAIL, чтобы не потерялась.
 */

header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex');

function reply($code, $msg) { http_response_code($code); echo json_encode(['ok' => $code === 200, 'message' => $msg], JSON_UNESCAPED_UNICODE); exit; }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') reply(405, 'Только POST');

$cfgFile = __DIR__ . '/lead-config.php';
if (!is_file($cfgFile)) reply(500, 'Нет lead-config.php');
$cfg = require $cfgFile;

// заявки только с нашего сайта
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin && !empty($cfg['allowed_origins']) && !in_array($origin, $cfg['allowed_origins'], true)) reply(403, 'Чужой сайт');

$raw = file_get_contents('php://input', false, null, 0, 4000000);
$in = json_decode($raw, true);
if (!is_array($in) || !isset($in['data']) || !is_array($in['data'])) reply(400, 'Пустая заявка');
$d = $in['data'];
$form = mb_substr(trim((string)($in['form'] ?? 'Заявка с сайта')), 0, 120);

// защита от ботов: скрытое поле website заполняют только роботы
if (!empty($d['website'])) reply(200, 'ok');

date_default_timezone_set('Europe/Moscow');
$s = function ($k, $len = 2000) use ($d) { $v = $d[$k] ?? ''; if (is_array($v)) $v = implode(', ', $v); return mb_substr(trim((string)$v), 0, $len); };
$phoneDigits = preg_replace('/\D/', '', $s('phone', 40));
$email = $s('email', 200);
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) $email = '';
// нужен телефон или e-mail (форма запроса документации — только e-mail)
if (strlen($phoneDigits) < 10 && !$email) reply(400, 'Проверьте телефон');
if (strlen($phoneDigits) < 10) $phoneDigits = '';
// 152-ФЗ: без согласия на обработку персональных данных заявку не принимаем
if (empty($d['consent'])) reply(400, 'Нужно согласие на обработку персональных данных');

// не больше 20 заявок с одного адреса за 10 минут
$ipKey = sys_get_temp_dir() . '/ada_lead_' . md5($_SERVER['REMOTE_ADDR'] ?? '');
$hits = array_filter(is_file($ipKey) ? (array)json_decode(file_get_contents($ipKey), true) : [], function ($t) { return $t > time() - 600; });
if (count($hits) >= 20) reply(429, 'Слишком много заявок, позвоните нам');
$hits[] = time(); @file_put_contents($ipKey, json_encode(array_values($hits)));

// текст для менеджера
$lines = [];
foreach ([
    'email' => 'E-mail', 'skus' => 'Серии / артикулы', 'docs' => 'Что нужно',
    'role' => 'Кто', 'object' => 'Тип объекта', 'stage' => 'Стадия проекта', 'topic' => 'Тема',
    'comment' => 'Комментарий', 'spec' => "Спецификация:\n", 'spec_link' => 'Открыть спецификацию на сайте',
] as $k => $title) {
    $v = $s($k, 20000);
    if ($v !== '') $lines[] = (substr($title, -1) === "\n" ? $title : $title . ': ') . $v;
}
$page = $s('page', 500);
if ($page && empty($d['spec_link'])) $lines[] = 'Страница: ' . $page;
$ref = $s('referrer', 500);
if ($ref) $lines[] = 'Пришёл с: ' . $ref;
$utm = is_array($d['utm'] ?? null) ? $d['utm'] : [];
$lines[] = 'Согласие на обработку ПД: дано ' . date('d.m.Y H:i') . ' (МСК), IP ' . ($_SERVER['REMOTE_ADDR'] ?? '?') . ', текст: ' . ($s('consent_doc', 200) ?: 'https://adalight.ru/consent/');

$name = $s('name', 100);
$lead = [
    'TITLE' => $form . ($name ? ' — ' . $name : ''),
    'NAME' => $name,
    'PHONE' => $phoneDigits ? [['VALUE' => '+' . $phoneDigits, 'VALUE_TYPE' => 'WORK']] : [],
    'EMAIL' => $email ? [['VALUE' => $email, 'VALUE_TYPE' => 'WORK']] : [],
    'COMMENTS' => implode('<br>', array_map(function ($l) { return nl2br(htmlspecialchars($l, ENT_QUOTES, 'UTF-8')); }, $lines)),
    'SOURCE_ID' => $cfg['source_id'] ?? 'WEB',
    'SOURCE_DESCRIPTION' => 'Сайт ADALIGHT: ' . $form,
    'OPENED' => 'Y',
];
if (!empty($cfg['assigned_by_id'])) $lead['ASSIGNED_BY_ID'] = (int)$cfg['assigned_by_id'];
foreach (['utm_source' => 'UTM_SOURCE', 'utm_medium' => 'UTM_MEDIUM', 'utm_campaign' => 'UTM_CAMPAIGN', 'utm_content' => 'UTM_CONTENT', 'utm_term' => 'UTM_TERM'] as $k => $f) {
    if (!empty($utm[$k])) $lead[$f] = mb_substr((string)$utm[$k], 0, 250);
}

// файлы спецификации (Excel + документ для печати), до 2 шт. по 1,5 МБ
$files = [];
foreach ((is_array($d['files'] ?? null) ? array_slice($d['files'], 0, 2) : []) as $f) {
    $fn = preg_replace('/[^A-Za-z0-9._-]/', '_', (string)($f['name'] ?? 'file'));
    $raw = base64_decode((string)($f['b64'] ?? ''), true);
    if ($raw !== false && strlen($raw) > 0 && strlen($raw) < 1500000 && preg_match('/\.(xlsx|html)$/', $fn)) {
        $files[] = ['name' => $fn, 'type' => substr($fn, -4) === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'text/html', 'data' => $raw];
    }
}

$sent = false; $err = ''; $leadId = 0;
if (!empty($cfg['webhook'])) {
    $ch = curl_init(rtrim($cfg['webhook'], '/') . '/crm.lead.add.json');
    curl_setopt_array($ch, [
        CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS => json_encode(['fields' => $lead, 'params' => ['REGISTER_SONET_EVENT' => 'Y']], JSON_UNESCAPED_UNICODE),
    ]);
    $res = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    $j = json_decode((string)$res, true);
    $sent = $code === 200 && !empty($j['result']);
    $leadId = $sent ? (int)$j['result'] : 0;
    // файлы — комментарием в карточке лида
    if ($leadId && $files) {
        $ch = curl_init(rtrim($cfg['webhook'], '/') . '/crm.timeline.comment.add.json');
        curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15, CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode(['fields' => ['ENTITY_ID' => $leadId, 'ENTITY_TYPE' => 'lead', 'COMMENT' => 'Спецификация с сайта',
                'FILES' => array_map(function ($f) { return [$f['name'], base64_encode($f['data'])]; }, $files)]], JSON_UNESCAPED_UNICODE)]);
        curl_exec($ch); curl_close($ch);
    }
    if (!$sent) $err = $err ?: ('Битрикс24 ответил ' . $code . ': ' . mb_substr((string)$res, 0, 300));
}

// копия в Google Таблицу (учёт заявок и эффективности рекламы). Сбой таблицы не мешает заявке.
$sheetOk = false;
if (!empty($cfg['gsheet_url'])) {
    $row = [
        'token' => (string)($cfg['gsheet_token'] ?? ''),
        'form' => $form, 'name' => $name, 'phone' => $phoneDigits ? '+' . $phoneDigits : '', 'email' => $email,
        'role' => $s('role', 100), 'object' => $s('object', 100), 'stage' => $s('stage', 100),
        'comment' => trim($s('comment', 2000) . ($s('skus', 1000) ? "\nАртикулы: " . $s('skus', 1000) : '') . ($s('docs', 300) ? "\nНужно: " . $s('docs', 300) : '')),
        'spec' => $s('spec', 5000), 'spec_total' => (int)($d['spec_total'] ?? 0), 'spec_count' => (int)($d['spec_count'] ?? 0), 'spec_link' => $s('spec_link', 3000),
        'utm_source' => mb_substr((string)($utm['utm_source'] ?? ''), 0, 200), 'utm_medium' => mb_substr((string)($utm['utm_medium'] ?? ''), 0, 200),
        'utm_campaign' => mb_substr((string)($utm['utm_campaign'] ?? ''), 0, 200), 'utm_content' => mb_substr((string)($utm['utm_content'] ?? ''), 0, 200),
        'utm_term' => mb_substr((string)($utm['utm_term'] ?? ''), 0, 200),
        'click_id' => !empty($utm['yclid']) ? 'yclid ' . mb_substr((string)$utm['yclid'], 0, 100) : (!empty($utm['gclid']) ? 'gclid ' . mb_substr((string)$utm['gclid'], 0, 100) : ''),
        'landing' => mb_substr((string)($utm['landing'] ?? ''), 0, 300), 'page' => $page, 'referrer' => $ref,
        'crm_id' => $leadId, 'crm_url' => $leadId && !empty($cfg['webhook']) ? preg_replace('#/rest/.*$#', '', $cfg['webhook']) . '/crm/lead/details/' . $leadId . '/' : '',
    ];
    // без согласования трансграничной передачи — в таблицу только аналитика, без контактов (см. lead-config.php)
    if (empty($cfg['gsheet_personal'])) { foreach (['name', 'phone', 'email', 'comment', 'spec', 'spec_link'] as $k) $row[$k] = ''; $row['name'] = $leadId ? 'см. Битрикс24' : 'см. почту'; }
    $ch = curl_init($cfg['gsheet_url']);
    curl_setopt_array($ch, [
        CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 8, CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS => json_encode($row, JSON_UNESCAPED_UNICODE),
    ]);
    $res = curl_exec($ch); curl_close($ch);
    $j = json_decode((string)$res, true);
    $sheetOk = !empty($j['ok']);
    if (!$sheetOk) $lines[] = 'Google Таблица: не записалось' . ($res ? ' (' . mb_substr(strip_tags((string)$res), 0, 120) . ')' : '');
}

// запасной путь и копия: письмо на почту
if (!empty($cfg['email']) && (!$sent || !empty($cfg['email_copy']))) {
    $subj = '=?UTF-8?B?' . base64_encode(($sent ? '' : '[не дошло до CRM] ') . $lead['TITLE']) . '?=';
    $body = ($phoneDigits ? "Телефон: +{$phoneDigits}\n" : '') . "Имя: {$name}\n" . implode("\n", $lines) . ($err ? "\n\nОшибка CRM: {$err}" : '');
    $from = $cfg['email_from'] ?? ('noreply@' . ($_SERVER['HTTP_HOST'] ?? 'adalight.ru'));
    if ($files) {
        $b = '=_ada_' . md5(uniqid('', true));
        $msg = "--{$b}\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n"
            . chunk_split(base64_encode($body . "\n\nВо вложении — спецификация: Excel и документ для печати (открыть в браузере → Печать / Сохранить в PDF)."));
        foreach ($files as $f) {
            $msg .= "--{$b}\r\nContent-Type: {$f['type']}; name=\"{$f['name']}\"\r\nContent-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename=\"{$f['name']}\"\r\n\r\n" . chunk_split(base64_encode($f['data']));
        }
        $msg .= "--{$b}--";
        $mailed = @mail($cfg['email'], $subj, $msg, "From: {$from}\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary=\"{$b}\"");
    } else {
        $mailed = @mail($cfg['email'], $subj, $body, "From: {$from}\r\nContent-Type: text/plain; charset=utf-8");
    }
    if (!$sent) $sent = $mailed;
}

($sent || $sheetOk) ? reply(200, 'ok') : reply(502, 'Не удалось отправить');

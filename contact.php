<?php
/**
 * Kernow Decking Co. — quote form handler for Hostinger (authenticated SMTP).
 *
 * Credentials come from smtp-config.php, which must never be committed.
 * contact.php looks in this order:
 *   1. The directory above the web root (recommended on Hostinger,
 *      e.g. /home/u562292805/domains/kernowdecking.com/smtp-config.php)
 *   2. A gitignored smtp-config.php next to this file
 *
 * Copy smtp-config.example.php to one of those paths and set the mailbox
 * password. When the site is first uploaded to Hostinger, upload
 * smtp-config.php as well — it is not in git.
 */

declare(strict_types=1);

require_once __DIR__ . '/lib/PHPMailer/Exception.php';
require_once __DIR__ . '/lib/PHPMailer/PHPMailer.php';
require_once __DIR__ . '/lib/PHPMailer/SMTP.php';

use PHPMailer\PHPMailer\Exception as MailException;
use PHPMailer\PHPMailer\PHPMailer;

header('X-Content-Type-Options: nosniff');
$wantsJson = isset($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false;
$THANK_YOU = 'thank-you.html';

function respond(bool $ok, string $msg, bool $wantsJson, string $thankYou): void {
    if ($wantsJson) {
        header('Content-Type: application/json; charset=utf-8');
        http_response_code($ok ? 200 : 400);
        echo json_encode($ok ? ['ok' => true] : ['ok' => false, 'error' => $msg]);
    } else if ($ok) {
        header('Location: ' . $thankYou, true, 303);
    } else {
        http_response_code(400);
        header('Content-Type: text/html; charset=utf-8');
        echo '<!doctype html><meta charset="utf-8"><title>Form error</title><p style="font-family:sans-serif">'
           . htmlspecialchars($msg, ENT_QUOTES, 'UTF-8') . ' <a href="contact.html">Go back</a></p>';
    }
    exit;
}

function load_smtp_config(): array {
    $candidates = [
        dirname(__DIR__) . '/smtp-config.php',
        __DIR__ . '/smtp-config.php',
    ];
    foreach ($candidates as $path) {
        if (!is_readable($path)) {
            continue;
        }
        $config = require $path;
        if (!is_array($config)) {
            continue;
        }
        foreach (['host', 'port', 'username', 'password', 'from_email', 'from_name', 'to_email'] as $key) {
            if (empty($config[$key])) {
                continue 2;
            }
        }
        if ($config['password'] === 'REPLACE_WITH_MAILBOX_PASSWORD') {
            continue;
        }
        return $config;
    }
    throw new RuntimeException('SMTP configuration is missing.');
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Location: contact.html', true, 303);
    exit;
}

function field(string $k, int $max = 200): string {
    $v = isset($_POST[$k]) ? trim((string) $_POST[$k]) : '';
    $v = str_replace(["\r", "\0"], '', $v);
    return mb_substr($v, 0, $max);
}

// Spam checks: honeypot + minimum time on page
if (field('company') !== '') respond(true, '', $wantsJson, $THANK_YOU);
$ts = (int) field('ts', 20);
if ($ts > 0 && (time() - $ts) < 3) respond(false, 'Please take a moment to check your details and try again.', $wantsJson, $THANK_YOU);

$name     = field('name', 100);
$phone    = field('phone', 30);
$email    = field('email', 150);
$postcode = strtoupper(field('postcode', 10));
$type     = field('project_type', 80);
$message  = field('message', 3000);
$consent  = field('consent', 5);
$source   = field('source', 120);

$errors = [];
if ($name === '')                                  $errors[] = 'name';
if (strlen(preg_replace('/\D/', '', $phone)) < 10) $errors[] = 'phone';
if (!filter_var($email, FILTER_VALIDATE_EMAIL))    $errors[] = 'email';
if (!preg_match('/^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/', $postcode)) $errors[] = 'postcode';
if ($type === '')                                  $errors[] = 'project type';
if ($message === '')                               $errors[] = 'message';
if ($consent !== 'yes')                            $errors[] = 'consent';
if ($errors) respond(false, 'Please check: ' . implode(', ', $errors) . '.', $wantsJson, $THANK_YOU);

// Strip anything that could inject headers
$safeName  = preg_replace('/[\r\n<>"]+/', ' ', $name);
$safeEmail = preg_replace('/[\r\n]+/', '', $email);

$subject = "New decking quote request: $type ($postcode)";
$body  = "New enquiry from the Kernow Decking Co. website\n";
$body .= str_repeat('-', 40) . "\n";
$body .= "Name:         $name\n";
$body .= "Phone:        $phone\n";
$body .= "Email:        $email\n";
$body .= "Postcode:     $postcode\n";
$body .= "Project type: $type\n";
$body .= "Page:         $source\n\n";
$body .= "Message:\n$message\n\n";
$body .= str_repeat('-', 40) . "\n";
$body .= 'Sent: ' . date('d/m/Y H:i') . ' | IP: ' . ($_SERVER['REMOTE_ADDR'] ?? '') . "\n";

try {
    $config = load_smtp_config();
} catch (Throwable $e) {
    respond(false, 'Sorry, we could not send your message just now. Please call or email us directly.', $wantsJson, $THANK_YOU);
}

$mail = new PHPMailer(true);
try {
    $mail->CharSet  = 'UTF-8';
    $mail->Encoding = 'base64';
    $mail->isSMTP();
    $mail->Host       = $config['host'];
    $mail->Port       = (int) $config['port'];
    $mail->SMTPAuth   = true;
    $mail->Username   = $config['username'];
    $mail->Password   = $config['password'];
    $encryption       = strtolower((string) ($config['encryption'] ?? 'ssl'));
    $mail->SMTPSecure = ($encryption === 'tls') ? PHPMailer::ENCRYPTION_STARTTLS : PHPMailer::ENCRYPTION_SMTPS;

    $mail->setFrom($config['from_email'], $config['from_name']);
    $mail->addAddress($config['to_email']);
    $mail->addReplyTo($safeEmail, $safeName);
    $mail->Subject = $subject;
    $mail->isHTML(false);
    $mail->Body    = $body;

    $mail->send();
} catch (MailException $e) {
    respond(false, 'Sorry, we could not send your message just now. Please call or email us directly.', $wantsJson, $THANK_YOU);
}

respond(true, '', $wantsJson, $THANK_YOU);

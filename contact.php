<?php
/**
 * Kernow Decking Co. — quote form handler for Hostinger (PHP mail()).
 *
 * EDIT THESE THREE SETTINGS:
 *   $TO_EMAIL   – where enquiries are delivered (your inbox)
 *   $FROM_EMAIL – must be an address ON YOUR DOMAIN (create it in Hostinger > Emails),
 *                 otherwise many providers will reject or spam-folder the message.
 */
$TO_EMAIL   = '[EMAIL]';
$FROM_EMAIL = 'no-reply@[DOMAIN]';
$SITE_NAME  = 'Kernow Decking Co.';
$THANK_YOU  = 'thank-you.html';

// ---------------------------------------------------------------------------
header('X-Content-Type-Options: nosniff');
$wantsJson = isset($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false;

function respond($ok, $msg, $wantsJson, $thankYou) {
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
           . htmlspecialchars($msg) . ' <a href="index.html#contact">Go back</a></p>';
    }
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: index.html#contact', true, 303);
    exit;
}

function field($k, $max = 200) {
    $v = isset($_POST[$k]) ? trim((string)$_POST[$k]) : '';
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

$subject = "New quote request: $type ($postcode)";
$body  = "New enquiry from the $SITE_NAME website\n";
$body .= str_repeat('-', 40) . "\n";
$body .= "Name:         $name\n";
$body .= "Phone:        $phone\n";
$body .= "Email:        $email\n";
$body .= "Postcode:     $postcode\n";
$body .= "Project type: $type\n\n";
$body .= "Message:\n$message\n\n";
$body .= str_repeat('-', 40) . "\n";
$body .= 'Sent: ' . date('d/m/Y H:i') . ' | IP: ' . ($_SERVER['REMOTE_ADDR'] ?? '') . "\n";

$headers  = "From: $SITE_NAME <$FROM_EMAIL>\r\n";
$headers .= "Reply-To: $safeName <$safeEmail>\r\n";
$headers .= "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
$headers .= "X-Mailer: PHP/" . phpversion();

$sent = @mail($TO_EMAIL, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $headers, '-f' . $FROM_EMAIL);

if (!$sent) respond(false, 'Sorry, we could not send your message just now. Please call or email us directly.', $wantsJson, $THANK_YOU);
respond(true, '', $wantsJson, $THANK_YOU);

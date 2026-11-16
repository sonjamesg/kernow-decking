<?php
/**
 * Copy this file to smtp-config.php (gitignored) and fill in the mailbox password.
 *
 * On Hostinger, the safest place is one directory above the web root, for example:
 *   /home/u562292805/domains/kernowdecking.com/smtp-config.php
 * with the site itself in public_html/. contact.php looks there first.
 *
 * A gitignored copy inside the web root also works. .htaccess blocks HTTP access
 * to smtp-config.php, but keep it out of git either way.
 *
 * Do not commit smtp-config.php. Do not put the password in this example file.
 */
return [
    'host'       => 'smtp.hostinger.com',
    'port'       => 465,
    'encryption' => 'ssl', // implicit TLS on port 465
    'username'   => 'info@kernowdecking.com',
    'password'   => 'REPLACE_WITH_MAILBOX_PASSWORD',
    'from_email' => 'info@kernowdecking.com',
    'from_name'  => 'Kernow Decking Co.',
    'to_email'   => 'info@kernowdecking.com',
];

# Old PHP for archiving legacy WordPress 3.x / Joomla 3.x sites locally (never exposed publicly)
FROM php:5.6-apache
RUN docker-php-ext-install mysql mysqli pdo_mysql \
 && a2enmod rewrite \
 && printf '<Directory /var/www/html>\n  AllowOverride All\n</Directory>\n' > /etc/apache2/conf-enabled/override.conf \
 && printf 'display_errors=Off\nlog_errors=On\nerror_reporting=E_ALL & ~E_DEPRECATED & ~E_STRICT & ~E_NOTICE\nmemory_limit=256M\n' > /usr/local/etc/php/conf.d/archive.ini

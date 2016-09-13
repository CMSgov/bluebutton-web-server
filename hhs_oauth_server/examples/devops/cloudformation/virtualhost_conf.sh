#!/usr/bin/env bash
echo "    WSGISocketPrefix /var/run/modwsgi ">/etc/httpd/virtualhost/server.conf
echo "  ">>/etc/httpd/virtualhost/server.conf
echo "    WSGIApplicationGroup %{GLOBAL}" >>/etc/httpd/virtualhost/server.conf
echo "    WSGIPythonHome $PY_VENV ">>/etc/httpd/virtualhost/server.conf
echo "    WSGIPythonPath $PY_APP_HOME:$PY_VENV/bin:/usr/local/bin:$PY_APP_HOME:$PY_VENV/lib/python3.5/site-packages  ">>/etc/httpd/virtualhost/server.conf

echo "<VirtualHost *:80> ">>/etc/httpd/virtualhost/server.conf
echo "    ServerAdmin webmaster@$PY_SERVER ">>/etc/httpd/virtualhost/server.conf
echo "    DocumentRoot /var/www/doc/$PY_SERVER ">>/etc/httpd/virtualhost/server.conf
    
echo "    ErrorLog logs/$PY_SERVER-error_log ">>/etc/httpd/virtualhost/server.conf
echo "    CustomLog logs/$PY_SERVER-access_log common ">>/etc/httpd/virtualhost/server.conf
    
echo "    LogLevel warn ">>/etc/httpd/virtualhost/server.conf

echo "    ServerName $PY_SERVER ">>/etc/httpd/virtualhost/server.conf
    
echo "    WSGIDaemonProcess apache user=pyapps group=apache threads=10 python-path=$PY_VENV/bin:/usr/local/bin:$PY_APP_HOME:$PY_VENV/lib/python3.5/site-packages ">>/etc/httpd/virtualhost/server.conf 

echo "    WSGIProcessGroup apache ">>/etc/httpd/virtualhost/server.conf

echo "    WSGIScriptAlias / $PY_APP_HOME/hhs_oauth_server/hhs_oauth_server/wsgi.py ">>/etc/httpd/virtualhost/server.conf

echo "    # Directory specification needed to allow apache to load wsgi.py ">>/etc/httpd/virtualhost/server.conf
echo "    # Directory  to point to folder where wsgi.py stored ">>/etc/httpd/virtualhost/server.conf
echo "    <Directory $PY_APP_HOME/hhs_oauth_server/hhs_oauth_server> ">>/etc/httpd/virtualhost/server.conf
echo "	Order deny,allow ">>/etc/httpd/virtualhost/server.conf
echo "	Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "    </Directory> ">>/etc/httpd/virtualhost/server.conf
echo "    <Directory $PY_APP_HOME/hhs_oauth_server/hhs_oauth_server/settings> ">>/etc/httpd/virtualhost/server.conf
echo "	Order deny,allow ">>/etc/httpd/virtualhost/server.conf
echo "	Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "    	<Files base.py > ">>/etc/httpd/virtualhost/server.conf
echo "	    Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "	</Files> ">>/etc/httpd/virtualhost/server.conf
echo "	<Files production.py> ">>/etc/httpd/virtualhost/server.conf
echo "	    Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "	</Files> ">>/etc/httpd/virtualhost/server.conf
echo "    </Directory> ">>/etc/httpd/virtualhost/server.conf
   
echo "    Alias /static/ $PY_APP_HOME/hhs_oauth_server/collectedstatic/ ">>/etc/httpd/virtualhost/server.conf
echo "    Alias /media/  $PY_APP_HOME/hhs_oauth_server/media/ ">>/etc/httpd/virtualhost/server.conf
echo "    <Directory      $PY_APP_HOME/hhs_oauth_server/collectedstatic> ">>/etc/httpd/virtualhost/server.conf
echo "	# Apache 2.4 command: ">>/etc/httpd/virtualhost/server.conf
echo "       # Require all granted ">>/etc/httpd/virtualhost/server.conf
echo "	# Apache 2.2 commands: ">>/etc/httpd/virtualhost/server.conf
echo "	Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "	Order deny,allow ">>/etc/httpd/virtualhost/server.conf
echo "    </Directory> ">>/etc/httpd/virtualhost/server.conf

echo "    <Directory      $PY_APP_HOME/hhs_oauth_server/media> ">>/etc/httpd/virtualhost/server.conf
echo "	# Apache 2.4 command: ">>/etc/httpd/virtualhost/server.conf
echo "        # Require all granted ">>/etc/httpd/virtualhost/server.conf
echo "        # Apache 2.2 commands: ">>/etc/httpd/virtualhost/server.conf
echo "        Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "        Order deny,allow ">>/etc/httpd/virtualhost/server.conf

echo "    </Directory> ">>/etc/httpd/virtualhost/server.conf

echo "    <Directory $PY_APP_HOME/hhs_oauth_server> ">>/etc/httpd/virtualhost/server.conf
echo "	Order allow,deny ">>/etc/httpd/virtualhost/server.conf
echo "	Allow from all ">>/etc/httpd/virtualhost/server.conf
echo "    </Directory>  ">>/etc/httpd/virtualhost/server.conf
echo "</VirtualHost>  ">>/etc/httpd/virtualhost/server.conf



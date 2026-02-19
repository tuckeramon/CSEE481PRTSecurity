FROM mysql:8.0.42

ENV MYSQL_ROOT_PASSWORD=password \
    MYSQL_DATABASE=prt_system

# Basic PRT table skeleton
COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 3306

# TODO: Add your custom tables and data here
# See README.md for examples
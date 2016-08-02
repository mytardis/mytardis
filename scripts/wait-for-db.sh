#!/bin/bash

if [ ! -v DB_ENGINE ]
then
    DB_ENGINE="postgres"
fi

if [[ $DB_ENGINE == "postgres" ]]
then
    until nc -z db 5432; do
        echo "$(date) - waiting for $DB_ENGINE..."
        sleep 1
    done
elif [[ $DB_ENGINE == "mysql" ]]
then
    until nc -z mysql 3306; do
        echo "$(date) - waiting for $DB_ENGINE..."
        sleep 1
    done
fi


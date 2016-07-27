#!/bin/bash

DB_ENGINE=`echo $DATABASE_URL | cut -d : -f 1`

if [[ $DB_ENGINE == "postgres" ]]
then
    until nc -z pg 5432; do
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


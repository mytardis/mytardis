#!/bin/sh

DJANGO=/home/tardis/bin/django
SCHEMA_FILE=/home/tardis/solr-schema.xml
TMP_SCHEMA_FILE=/tmp/solr-schema.xml
LOG_FILE=/home/tardis/solr-indexing.log

if [ ! -f $SCHEMA_FILE ]; then
    touch $SCHEMA_FILE >/dev/null 2>&1
fi

$DJANGO build_solr_schema 2>/dev/null > $TMP_SCHEMA_FILE
diff -q $SCHEMA_FILE $TMP_SCHEMA_FILE >/dev/null 2>&1
if [ $? -eq 1 ]; then
    date >> $LOG_FILE
    echo "Schema changed... updating $SCHEMA_FILE." >> $LOG_FILE
    cp $TMP_SCHEMA_FILE $SCHEMA_FILE >> $LOG_FILE 2>&1
    # reload solr to pick up the schema changes.
    curl -n --silent "http://localhost:8080/manager/reload?path=/solr" >> $LOG_FILE 2>&1
    echo "Rebuilding solr index." >> $LOG_FILE
    $DJANGO rebuild_index --noinput >> $LOG_FILE 2>&1
    echo "Rebuild finished at `date`" >> $LOG_FILE
fi


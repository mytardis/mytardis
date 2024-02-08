# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
SYSTEM_LOG_LEVEL = "INFO"
MODULE_LOG_LEVEL = "INFO"

SYSTEM_LOG_FILENAME = "request.log"
MODULE_LOG_FILENAME = "tardis.log"

# Rollover occurs whenever the current log file is nearly maxBytes in length;
# if maxBytes is zero, rollover never occurs
SYSTEM_LOG_MAXBYTES = 0
MODULE_LOG_MAXBYTES = 0

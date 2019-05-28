.. _ref-filterframework:

Filter Setup
============

Filters are called once a file object has verified.

The DataFileObject's verify method submits a task called "mytardis.apply_filters"
to the message broker (RabbitMQ).

This task can be picked up by the "mytardis-filters" microservice:
https://github.com/mytardis/mytardis-filters or by your own custom microservice.

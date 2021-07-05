*** Settings ***

Library     DjangoLibrary
Library     SeleniumLibrary

*** Keywords ***

CreateUer
    djangolibrary.create superuser    ('testUser',


*** Variables ***

${HOSTNAME}             127.0.0.1
${PORT}                 55001
${SERVER}               http://${HOSTNAME}:${PORT}/
${BROWSER}              firefox


*** Settings ***

Documentation   Django Robot Tests
Library         SeleniumLibrary  timeout=10  implicit_wait=0
Library         DjangoLibrary  ${HOSTNAME}  ${PORT}  path=mysite/mysite  manage=mysite/manage.py  settings=mysite.settings


*** Keywords ***

Start Django and open Browser
  Start Django
  Open Browser  ${SERVER}  ${BROWSER}

Stop Django and close browser
  Close Browser
  Stop Django


*** Test Cases ***

Scenario: As a visitor I can visit the django default page
  Go To  ${SERVER}
  Wait until page contains element  id=explanation
  Page Should Contain  It worked!
  Page Should Contain  Congratulations on your first Django-powered page.
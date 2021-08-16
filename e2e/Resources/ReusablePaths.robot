*** Variables ***

${Sharing}                  xpath://*[@title='Sharing']
${ChngUserSharing}          xpath://*[@class='share_link btn btn-outline-secondary btn-sm' and @title='Change']
${User}                     id:id_entered_user
${PermissionsList}          id:id_permission
${AddUser}                  id:user

${ChngPublicAccess}         xpath://*[@class='public_access_button btn btn-outline-secondary btn-sm' and @title='Change']
${PublicAccess}             id:id_public_access

${ChngGroupSharing}         xpath://*[@class='share_link_group btn btn-outline-secondary btn-sm' and @title='Change']
${Group}                    id:id_group
${GroupPermissionsList}     id:id_permission_group
${AddGroupbtn}              id:group
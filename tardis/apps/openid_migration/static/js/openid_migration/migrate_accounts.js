var verify_my_account = function() {
  var username = $("#id_username").val();
  var password = $("#id_password").val();
  var authenticationMethod = $("#id_authenticationMethod").val();

    if (username != "" && password != "") {
      var data = {operation: 'addAuth', username: username, password: password, authenticationMethod: authenticationMethod,
                  csrfmiddlewaretoken: $("#csrf-token").val()
      };
      $.post("/apps/openid-migration/migrate-accounts/", data, function(data) {
          var status = data.status;
          if (status == "confirm") {
              $("#authForm").css('display','none')
              $('.alert-info').css('display','none')
              $("#confirm-migrate").css('display','block')
              update_user_data(data)
          } else {
            display_error(data.errorMessage, $("#authForm"));
          }
      }, "json");
    }
    else {
        display_error("You need to provide all the necessary information to authenticate.", $("#authForm"));
    }
  return false;
};

var update_user_data = function (data) {
    $("#current_user_email").append(data.data.new_user_email)
    $("#old_username").append('<td>'+data.data.old_username+'</td')
    $("#old_email").append('<td>'+data.data.old_user_email+'</td')
}

var migrate_account= function () {
    $("#spinner").css('display', 'block')
    $("#confirm-migrate").css('opacity','.5')
    var username = $("#id_username").val();
    var password = $("#id_password").val();
    var authenticationMethod = $("#id_authenticationMethod").val();
    var data = {
        operation: 'migrateAccount', username: username, password: password, authenticationMethod: authenticationMethod,
        csrfmiddlewaretoken: $("#csrf-token").val()
    }
        $.post("/apps/openid-migration/migrate-accounts/", data, function(data) {
                var status = data.status
                if (status == "success") {
                    $("#spinner").css('display', 'none')
                    $("#confirm-migrate").css('display','none')
                    $("#message").css('display','none')
                    $("#migration-success-message").css('display','block')
                    $("#migration-success-message span span").text(data.data['auth_method'])
                }
                else {
                    $("#spinner").css('display', 'none')
                    $("#confirm-migrate").css('display','none')
                    $("#message").css('display','none')
                    $("#migration-failed-message").css('display','block')
                }
              }, "json");
}

var display_error = function(msg, elem) {
  // Create box from template
  var msgBox = $('#template-block .alert-error-msg').clone();
  // Fill in error message
  msgBox.find('.msg').text(msg);
  // Insert into DOM
  msgBox.insertBefore(elem).fadeIn("slow").animate({opacity: 1.0}, 5000).fadeOut("slow",function() { msgBox.remove(); });
};

$(document).ready(function() {
    $("#verify-my-account").click(verify_my_account);
    $("#confirm_true").click(migrate_account)
});

/**
 * Modulo JS para Productos
 * @author dgonzalez
 */

function check_watch_callback(data) {
   if(data && data.variable) {
      $('#notificaciones_count').attr('class', 'label label-default').html('0');
      hideWait();
   }
};

function check_watch() {
   //showWait();
   Dajaxice.emisor_receptor.check_watch(check_watch_callback, {'variable':'A'});
};

$(document).ready(function() {
   $('#notificaciones_button').click(function() {
      var counter = $('#notificaciones_count').html();
      if (counter != '0') {
         check_watch();
      }
   });
});

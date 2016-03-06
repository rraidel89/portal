/**
 * Modulo de JS Reportes
 */

function filter_reporte_general_form() {
   showWait();
   $('#filter_reporte_general_button').prop('disabled', true);
   setTimeout(function() {$('#filter_reporte_general_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_reporte_general_form(Dajax.process,{'form':$('#filtro_reporte_general_form').serialize()});
   return false;
};

function filter_reporte_individual_form() {
   showWait();
   $('#filter_reporte_individual_button').prop('disabled', true);
   setTimeout(function() {$('#filter_reporte_individual_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_reporte_individual_form(Dajax.process,{'form':$('#filtro_reporte_individual_form').serialize()});
   return false;
};

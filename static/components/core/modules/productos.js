/**
 * Modulo JS para Productos
 * @author dgonzalez
 */

var categoria_field_name = '';
var subcategoria_field_name = '';

function cargar_sub_categorias_callback(data) {
   if(data && data.subcategorias.length > 0) {
        renderSelectOptions(subcategoria_field_name, data.subcategorias);
   }
   hideWait();
};

function cargar_sub_categorias(categoria_field, subcategoria_field) {
   categoria_field_name = categoria_field;
   subcategoria_field_name = subcategoria_field;
   var nombre_categoria = $('#'+categoria_field_name).val();
   console.log("nombre_categoria = "+nombre_categoria+" categoria_field_name="+categoria_field_name);
   Dajaxice.emisor_receptor.cargar_sub_categorias(cargar_sub_categorias_callback, {'nombre_categoria':nombre_categoria} );
   showWait();
};

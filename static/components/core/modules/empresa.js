/**
 * Modulo JS para Empresa
 * @author dgonzalez
 */

var categoria_empresa_field_name = '';
var subcategoria_empresa_field_name = '';

function cargar_sub_categorias_empresa_callback(data) {
   if(data && data.subcategorias.length > 0) {
        renderSelectOptions(subcategoria_empresa_field_name, data.subcategorias);
   }
   hideWait();
};

function cargar_sub_categorias_empresa(categoria_field, subcategoria_field) {
   categoria_empresa_field_name = categoria_field;
   subcategoria_empresa_field_name = subcategoria_field;
   var nombre_categoria = $('#'+categoria_empresa_field_name).val();
   Dajaxice.emisor_receptor.cargar_sub_categorias_empresa(cargar_sub_categorias_empresa_callback, {'nombre_categoria':nombre_categoria} );
   showWait();
};

function cargar_provincias_pais_callback(data) {
   if(data && data.provincias.length > 0) {
        renderSelectOptions('id_provincia', data.provincias);
   }
   hideWait();
};

function cargar_provincias_pais() {
   var nombre_pais = $('#id_pais').val();
   Dajaxice.emisor_receptor.cargar_provincias_pais(cargar_provincias_pais_callback, {'nombre_pais':nombre_pais} );
   showWait();
};

function cargar_ciudades_provincia_callback(data) {
   if(data && data.ciudades.length > 0) {
        renderSelectOptions('id_ciudad', data.ciudades);
   }
   hideWait();
};

function cargar_ciudades_provincia() {
   var nombre_provincia = $('#id_provincia').val();
   Dajaxice.emisor_receptor.cargar_ciudades_provincia(cargar_ciudades_provincia_callback, {'nombre_provincia':nombre_provincia} );
   showWait();
};

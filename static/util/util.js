//Funcion que genera los valores para la suma del catcha
function cargarNum(btn, btn2, txt, txtres){
    var num1= Math.floor((Math.random()*8)+1);
    var numAuxiliar = 9 - num1;
    var num2= Math.floor((Math.random()*numAuxiliar)+1);
    var resultado= num1+num2;
    document.getElementById(btn).innerHTML = num1;
    document.getElementById(btn2).innerHTML = num2;
    document.getElementById(txt).value = resultado;
    document.getElementById(txtres).value = null;
}


//Funcion lee los datos que el usuario da como resultad de la suma
function leerDatos(btn, text){
    var resultado = document.getElementById(text).value;
    var dato = document.getElementById(btn).innerHTML;
    resultado = resultado+dato;
    document.getElementById(text).value = resultado;
}


//Función que retorna el resultado de la validación del catcha
function resCatcha(txt, txt2){
    var val_calculo = document.getElementById(txt).value;
    var val_resultado = document.getElementById(txt2).value;
    if (val_calculo == val_resultado){
        return true;
    }else{
    	window.location.href=window.location.href;
    	return false;
    }

}

function utilidades() {
    $(document).ready(function () {
        $('.datepicker').datepicker({
            format: "yyyy-mm-dd"
        });

        $(".sucursal").tooltip({ placement: 'top'});
        $(".cliente").tooltip({ placement: 'top'});
        $(".copiar").tooltip({ placement: 'top'});
        $(".emisor").tooltip({ placement: 'top'});

        $('#btnGuardarBanner').click(function (e) {
            e.preventDefault();
            $('form#frmBanner').submit();
        });

        $('#btnCrearCampaniaEmail').click(function (e) {
            e.preventDefault();
            $('form#frmCampaniaEmail').submit();
        });


        $('#btnCrearSms').click(function (e) {
            e.preventDefault();
            $('form#frmCampaniaSMS').submit();
        });

        $('#btnCrearCupon').click(function (e) {
            e.preventDefault();
            $('form#frmCupon').submit();
        });

        $('#btnCrearProducto').click(function (e) {
            e.preventDefault();
            $('form#frmProducto').submit();
        });

        $('#btnCopiar').attr('title', 'doble click para copiar');

        var comprob = '';
        $('.conf-comp').click(function () {
            comprob = this.id;
        });

	// ver banner
        var imagen_banner = '';
        $('.banner_preview').click(function (e) {
            e.preventDefault();
            imagen_banner = this.value;
            $('#img_banner').attr('src',imagen_banner);
        });

        $('#preview_sms').click(function(e){
            e.preventDefault();
            var textSms = $("#id_mensaje").val();
             $('#preview_mensaje_sms').text(textSms);
        })

        $('.btnPreviewEmail').click(function(e){
            e.preventDefault();
            var img_banner = $(this).find(".img_banner").val()
            var txt_banner = $(this).find(".txt_banner").val();
            var subject_email = $(this).find(".subject_email").val();

            $('#subject_email_prev').text(subject_email);            
            $('#prev_banner_email').attr('src',img_banner);
	    $('#txttexto_prev').html(txt_banner);
        })

        function readURL(input, id_obj) {
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    $(id_obj).attr('src', e.target.result);
                }
                reader.readAsDataURL(input.files[0]);
            }
        }

        $("#id_imagen").change(function () {
            readURL(this, '#prev_banner');
        });
/*
        $("#id_banner_superior").change(function () {
             readURL(this, '#prev_banner_email');
        });

        $("#id_img_principal").change(function () {
             readURL(this, '#prev_imgprc_email');
        });

        $("#id_img_secundaria").change(function () {
             readURL(this, '#prev_imgsec_email');
        });
*/
        $('#btn_preview_email').click(function(e){
            e.preventDefault();
            var texto = $("#id_texto").val();
            $('#txttexto_prev').text(texto);
	    var img_prin = $(this).find(".img_prin").val();
	    $('#prev_banner_email').attr('src',img_prin);
        });

        $('#btnConfGuardarSms').click(function(e){
            e.preventDefault();
            var textbanner = $("#id_fecha_publicacion").val();
            $('#orden_date_publ').text(textbanner);
        });


    });


}




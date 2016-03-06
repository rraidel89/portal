function cloneMore(selector, type, selectables) {
    var newElement = $(selector).clone(true);
    var total = parseInt($('#id_' + type + '-TOTAL_FORMS').val());
    var max_forms = parseInt($('#id_' + type + '-MAX_NUM_FORMS').val());
     
    if(total < max_forms) {
        
        newElement.find(':input').each(function() {
            
            var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });
           
        try {
            newElement.find('a.last_delete_item_factura').each(function() {
               $(this).attr('onClick','pregunta(this,'+"'"+''+type+''+"'"+', '+"'"+'item'+"'"+', '+"'"+'item_factura'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('a.delete_item_retencion').each(function() {
               
               $(this).attr('onClick','pregunta_retencion(this,'+"'"+''+type+''+"'"+', '+"'"+'item'+"'"+', '+"'"+'item_impuesto_retencion'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('a.delete_info_adicional').each(function() {
               
               $(this).attr('onClick','preguntainfo(this,'+"'"+''+type+''+"'"+', '+"'"+'item-info-adi'+"'"+', '+"'"+'item-info-adi'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('a.delete_gui_remision_pro').each(function() {
               
               $(this).attr('onClick','pregunta_guia_remision(this,'+"'"+''+type+''+"'"+', '+"'"+'item-dest-prod'+"'"+', '+"'"+'item-gr-prod'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('a.last_delete_item_nota_credito').each(function() {
               
               $(this).attr('onClick','pregunta_nota_credito(this,'+"'"+''+type+''+"'"+', '+"'"+'item'+"'"+', '+"'"+'item_nota_credito'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('a.delete_nota_debito_impuesto').each(function() {
               
               $(this).attr('onClick','pregunta_nota_debito(this,'+"'"+''+type+''+"'"+', '+"'"+'item_impuestos'+"'"+', '+"'"+'item_nota_debito_impuesto'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('a.delete_nota_debito_motivos').each(function() {
               
               $(this).attr('onClick','pregunta_nota_debito(this,'+"'"+''+type+''+"'"+', '+"'"+'item_motivos'+"'"+', '+"'"+'item_nota_debito_motivos'+"'"+', '+"'"+'None'+"'"+' );');
            });
            
            newElement.find('label').each(function() {
                
                var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
                $(this).attr('for', newFor);
            });
        }catch(e) {
            console.log(e);
        }
        
        total++;
        $('#id_' + type + '-TOTAL_FORMS').val(total);
        $(selector).after(newElement);
        
        if(selectables) {
            try {
                window.bindSelectables('body');
            }catch(e) {console.log(e);}
            $('.datepicker').datepicker({dateFormat: "dd/mm/yy"});
        }
    }
    else {
        alert('El límite es '+max_forms);
    }
    return false;
};

function deleteForm(btn, prefix, itemsName) {
    console.log("--Borrando "+prefix+", "+itemsName);
    var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    if (formCount > 1) {
        console.log("Borrando "+prefix+", "+itemsName);
        // Delete the item/form
        $(btn).parents('tr').remove();
        console.log($(btn));
        var forms = $('.'+itemsName); // Get all the forms  
        // Update the total number of forms (1 less than before)
        $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
        var i = 0;
        // Go through the forms and set their indices, names and IDs
        //console.log('deleteForm - Borrado, actualizando...');
        //console.log(prefix);
        //console.log(this);
        for (formCount = forms.length; i < formCount; i++) {
            $(forms.get(i)).children().children().each(function () {
                if ($(this).attr('type') == 'text' || $(this).attr('type') == 'hidden' || $(this).is("select"))
                    updateElementIndex(this, prefix, i);
            });
        }
        //console.log($(forms.get(1)).children().children());
        try {
            if ( after_remove_form ) after_remove_form(prefix);
        }catch(e) {}
    } // End if
    else {
        //console.log('Al menos un item');
        return true;
    }
    return false;
};


function deleteAll(selector, prefix, itemsName) {
    while(!deleteLastForm(selector, prefix, itemsName, true, true)) {
        console.log('- Borrando '+selector);
    };
};

function deleteLastForm(selector, prefix, itemsName, noUpdate, justOne) {
    
    var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    if (formCount > 1) {
        // Delete the item/form
        if(justOne) {
            $(selector).first().remove();
        }
        else {
            $(selector).remove();
        }
        var forms = $('.'+itemsName); // Get all the forms  
        // Update the total number of forms (1 less than before)
        $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
        
        if(!noUpdate) {
            var i = 0;
            // Go through the forms and set their indices, names and IDs
            for (formCount = forms.length; i < formCount; i++) {
                $(forms.get(i)).children().children().each(function () {
                    if ($(this).attr('type') == 'text' || $(this).attr('type') == 'hidden'
                     || $(this).is("select")) updateElementIndex(this, prefix, i);
                });
            }
        }
        
    } // End if
    else {
        console.log('deleteLastForm - Al menos un item');
        return true;
    }
    return false;
};




function updateElementIndex(el, prefix, ndx) {
    //console.log(el);
    //console.log(prefix);
    //console.log(ndx);
    var id_regex = new RegExp('(' + prefix + '-\\d+)');
    var replacement = prefix + '-' + ndx;
    //console.log(id_regex);
    //console.log(el);
    if ($(el).attr("for")){ console.log("entri if 1"); $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));}
    if (el.id)el.id = el.id.replace(id_regex, replacement);
    if (el.name) el.name = el.name.replace(id_regex, replacement);
    
};
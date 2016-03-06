import xlrd

__author__ = 'amarcillo'


def leer_desde_xls(file_name):
    try:
        with xlrd.open_workbook(file_name) as wb:
            # elegir primera hoja
            worksheet = wb.sheet_by_index(0)
            # leer numero de filas y establecer la fila actual a 0 (primera)
            num_rows, curr_row = worksheet.nrows, 0 # - 1
            # recuperas los valores de la fila
            #key_values = [x.value for x in worksheet.col[0]]#.row(0)]
            # construir un dict
            #data = dict((x, []) for x in key_values)
            #print 'leer_desde_xls - Leyendo desde XLS', data, 'numero de filas', num_rows, 'Fila actual', curr_row
            # iterar a traves de las filas y llenas el diccionario
            data = []
            while curr_row < num_rows:
                print 'leer_desde_xls - Ingresando a la fila', curr_row
                cell_value = worksheet.cell_value(curr_row, 0)
                print 'leer_desde_xls - Value', cell_value
                data.append(cell_value)                
                curr_row += 1                
                '''
                for idx, val in enumerate(worksheet.row(curr_row)):
                    if val.value.strip():
                        print 'leer_desde_xls --> Dato', curr_row, '=', val.value
                        data[key_values[idx]].append(val.value)
                '''
            return data
    except Exception as e:
        print 'Error al leer archivo xls', e


def leer_desde_txt(file_name):
    with open(file_name, 'r') as f:
        items = [line.strip() for line in f]
        print '---'
    for item in items:
        print item
    return items


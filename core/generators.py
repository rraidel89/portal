import os
import random
import string
import csv
import sys

class RandomCodes(object):

    @staticmethod
    def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
    
    @staticmethod
    def digit(num_from, num_to):
        return random.randint(num_from, num_to)
    
class CuponCodesGenerator(object):
    
    @staticmethod
    def verifyCuponCodesEmpty(cupon):
        if not hasattr(cupon,"id") or not cupon.pk: return True
        from models import CodigoCupon
        return CodigoCupon.objects.filter(cupon = cupon).count() == 0
    
    @staticmethod
    def getRandomCode(cupon):
        try:
            from models import CodigoCupon
            codigo_cupon = CodigoCupon.objects.filter(cupon = cupon).order_by('?')[0]
            return codigo_cupon.codigo
        except:
            return ''
    
    @staticmethod
    def readAndCreateCodes(cupon):
        if cupon.pk:
            print 'CuponCodesGenerator.readAndCreateCodes - Inicio de creacion de los codigos del cupon', cupon.pk,'de la ruta',cupon.codigos_ruta.path
            try:
                f = open(cupon.codigos_ruta.path, 'rt')
                codes = []
                try:
                    reader = csv.reader(f)
                    for row in reader:
                        codes.append( row )
                finally:
                    f.close()
                
                if len(codes) > 0:
                    from models import CodigoCupon
                    
                    for c in codes:
                        if not isinstance(c, basestring) and len(c) > 0:
                            for cc in c:
                                print 'CuponCodesGenerator.readAndCreateCodes ---> Usando', cc
                                codigo_cupon = CodigoCupon()
                                codigo_cupon.codigo = cc[:20].strip()
                                codigo_cupon.usos = 0
                                codigo_cupon.cupon = cupon
                                codigo_cupon.save(user = cupon.usuario_creacion)
                        else:
                            print 'CuponCodesGenerator.readAndCreateCodes --> Usando', c
                            codigo_cupon = CodigoCupon()
                            codigo_cupon.codigo = c[:20].strip()
                            codigo_cupon.usos = 0
                            codigo_cupon.cupon = cupon
                            codigo_cupon.save(user = cupon.usuario_creacion)
                print 'CuponCodesGenerator.readAndCreateCodes - Fin, se han creado',len(codes),' codigos para el cupon', cupon.pk
            except Exception as e:
                print 'CuponCodesGenerator.readAndCreateCodes - Error al crear codigos de cupones', e            
        else:
            print 'CuponCodesGenerator.readAndCreateCodes - El cupon debe estar creado antes'

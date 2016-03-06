'''
Created on Jun 7, 2012

@author: tonny
'''

class Struct:
    '''
        Convierte un diccionario a estructura
    '''

    def __init__(self, **entries):
        self.__dict__.update(entries)

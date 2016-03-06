from django.db import models


class DjangoMenu(models.Model):
    name = models.CharField(max_length=30)
    url = models.CharField(max_length=100, blank=True)
    icon = models.CharField(max_length=100, blank=True)
    icon_hover = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField()
    level = models.IntegerField()
    parent = models.ForeignKey('self', null=True, db_column='parent',
                               blank=True, related_name='submenus')
    description = models.CharField(max_length=100, blank=True)
    index = models.IntegerField(default=1)
    visible = models.BooleanField()
    is_selected = False

    class Meta:
        db_table = u'django_menu'

    def __unicode__(self):
        return self.name

    def get_children(self):
        self.childs = DjangoMenu.objects.select_related().filter(parent=self)
        return self.childs

    def get_all_children(self, include_self=True):
        r = []
        if include_self:
            r.append(self)
        for c in DjangoMenu.objects.filter(parent=self):
            r.append(c.get_all_children(include_self=False))
        return r

    childrens = property(get_children)

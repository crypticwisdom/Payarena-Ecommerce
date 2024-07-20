from django.db import models


# class Country(models.Model):
#     name = models.CharField(max_length=200)
#     code = models.CharField(max_length=10)
#     currency_name = models.CharField(max_length=50, null=True, blank=True)
#     currency_code = models.CharField(max_length=50, null=True, blank=True)
#     currency_symbol = models.CharField(max_length=50, null=True, blank=True)
#     flag_link = models.URLField(null=True, blank=True)
#
#     def __str__(self):
#         return str("{}").format(self.name)
#
#     class Meta:
#         verbose_name_plural = 'Countries'
#
#
# class State(models.Model):
#     country = models.ForeignKey(Country, on_delete=models.CASCADE)
#     name = models.CharField(max_length=50)
#     code = models.CharField(max_length=20, null=True, blank=True)
#
#     def __str__(self):
#         return str("{} - {}").format(self.name, self.country)
#
#     class Meta:
#         verbose_name_plural = 'States'
#
#
# class City(models.Model):
#     state = models.ForeignKey(State, on_delete=models.CASCADE)
#     name = models.CharField(max_length=50)
#     code = models.CharField(max_length=20, null=True, blank=True)
#     image = models.ImageField(upload_to='location-images/cities', blank=True, null=True)
#
#     def __str__(self):
#         return str("{} - {}").format(self.name, self.state)
#
#     class Meta:
#         verbose_name_plural = 'Cities'

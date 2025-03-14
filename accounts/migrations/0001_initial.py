# Generated by Django 4.2.10 on 2025-03-11 14:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_line1', models.CharField(blank=True, max_length=250)),
                ('address_line2', models.CharField(blank=True, max_length=250)),
                ('town_or_city', models.CharField(blank=True, max_length=100)),
                ('county', models.CharField(blank=True, choices=[('antrim', 'Antrim'), ('armagh', 'Armagh'), ('carlow', 'Carlow'), ('cavan', 'Cavan'), ('clare', 'Clare'), ('cork', 'Cork'), ('derry', 'Derry'), ('donegal', 'Donegal'), ('down', 'Down'), ('dublin', 'Dublin'), ('fermanagh', 'Fermanagh'), ('galway', 'Galway'), ('kerry', 'Kerry'), ('kildare', 'Kildare'), ('kilkenny', 'Kilkenny'), ('laois', 'Laois'), ('leitrim', 'Leitrim'), ('limerick', 'Limerick'), ('longford', 'Longford'), ('louth', 'Louth'), ('mayo', 'Mayo'), ('meath', 'Meath'), ('monaghan', 'Monaghan'), ('offaly', 'Offaly'), ('roscommon', 'Roscommon'), ('sligo', 'Sligo'), ('tipperary', 'Tipperary'), ('tyrone', 'Tyrone'), ('waterford', 'Waterford'), ('westmeath', 'Westmeath'), ('wexford', 'Wexford'), ('wicklow', 'Wicklow')], max_length=50)),
                ('eircode', models.CharField(blank=True, help_text='Format: A65 F4E2', max_length=8)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

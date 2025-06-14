# Generated by Django 5.2.1 on 2025-05-20 20:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonitoredWebsite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('check_interval', models.IntegerField(default=60)),
            ],
        ),
        migrations.CreateModel(
            name='MonitoringResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_code', models.IntegerField(null=True)),
                ('response_time', models.FloatField(null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_up', models.BooleanField(default=False)),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='monitor.monitoredwebsite')),
            ],
        ),
        migrations.DeleteModel(
            name='MonitoredSite',
        ),
    ]

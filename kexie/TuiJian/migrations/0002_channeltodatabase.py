# Generated by Django 2.2.4 on 2019-09-19 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TuiJian', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelToDatabase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(max_length=255, unique=True)),
                ('database', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': '频道和数据库的映射',
                'verbose_name_plural': '频道和数据库的映射',
                'db_table': 'channelToDatabase',
            },
        ),
    ]

# Generated by Django 2.2.4 on 2019-09-24 11:02

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TuiJian', '0007_auto_20190924_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chinatopnews',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='新闻内容'),
        ),
        migrations.AlterField(
            model_name='dfkx',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='新闻内容'),
        ),
        migrations.AlterField(
            model_name='kx',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='新闻内容'),
        ),
        migrations.AlterField(
            model_name='news',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='新闻内容'),
        ),
        migrations.AlterField(
            model_name='qgxh',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='新闻内容'),
        ),
        migrations.AlterField(
            model_name='tech',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(verbose_name='新闻内容'),
        ),
    ]

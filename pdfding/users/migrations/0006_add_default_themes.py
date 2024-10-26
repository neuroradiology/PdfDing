# Generated by Django 5.1.1 on 2024-10-26 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_add_pdfs_per_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='dark_mode',
            field=models.CharField(choices=[('Light', 'Light'), ('Dark', 'Dark')], default='Dark', max_length=5),
        ),
        migrations.AlterField(
            model_name='profile',
            name='theme_color',
            field=models.CharField(
                choices=[
                    ('Green', 'Green'),
                    ('Blue', 'Blue'),
                    ('Gray', 'Gray'),
                    ('Red', 'Red'),
                    ('Pink', 'Pink'),
                    ('Orange', 'Orange'),
                ],
                default='Red',
                max_length=6,
            ),
        ),
    ]

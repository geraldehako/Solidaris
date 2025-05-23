# Generated by Django 4.2.19 on 2025-03-15 17:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mutualistes", "0019_mutualiste_telephone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beneficiaire",
            name="photo",
            field=models.ImageField(
                blank=True,
                help_text="Photo du mutualiste",
                null=True,
                upload_to="mutualistes/ayants droits/photos/",
            ),
        ),
    ]

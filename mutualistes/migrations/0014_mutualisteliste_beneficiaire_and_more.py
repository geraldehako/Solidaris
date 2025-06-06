# Generated by Django 4.1.7 on 2025-02-20 20:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("mutualistes", "0013_alter_mutualisteliste_mutualiste"),
    ]

    operations = [
        migrations.AddField(
            model_name="mutualisteliste",
            name="beneficiaire",
            field=models.ForeignKey(
                blank=True,
                help_text="Bénéficiaire concerné, s'il ne s'agit pas du mutualiste",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="listemutb",
                to="mutualistes.beneficiaire",
            ),
        ),
        migrations.AlterField(
            model_name="mutualisteliste",
            name="mutualiste",
            field=models.ForeignKey(
                help_text="Le mutualiste ayant cette",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="listemut",
                to="mutualistes.mutualiste",
            ),
        ),
    ]

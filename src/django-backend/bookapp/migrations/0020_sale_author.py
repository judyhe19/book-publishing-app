from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookapp', '0019_add_kickstarter_sale_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='author',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sales',
                to='bookapp.author',
            ),
        ),
    ]

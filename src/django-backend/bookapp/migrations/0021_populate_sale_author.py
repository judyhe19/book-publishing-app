from django.db import migrations


def populate_sale_author(apps, schema_editor):
    Sale = apps.get_model("bookapp", "Sale")
    for sale in Sale.objects.select_related("book__author"):
        if sale.book and sale.book.author_id:
            sale.author_id = sale.book.author_id
            sale.save(update_fields=["author_id"])


class Migration(migrations.Migration):

    dependencies = [
        ('bookapp', '0020_sale_author'),
    ]

    operations = [
        migrations.RunPython(populate_sale_author, migrations.RunPython.noop),
    ]

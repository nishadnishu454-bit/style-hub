from django.db import migrations, models
import django.db.models.deletion


def copy_addresses(apps, schema_editor):
    Address = apps.get_model("addresses", "Address")
    OrderAddress = apps.get_model("orders", "OrderAddress")

    for addr in Address.objects.all():
        OrderAddress.objects.create(
            id=addr.id,
            full_name=addr.full_name,
            phone_number=addr.phone_number,
            house_name=addr.house_name,
            address=addr.address,
            area=addr.area,
            country=addr.country,
            state=addr.state,
            district=addr.district,
            pincode=addr.pincode,
            address_type=addr.address_type,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_refunded_amount"),
        ("addresses", "0001_initial"),
    ]

    operations = [

        migrations.CreateModel(
            name="OrderAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=50)),
                ("phone_number", models.CharField(max_length=12)),
                ("house_name", models.CharField(max_length=30)),
                ("address", models.TextField()),
                ("area", models.CharField(max_length=30)),
                ("country", models.CharField(max_length=20)),
                ("state", models.CharField(max_length=50)),
                ("district", models.CharField(max_length=30)),
                ("pincode", models.CharField(max_length=30)),
                ("address_type", models.CharField(max_length=30)),
            ],
        ),

        migrations.RunPython(copy_addresses),

        migrations.AlterField(
            model_name="order",
            name="address",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="orders.orderaddress",
            ),
        ),
    ]
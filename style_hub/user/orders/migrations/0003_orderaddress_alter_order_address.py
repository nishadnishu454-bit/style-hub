from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_refunded_amount'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=50)),
                ('phone_number', models.CharField(max_length=12)),
                ('house_name', models.CharField(max_length=30)),
                ('address', models.TextField()),
                ('area', models.CharField(max_length=30)),
                ('country', models.CharField(max_length=20)),
                ('state', models.CharField(max_length=50)),
                ('district', models.CharField(max_length=30)),
                ('pincode', models.CharField(max_length=30)),
                ('address_type', models.CharField(max_length=30)),
            ],
        ),
        migrations.AlterField(
            model_name='order',
            name='address',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order', to='orders.orderaddress'),
        ),
    ]
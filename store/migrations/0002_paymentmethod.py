from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('code', models.SlugField(max_length=50, unique=True, help_text="Short code for use in code, e.g. 'paystack', 'bank_transfer'")),
                ('is_active', models.BooleanField(default=True, help_text='Should this payment method be available to customers?')),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Order in which to display payment methods.')),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['display_order', 'name'],
                'verbose_name': 'Payment Method',
                'verbose_name_plural': 'Payment Methods',
            },
        ),
    ]

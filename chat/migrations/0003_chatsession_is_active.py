# Generated by Django 5.1.1 on 2025-03-19 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_userprofile_alter_chatsession_user1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]

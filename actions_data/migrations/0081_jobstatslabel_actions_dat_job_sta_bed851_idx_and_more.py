# Generated by Django 5.1.3 on 2024-12-02 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0080_jobstatslabel"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="jobstatslabel",
            index=models.Index(
                fields=["job_stats_id", "label"], name="actions_dat_job_sta_bed851_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="jobstatslabel",
            index=models.Index(fields=["label"], name="actions_dat_label_7b1f32_idx"),
        ),
    ]

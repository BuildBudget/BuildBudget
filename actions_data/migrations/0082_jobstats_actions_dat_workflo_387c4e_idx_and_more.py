# Generated by Django 5.1.3 on 2024-12-02 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0081_jobstatslabel_actions_dat_job_sta_bed851_idx_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="jobstats",
            index=models.Index(
                fields=["workflow_id"], name="actions_dat_workflo_387c4e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="jobstats",
            index=models.Index(
                fields=["repository_id"], name="actions_dat_reposit_ac69d6_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="jobstats",
            index=models.Index(
                fields=["owner_entity_id"], name="actions_dat_owner_e_d14dc1_idx"
            ),
        ),
    ]

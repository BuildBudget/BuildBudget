from django.db import models


class Step(models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    conclusion = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job.workflow_run.workflow.name} - {self.job.workflow_run.repository.name} - {self.job.name} - {self.name} - {self.status}"

# from worker.services.tasks import run_evaluation

# def submit_evaluation(document_path: str):
#     # Submit a task
#     result = run_evaluation.delay(document_path)

#     # You can check the task status later
#     print(result.task_id)  # Prints the task ID
#     print(result.status)   # Prints the task status (PENDING, STARTED, SUCCESS, etc.)
    
#     return result


# if __name__ == "__main__":
#     # submit_evaluation("/Users/roger.dsouza/workspace/eval_processor/data/doc_sample.docx")
#     submit_evaluation("/Users/roger.dsouza/workspace/eval_processor/data/pdf_sample.pdf")


from celery import Celery

app = Celery('doc_evaluator_worker',
             broker='redis://10.22.98.9:6379/0',
)
data = ("ITSCM_DEV","56f157ec-e18e-4948-aeef-4f03705991a6") # sample data
app.send_task('worker.services.tasks.run_evaluation', data)
from worker.services.tasks import run_evaluation

def submit_evaluation(document_path: str):
    # Submit a task
    result = run_evaluation.delay(document_path)

    # You can check the task status later
    print(result.task_id)  # Prints the task ID
    print(result.status)   # Prints the task status (PENDING, STARTED, SUCCESS, etc.)
    
    return result


if __name__ == "__main__":
    # submit_evaluation("/Users/roger.dsouza/workspace/eval_processor/data/doc_sample.docx")
    submit_evaluation("/Users/roger.dsouza/workspace/eval_processor/data/pdf_sample.pdf")
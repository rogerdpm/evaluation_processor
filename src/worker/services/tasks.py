from worker.eval_app import celery_app
from worker.utils.document_loader import PDFLoader, WordLoader
from opentelemetry import trace
from worker.utils.evaluate_doc import perform_evaluation
from worker.utils.helper import download_file, get_job_info, create_temp_folder, update_job_status
tracer = trace.get_tracer(__name__)
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@celery_app.task
def run_evaluation(org:str, job_id: str):
    logger.info(f"running evaluation for job_id: {job_id} linked to organization:{org}")
    job_info = get_job_info(org, job_id)
    logger.info(f"job information: {job_info}")

    update_job_status(org, job_id, job_info['job_name'], "running")

    repository = job_info["repo_name"]
    repository_filename=job_info["checklist_file_path"]
    sandbox_name=job_info["sandbox_name"]
    sandbox_filename=job_info["document_url"]

    # create a temp folder
    temp_folder = create_temp_folder()
    logger.info(f"Temporary directory created at: {temp_folder}")

    # download the checklist file
    checklist_file_path = os.path.join(temp_folder, repository_filename)
    CHECKLIST_ENDPOINT=f"http://10.22.98.9:9000/api/v1/orgs/{org}/repos/{repository}/checklist?filename={repository_filename}"
    download_file(CHECKLIST_ENDPOINT, checklist_file_path)
    logger.info(f"Checklist file downloaded to {checklist_file_path}")

    # download the document file
    document_file_path = os.path.join(temp_folder, sandbox_filename)
    SANDBOX_DOC_ENDPOINT=f"http://10.22.98.9:9000/api/v1/orgs/{org}/sandboxes/{sandbox_name}/files/download?filename={sandbox_filename}"
    download_file(SANDBOX_DOC_ENDPOINT, document_file_path)
    logger.info(f"Document file downloaded to {document_file_path}")

    # perform evaluation
    findings = perform_evaluation(document_file_path, checklist_file_path) 


    update_job_status(org, job_id, job_info['job_name'], "completed")
    print(findings)



    

    # document_path = '/home/qxz1viq/doc_eval_latest/evaluation_processor/data/example_doc.docx'
    # yaml_file_path = '/home/qxz1viq/doc_eval_latest/evaluation_processor/data/checklist.yaml'
    # perform_evaluation(document_path, yaml_file_path)

# @celery_app.task
# def run_evaluation(document_path: str):
#     print(f"Evaluating document {document_path}")
#     with tracer.start_as_current_span("run_evaluation") as span:
#         # Determine file type and use appropriate loader    
#         span.set_attribute("document_path", document_path)

#     # Determine file type and use appropriate loader
#     if document_path.endswith('.pdf'):
#         loader = PDFLoader(document_path)
#     elif document_path.endswith('.docx'):
#         loader = WordLoader(document_path)
#     else:
#         raise ValueError("Unsupported document type. Must be PDF or Word document.")

#     # Load and parse the document
#     document_tree = loader.get_tree()
    
#     def print_node(node, level=0):
#         indent = "  " * level
#         print(f"{indent}Node attributes:")
#         print(f"{indent}- content: {node.content}")
#         print(f"{indent}- level: {node.level}")
#         print(f"{indent}- parent: {node.parent}")
#         print(f"{indent}- children count: {len(node.children)}")
#         print(f"{indent}Content: {node.content}")
#         if hasattr(node, 'children'):
#             for child in node.children:
#                 print_node(child, level + 1)

#     # Print the full document tree structure
#     print("\nDocument Tree Structure:")
#     print_node(document_tree)
#     return document_tree.content




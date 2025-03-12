import httpx
import asyncio
import tempfile
import os
import logging
from typing import List, Dict
import json
from worker.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

EVAL_API_BASE_URL = str(settings.EVAL_API_BASE_PATH)



def download_file(url: str, local_path: str):
    logger.info(f"Downloading file from {url} to {local_path}")
    print(f"Downloading file from {url} to {local_path}")

    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            with open(local_path, 'wb') as file:
                file.write(response.content)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        logger.error(f"Error during request: {e}")
        print(f"Error during request: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")


def get_job_info(org: str, job_id: str):
    endpoint = f"{EVAL_API_BASE_URL}/orgs/{org}/evaluation_jobs/{job_id}"
    logger.info(f"Fetching job info from {endpoint}")
    response = httpx.get(endpoint)
    response.raise_for_status()
    return response.json()


def update_job_status(org: str, job_id: str, job_name: str, status: str):
    endpoint = f"{EVAL_API_BASE_URL}/orgs/{org}/evaluation_jobs/{job_id}"
    logger.info(f"Fetching job info from {endpoint}")
    job_data = {
        "job_name": job_name,
        "status": status
    }
    try:
        response = httpx.put(endpoint, json=job_data)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url}: {exc}")
        raise
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url}: {exc.response.json()}")
        raise


def add_job_findings(org: str, job_id: str, job_name: str, findings: List[Dict[str, str]]):
    endpoint = f"{EVAL_API_BASE_URL}/orgs/{org}/evaluation_jobs/{job_id}/findings"
    logger.info(f"Adding job findings to {endpoint}")
    
    try:
        response = httpx.post(endpoint, json=findings)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        raise e
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting to {endpoint}: {e}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise e





def create_temp_folder():
    temp_dir = tempfile.mkdtemp()
    print(f"Temporary directory created at: {temp_dir}")
    return temp_dir


# org = "ITSCM_DEV"
# repository = "itscmdev-repository"
# repository_filename="ehb_checklist_v1_completed.yaml"
# sandbox_name="singapore-nsc"
# sandbox_filename="test.docx"

# CHECKLIST_ENDPOINT=f"http://10.22.98.9:9000/api/v1/orgs/{org}/repos/{repository}/checklist?filename={repository_filename}"

# SANDBOX_DOC_ENDPOINT=f"http://10.22.98.9:9000/api/v1/orgs/{org}/sandboxes/{sandbox_name}/files/download?filename={sandbox_filename}"

# temp_folder = create_temp_folder()
# print(temp_folder)
# asyncio.run(
#     download_file(
#         url=CHECKLIST_ENDPOINT,
#         local_path=os.path.join(temp_folder, repository_filename)
#     )
# )

# asyncio.run(
#     download_file(
#         url=SANDBOX_DOC_ENDPOINT,
#         local_path=os.path.join(temp_folder, sandbox_filename)
#     )
# )



import streamlit as st
import requests
import time
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class SubmitQuestionAndDocumentsResponse(BaseModel):
    pass  # The response body doesn't matter for this endpoint


class GetQuestionAndFactsResponse(BaseModel):
    question: str
    facts: Optional[List[str]]
    status: str


def submit_question_and_documents(base_url):
    # Question and documents to submit
    payload = {
        "question": "What is our pricing model?",
        "documents": [
            "https://storage.googleapis.com/cleric-assignment-call-logs/call_log_20240314_104111.txt",
            "https://storage.googleapis.com/cleric-assignment-call-logs/call_log_20240315_104111.txt",
            "https://storage.googleapis.com/cleric-assignment-call-logs/call_log_20240316_104111.txt"
        ],
        "autoApprove": True
    }

    # Submit the question and documents
    st.write("Submitting question and documents to the API...")
    response = requests.post(f"{base_url}/submit_question_and_documents", json=payload)
    if response.status_code != 200:
        st.error(f"Unexpected status code when submitting question and documents: {response.status_code}")
        return None
    try:
        _ = SubmitQuestionAndDocumentsResponse(**response.json())
    except ValueError as e:
        st.error(f"The response data does not match the expected schema: {str(e)}")
        st.write(response.json())  # Print the invalid data for debugging
        return None

    # Poll until the facts are ready or timeout after 5 minutes
    start_time = time.time()
    while True:
        st.write("Polling for facts...")
        response = requests.get(f"{base_url}/get_question_and_facts")
        if response.status_code != 200:
            st.error(f"Unexpected status code when getting question and facts: {response.status_code}")
            return None
        try:
            data = GetQuestionAndFactsResponse(**response.json())
        except ValueError as e:
            st.error(f"The response data does not match the expected schema: {str(e)}")
            st.write(response.json())  # Print the invalid data for debugging
            return None
        if data.status == "done":
            break
        elif time.time() - start_time > 300:  # 5 minutes timeout
            st.error("Timeout: Facts not ready after 5 minutes")
            return None
        time.sleep(1)  # Wait a bit before polling again

    return data.facts


def main():
    st.title("Assignment Validator")

    # Input for the candidate's API URL
    base_url = st.text_input("Enter the API URL of your assignment:")

    if st.button("Submit"):
        try:
            facts = submit_question_and_documents(base_url)
            if facts is not None:
                st.success("Facts retrieved successfully!")
                st.write("Facts:")
                for fact in facts:
                    st.write(fact)
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()

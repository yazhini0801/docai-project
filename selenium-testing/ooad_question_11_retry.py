import os
import json
import time

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==========================================================
# SETTINGS
# ==========================================================

BASE_URL = "http://localhost:5173"

FOLDER_NAME = "ooad"

QUESTION_ID = 11

QUESTION = (
    "What is multiplicity in an association, "
    "and what does it specify?"
)

RESULTS_FOLDER = "results/ooad_11_20"

RESULT_FILE = os.path.join(
    RESULTS_FOLDER,
    "question_11_result.json"
)


# ==========================================================
# LOAD LOGIN
# ==========================================================

load_dotenv()

EMAIL = os.getenv("DOCAI_EMAIL")
PASSWORD = os.getenv("DOCAI_PASSWORD")

if not EMAIL or not PASSWORD:
    raise Exception(
        "DOCAI_EMAIL or DOCAI_PASSWORD missing from .env"
    )

os.makedirs(
    RESULTS_FOLDER,
    exist_ok=True
)


# ==========================================================
# START CHROME
# ==========================================================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    options=options
)

wait = WebDriverWait(
    driver,
    30
)

result_wait = WebDriverWait(
    driver,
    180
)


# ==========================================================
# HELPERS
# ==========================================================

def parse_percentage(value):

    if value is None:
        return None

    try:
        return float(
            value.replace("%", "").strip()
        )
    except:
        return None


def get_metric(metric_name, column):

    try:

        element = driver.find_element(
            By.XPATH,
            f"//td[normalize-space()='{metric_name}']"
            f"/following-sibling::td[{column}]"
        )

        return element.text.strip()

    except:
        return None


def get_answer(system_name):

    heading = result_wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                f"//h2[normalize-space()='{system_name}']"
            )
        )
    )

    panel = heading.find_element(
        By.XPATH,
        "./ancestor::div[contains(@style,'background')]"
    )

    answer_heading = panel.find_element(
        By.XPATH,
        ".//h3[normalize-space()='Answer']"
    )

    answer_box = answer_heading.find_element(
        By.XPATH,
        "./following-sibling::div[1]"
    )

    return answer_box.text.strip()


# ==========================================================
# LOGIN
# ==========================================================

print()
print("=" * 70)
print("OOAD QUESTION 11 RETRY")
print("=" * 70)

driver.get(
    BASE_URL
)

email_input = wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//input[@type='email']"
        )
    )
)

password_input = wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//input[@type='password']"
        )
    )
)

email_input.send_keys(
    EMAIL
)

password_input.send_keys(
    PASSWORD
)

password_input.send_keys(
    Keys.ENTER
)

wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            f"//*[normalize-space()='{FOLDER_NAME}']"
        )
    )
)

print("Login successful")


# ==========================================================
# OPEN OOAD
# ==========================================================

folder = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            f"//*[normalize-space()='{FOLDER_NAME}']"
        )
    )
)

driver.execute_script(
    "arguments[0].click();",
    folder
)

print("ooad folder opened")


# ==========================================================
# OPEN CHAT
# ==========================================================

chat_button = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[contains(normalize-space(), 'Chat')]"
        )
    )
)

driver.execute_script(
    "arguments[0].click();",
    chat_button
)

wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//h1[normalize-space()='Compare your RAG pipelines']"
        )
    )
)

print("Chat page opened")


# ==========================================================
# WAIT FOR DOCUMENT
# ==========================================================

print("Waiting for OOAD document...")


document_wait = WebDriverWait(
    driver,
    120
)


def document_ready(d):

    try:

        body = d.find_element(
            By.TAG_NAME,
            "body"
        ).text

        return (
            "1 document loaded" in body
            or "1 documents loaded" in body
        )

    except:
        return False


document_wait.until(
    document_ready
)

print("OOAD document detected")


# ==========================================================
# EXTRA STABILITY CHECK
# ==========================================================

# We already know the UI says the document is loaded.
# This short stability period prevents Question 11 from
# being submitted at the exact moment React is updating.

print("Making sure the document state is stable...")

stable_count = 0

while stable_count < 3:

    body = driver.find_element(
        By.TAG_NAME,
        "body"
    ).text

    if (
        "1 document loaded" in body
        or "1 documents loaded" in body
    ):

        stable_count += 1

    else:

        stable_count = 0

    time.sleep(1)


print("Document is ready")


# ==========================================================
# ENTER QUESTION
# ==========================================================

textarea = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//textarea[@placeholder='Ask anything about your documents...']"
        )
    )
)

textarea.clear()

textarea.send_keys(
    QUESTION
)

print()
print("Question 11 entered")
print(QUESTION)


# ==========================================================
# COMPARE
# ==========================================================

compare_button = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[contains(normalize-space(), 'Compare RAG')]"
        )
    )
)

driver.execute_script(
    "arguments[0].click();",
    compare_button
)

print("Compare RAG clicked")


# ==========================================================
# CHECK ALERT
# ==========================================================

time.sleep(1)

try:

    alert = driver.switch_to.alert

    alert_text = alert.text

    alert.accept()

    raise Exception(
        f"Application alert: {alert_text}"
    )

except Exception as alert_error:

    if "Application alert:" in str(
        alert_error
    ):
        raise alert_error


# ==========================================================
# WAIT FOR RESULTS
# ==========================================================

print(
    "Waiting for Standard RAG and RankFusion-RAG..."
)

result_wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//h2[normalize-space()='Standard RAG']"
        )
    )
)

result_wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//h2[normalize-space()='RankFusion-RAG']"
        )
    )
)

result_wait.until(
    EC.presence_of_element_located(
        (
            By.XPATH,
            "//h2[normalize-space()='Performance Comparison']"
        )
    )
)

print("Comparison completed")


# ==========================================================
# GET ANSWERS
# ==========================================================

standard_answer = get_answer(
    "Standard RAG"
)

rankfusion_answer = get_answer(
    "RankFusion-RAG"
)


# ==========================================================
# GET METRICS
# ==========================================================

metric_names = [
    "Answer Relevance",
    "Context Relevance",
    "Citation Correctness",
    "Faithfulness",
    "Overall Score",
    "Answer Accuracy",
    "Citation Accuracy",
    "Retrieval Precision",
    "Hallucination Rate",
    "Project Score",
    "Best Retrieval Score",
    "Confidence",
    "Retrieved Chunks",
    "Chunks Used",
    "Response Time",
]

standard_metrics = {}
rankfusion_metrics = {}

for metric in metric_names:

    standard_metrics[metric] = get_metric(
        metric,
        1
    )

    rankfusion_metrics[metric] = get_metric(
        metric,
        2
    )


# ==========================================================
# COMPARE PROJECT SCORE
# ==========================================================

standard_score = parse_percentage(
    standard_metrics.get(
        "Project Score"
    )
)

rankfusion_score = parse_percentage(
    rankfusion_metrics.get(
        "Project Score"
    )
)

better_result = None
improvement = None

if (
    standard_score is not None
    and rankfusion_score is not None
):

    improvement = (
        rankfusion_score
        - standard_score
    )

    if rankfusion_score > standard_score:

        better_result = "RankFusion-RAG"

    elif standard_score > rankfusion_score:

        better_result = "Standard RAG"

    else:

        better_result = "Tie"


# ==========================================================
# SAVE QUESTION 11
# ==========================================================

result = {

    "question_id": QUESTION_ID,

    "question": QUESTION,

    "standard_rag": {

        "answer":
            standard_answer,

        "metrics":
            standard_metrics
    },

    "rankfusion_rag": {

        "answer":
            rankfusion_answer,

        "metrics":
            rankfusion_metrics
    },

    "comparison": {

        "better_result":
            better_result,

        "rankfusion_improvement":
            improvement
    },

    "test_status":
        "PASS"
}


with open(
    RESULT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        result,
        file,
        indent=4,
        ensure_ascii=False
    )


# ==========================================================
# DISPLAY RESULT
# ==========================================================

print()
print("=" * 70)
print("QUESTION 11 RETRY COMPLETED")
print("=" * 70)

print(
    "Standard Project Score:",
    standard_metrics.get(
        "Project Score"
    )
)

print(
    "RankFusion Project Score:",
    rankfusion_metrics.get(
        "Project Score"
    )
)

print(
    "Higher Project Score:",
    better_result
)

if improvement is not None:

    print(
        "RankFusion Score Difference:",
        f"{improvement:.1f} percentage points"
    )

print()
print(
    "Saved to:",
    RESULT_FILE
)

print("=" * 70)


input(
    "\nPress Enter to close browser..."
)

driver.quit()
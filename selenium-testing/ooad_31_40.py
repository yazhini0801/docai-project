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

QUESTIONS_FILE = "ooad_31_40_questions.json"

FOLDER_NAME = "ooad"

RESULTS_FOLDER = "results/ooad_31_40"

ALL_RESULTS_FILE = os.path.join(
    RESULTS_FOLDER,
    "all_results.json"
)

FINAL_SUMMARY_FILE = os.path.join(
    RESULTS_FOLDER,
    "final_summary.json"
)


# ==========================================================
# LOAD ENVIRONMENT
# ==========================================================

load_dotenv()

EMAIL = os.getenv("DOCAI_EMAIL")
PASSWORD = os.getenv("DOCAI_PASSWORD")

if not EMAIL or not PASSWORD:
    raise Exception(
        "DOCAI_EMAIL or DOCAI_PASSWORD missing from .env"
    )


# ==========================================================
# LOAD QUESTIONS
# ==========================================================

with open(
    QUESTIONS_FILE,
    "r",
    encoding="utf-8"
) as file:
    QUESTIONS = json.load(file)


# ==========================================================
# CREATE RESULTS FOLDER
# ==========================================================

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
# PARSE PERCENTAGE
# ==========================================================

def parse_percentage(value):

    if value is None:
        return None

    value = str(value).strip()

    if value in ["", "—"]:
        return None

    try:
        return float(
            value.replace("%", "").strip()
        )

    except:
        return None


# ==========================================================
# PARSE RESPONSE TIME
# ==========================================================

def parse_response_time(value):

    if value is None:
        return None

    value = str(value).strip()

    if value in ["", "—"]:
        return None

    try:
        return float(
            value.lower()
            .replace("seconds", "")
            .replace("second", "")
            .replace("secs", "")
            .replace("sec", "")
            .replace("s", "")
            .strip()
        )

    except:
        return None


# ==========================================================
# GET METRIC
# ==========================================================

def get_metric(metric_name, column):

    xpath = (
        f"//td[normalize-space()='{metric_name}']"
        f"/following-sibling::td[{column}]"
    )

    try:

        element = driver.find_element(
            By.XPATH,
            xpath
        )

        return element.text.strip()

    except:
        return None


# ==========================================================
# GET ANSWER
# ==========================================================

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
# SCROLL RESULTS
# ==========================================================

def scroll_results():

    print("Scrolling through final results...")

    driver.execute_script(
        "window.scrollTo(0, 0);"
    )

    time.sleep(0.5)

    last_position = -1

    while True:

        driver.execute_script(
            "window.scrollBy(0, 700);"
        )

        time.sleep(0.3)

        current_position = driver.execute_script(
            "return window.pageYOffset"
        )

        page_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        window_height = driver.execute_script(
            "return window.innerHeight"
        )

        if (
            current_position + window_height
            >= page_height - 20
        ):
            break

        if current_position == last_position:
            break

        last_position = current_position

    print("Reached end of comparison page")


# ==========================================================
# CLEAR CHAT
# ==========================================================

def clear_chat():

    print("Clearing current result...")

    driver.execute_script(
        "window.scrollTo(0, 0);"
    )

    time.sleep(0.5)

    clear_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[normalize-space()='Clear']"
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        clear_button
    )

    time.sleep(0.3)

    driver.execute_script(
        "arguments[0].click();",
        clear_button
    )

    wait.until(
        EC.invisibility_of_element_located(
            (
                By.XPATH,
                "//h2[normalize-space()='Performance Comparison']"
            )
        )
    )

    print("Chat cleared")


# ==========================================================
# WAIT FOR DOCUMENT
# ==========================================================

def wait_for_document_loaded():

    print("Waiting for OOAD document to load...")

    document_wait = WebDriverWait(
        driver,
        120
    )

    def document_is_loaded(d):

        try:

            body_text = d.find_element(
                By.TAG_NAME,
                "body"
            ).text

            return (
                "document loaded" in body_text
                or "documents loaded" in body_text
            )

        except:
            return False

    document_wait.until(
        document_is_loaded
    )

    print("OOAD document detected")

    # Make sure document state stays stable
    stable_count = 0

    while stable_count < 3:

        body_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        if (
            "document loaded" in body_text
            or "documents loaded" in body_text
        ):
            stable_count += 1

        else:
            stable_count = 0

        time.sleep(1)

    print("OOAD document loaded successfully")


# ==========================================================
# LOGIN
# ==========================================================

print()
print("=" * 70)
print("OOAD SELENIUM TEST - QUESTIONS 31 TO 40")
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
# OPEN OOAD FOLDER
# ==========================================================

folder_element = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            f"//*[normalize-space()='{FOLDER_NAME}']"
        )
    )
)

driver.execute_script(
    "arguments[0].click();",
    folder_element
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
# WAIT UNTIL DOCUMENT IS READY
# ==========================================================

wait_for_document_loaded()


# ==========================================================
# ZOOM
# ==========================================================

driver.execute_script(
    "document.body.style.zoom='50%'"
)


# ==========================================================
# RESULTS
# ==========================================================

all_results = []

passed = 0
failed = 0


# ==========================================================
# RUN QUESTIONS 31-40
# ==========================================================

for item in QUESTIONS:

    question_id = item["id"]
    question = item["question"]

    print()
    print("=" * 70)
    print(f"QUESTION {question_id}")
    print("=" * 70)
    print(question)

    try:

        # --------------------------------------------------
        # ENTER QUESTION
        # --------------------------------------------------

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
            question
        )

        print("Question entered")


        # --------------------------------------------------
        # CLICK COMPARE
        # --------------------------------------------------

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


        # --------------------------------------------------
        # CHECK FOR APPLICATION ALERT
        # --------------------------------------------------

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


        # --------------------------------------------------
        # WAIT FOR RESULTS
        # --------------------------------------------------

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


        # --------------------------------------------------
        # GET ANSWERS
        # --------------------------------------------------

        standard_answer = get_answer(
            "Standard RAG"
        )

        rankfusion_answer = get_answer(
            "RankFusion-RAG"
        )

        print(
            "Standard RAG answer collected"
        )

        print(
            "RankFusion-RAG answer collected"
        )


        # --------------------------------------------------
        # GET METRICS
        # --------------------------------------------------

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

            standard_metrics[
                metric
            ] = get_metric(
                metric,
                1
            )

            rankfusion_metrics[
                metric
            ] = get_metric(
                metric,
                2
            )

        print("Metrics collected")


        # --------------------------------------------------
        # PROJECT SCORES
        # --------------------------------------------------

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

        print()

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


        # --------------------------------------------------
        # COMPARE SCORES
        # --------------------------------------------------

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

                better_result = (
                    "RankFusion-RAG"
                )

            elif standard_score > rankfusion_score:

                better_result = (
                    "Standard RAG"
                )

            else:

                better_result = "Tie"


        print(
            "Better Result:",
            better_result
        )

        if improvement is not None:

            print(
                "RankFusion Improvement:",
                f"{improvement:.1f}%"
            )


        # --------------------------------------------------
        # SCROLL RESULTS
        # --------------------------------------------------

        scroll_results()


        # --------------------------------------------------
        # CREATE RESULT
        # --------------------------------------------------

        result = {

            "question_id":
                question_id,

            "question":
                question,

            "standard_rag": {

                "answer":
                    standard_answer,

                "metrics":
                    standard_metrics,
            },

            "rankfusion_rag": {

                "answer":
                    rankfusion_answer,

                "metrics":
                    rankfusion_metrics,
            },

            "comparison": {

                "better_result":
                    better_result,

                "rankfusion_improvement":
                    improvement,
            },

            "test_status":
                "PASS",
        }


        # --------------------------------------------------
        # SAVE QUESTION RESULT
        # --------------------------------------------------

        result_file = os.path.join(
            RESULTS_FOLDER,
            f"question_{question_id}_result.json"
        )

        with open(
            result_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4,
                ensure_ascii=False
            )

        all_results.append(
            result
        )

        passed += 1

        print(
            "Result saved:",
            result_file
        )


        # --------------------------------------------------
        # CLEAR FOR NEXT QUESTION
        # --------------------------------------------------

        clear_chat()


    except Exception as error:

        failed += 1

        print()

        print(
            "FAILED:",
            error
        )

        failure_result = {

            "question_id":
                question_id,

            "question":
                question,

            "test_status":
                "FAIL",

            "error":
                str(error),
        }

        all_results.append(
            failure_result
        )


        # --------------------------------------------------
        # ERROR SCREENSHOT
        # --------------------------------------------------

        screenshot_file = os.path.join(
            RESULTS_FOLDER,
            f"question_{question_id}_error.png"
        )

        try:

            driver.save_screenshot(
                screenshot_file
            )

            print(
                "Error screenshot saved:",
                screenshot_file
            )

        except:
            pass


        # --------------------------------------------------
        # TRY TO RECOVER
        # --------------------------------------------------

        try:

            clear_chat()

        except:

            print(
                "Could not automatically clear after failure."
            )


# ==========================================================
# SAVE ALL RESULTS
# ==========================================================

with open(
    ALL_RESULTS_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        all_results,
        file,
        indent=4,
        ensure_ascii=False
    )


# ==========================================================
# CREATE SUMMARY
# ==========================================================

rankfusion_wins = 0

standard_wins = 0

ties = 0

improvements = []

standard_scores = []

rankfusion_scores = []

standard_times = []

rankfusion_times = []


for result in all_results:

    if result.get(
        "test_status"
    ) != "PASS":

        continue


    comparison = result.get(
        "comparison",
        {}
    )

    better = comparison.get(
        "better_result"
    )

    if better == "RankFusion-RAG":

        rankfusion_wins += 1

    elif better == "Standard RAG":

        standard_wins += 1

    elif better == "Tie":

        ties += 1


    improvement = comparison.get(
        "rankfusion_improvement"
    )

    if improvement is not None:

        improvements.append(
            improvement
        )


    # ------------------------------------------------------
    # STANDARD PROJECT SCORE
    # ------------------------------------------------------

    standard_project_score = parse_percentage(
        result.get(
            "standard_rag",
            {}
        ).get(
            "metrics",
            {}
        ).get(
            "Project Score"
        )
    )

    if standard_project_score is not None:

        standard_scores.append(
            standard_project_score
        )


    # ------------------------------------------------------
    # RANKFUSION PROJECT SCORE
    # ------------------------------------------------------

    rankfusion_project_score = parse_percentage(
        result.get(
            "rankfusion_rag",
            {}
        ).get(
            "metrics",
            {}
        ).get(
            "Project Score"
        )
    )

    if rankfusion_project_score is not None:

        rankfusion_scores.append(
            rankfusion_project_score
        )


    # ------------------------------------------------------
    # STANDARD RESPONSE TIME
    # ------------------------------------------------------

    standard_response_time = parse_response_time(
        result.get(
            "standard_rag",
            {}
        ).get(
            "metrics",
            {}
        ).get(
            "Response Time"
        )
    )

    if standard_response_time is not None:

        standard_times.append(
            standard_response_time
        )


    # ------------------------------------------------------
    # RANKFUSION RESPONSE TIME
    # ------------------------------------------------------

    rankfusion_response_time = parse_response_time(
        result.get(
            "rankfusion_rag",
            {}
        ).get(
            "metrics",
            {}
        ).get(
            "Response Time"
        )
    )

    if rankfusion_response_time is not None:

        rankfusion_times.append(
            rankfusion_response_time
        )


# ==========================================================
# CALCULATE AVERAGES
# ==========================================================

average_improvement = None

if improvements:

    average_improvement = (
        sum(improvements)
        / len(improvements)
    )


average_standard_score = None

if standard_scores:

    average_standard_score = (
        sum(standard_scores)
        / len(standard_scores)
    )


average_rankfusion_score = None

if rankfusion_scores:

    average_rankfusion_score = (
        sum(rankfusion_scores)
        / len(rankfusion_scores)
    )


average_standard_time = None

if standard_times:

    average_standard_time = (
        sum(standard_times)
        / len(standard_times)
    )


average_rankfusion_time = None

if rankfusion_times:

    average_rankfusion_time = (
        sum(rankfusion_times)
        / len(rankfusion_times)
    )


# ==========================================================
# FINAL SUMMARY
# ==========================================================

summary = {

    "batch":
        "OOAD Questions 31-40",

    "total_tests":
        len(QUESTIONS),

    "passed":
        passed,

    "failed":
        failed,

    "standard_rag": {

        "average_project_score":
            round(
                average_standard_score,
                2
            )
            if average_standard_score is not None
            else None,

        "wins":
            standard_wins,

        "average_response_time":
            round(
                average_standard_time,
                2
            )
            if average_standard_time is not None
            else None,
    },

    "rankfusion_rag": {

        "average_project_score":
            round(
                average_rankfusion_score,
                2
            )
            if average_rankfusion_score is not None
            else None,

        "wins":
            rankfusion_wins,

        "average_response_time":
            round(
                average_rankfusion_time,
                2
            )
            if average_rankfusion_time is not None
            else None,
    },

    "ties":
        ties,

    "average_rankfusion_improvement":
        round(
            average_improvement,
            2
        )
        if average_improvement is not None
        else None,
}


# ==========================================================
# SAVE SUMMARY
# ==========================================================

with open(
    FINAL_SUMMARY_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        summary,
        file,
        indent=4,
        ensure_ascii=False
    )


# ==========================================================
# TERMINAL OUTPUT
# ==========================================================

print()

print("=" * 70)

print(
    "OOAD QUESTIONS 31-40 TEST COMPLETED"
)

print("=" * 70)

print(
    "Total Questions:",
    len(QUESTIONS)
)

print(
    "Tests Passed:",
    passed
)

print(
    "Tests Failed:",
    failed
)

print()

print(
    "Standard RAG Average Project Score:",
    average_standard_score
)

print(
    "RankFusion-RAG Average Project Score:",
    average_rankfusion_score
)

print()

print(
    "Standard RAG Wins:",
    standard_wins
)

print(
    "RankFusion-RAG Wins:",
    rankfusion_wins
)

print(
    "Ties:",
    ties
)

print()

print(
    "Standard RAG Average Response Time:",
    average_standard_time
)

print(
    "RankFusion-RAG Average Response Time:",
    average_rankfusion_time
)

if average_improvement is not None:

    print(
        "Average RankFusion Improvement:",
        f"{average_improvement:.2f}%"
    )

print()

print(
    "All results:",
    ALL_RESULTS_FILE
)

print(
    "Final summary:",
    FINAL_SUMMARY_FILE
)

print("=" * 70)

input(
    "\nPress Enter to close browser..."
)

driver.quit()
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

QUESTIONS_FILE = "ooad_1_10_questions.json"

FOLDER_NAME = "ooad"

RESULTS_FOLDER = "results/ooad_1_10"

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
# HELPER - PARSE PERCENTAGE
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
# HELPER - GET METRIC
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
# HELPER - GET ANSWER
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
# HELPER - SCROLL THROUGH RESULTS
# ==========================================================

def scroll_results():

    print(
        "Scrolling through final results..."
    )

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

    print(
        "Reached end of comparison page"
    )


# ==========================================================
# HELPER - CLEAR CHAT
# ==========================================================

def clear_chat():

    print(
        "Clearing current result..."
    )

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

    # Wait until previous result disappears.
    wait.until(
        EC.invisibility_of_element_located(
            (
                By.XPATH,
                "//h2[normalize-space()='Performance Comparison']"
            )
        )
    )

    print(
        "Chat cleared"
    )


# ==========================================================
# HELPER - WAIT FOR DOCUMENT
# ==========================================================

def wait_for_document_loaded():

    print(
        "Waiting for OOAD document to load..."
    )

    document_wait = WebDriverWait(
        driver,
        60
    )

    def document_is_loaded(d):

        try:

            body_text = d.find_element(
                By.TAG_NAME,
                "body"
            ).text

            # ChatPage displays:
            # "1 document loaded"
            # "2 documents loaded"
            # etc.

            return (
                "document loaded" in body_text
                or "documents loaded" in body_text
            )

        except:
            return False

    document_wait.until(
        document_is_loaded
    )

    print(
        "OOAD document loaded successfully"
    )


# ==========================================================
# LOGIN
# ==========================================================

print()
print("=" * 70)
print("OOAD SELENIUM TEST - QUESTIONS 1 TO 10")
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


print(
    "Login successful"
)


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


print(
    "ooad folder opened"
)


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


print(
    "Chat page opened"
)


# ==========================================================
# WAIT UNTIL DOCUMENT IS ACTUALLY LOADED
# ==========================================================

wait_for_document_loaded()


# ==========================================================
# ZOOM OUT
# ==========================================================

driver.execute_script(
    "document.body.style.zoom='50%'"
)


# ==========================================================
# TEST RESULTS
# ==========================================================

all_results = []

passed = 0
failed = 0


# ==========================================================
# RUN QUESTIONS
# ==========================================================

for item in QUESTIONS:

    question_id = item["id"]
    question = item["question"]

    print()
    print("=" * 70)
    print(
        f"QUESTION {question_id}"
    )
    print("=" * 70)

    print(
        question
    )


    try:

        # --------------------------------------------------
        # INPUT QUESTION
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


        print(
            "Question entered"
        )


        # --------------------------------------------------
        # CLICK COMPARE RAG
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


        print(
            "Compare RAG clicked"
        )


        # --------------------------------------------------
        # CHECK APPLICATION ALERT
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
        # WAIT FOR BOTH RESULTS
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


        print(
            "Comparison completed"
        )


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


        print(
            "Metrics collected"
        )


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
        # COMPARE
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


            if (
                rankfusion_score
                > standard_score
            ):

                better_result = (
                    "RankFusion-RAG"
                )


            elif (
                standard_score
                > rankfusion_score
            ):

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
        # SCROLL THROUGH COMPLETE RESULTS
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
        # SAVE INDIVIDUAL QUESTION RESULT
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


for result in all_results:

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


# ==========================================================
# AVERAGE IMPROVEMENT
# ==========================================================

average_improvement = None


if improvements:

    average_improvement = (
        sum(improvements)
        / len(improvements)
    )


# ==========================================================
# FINAL SUMMARY
# ==========================================================

summary = {

    "batch":
        "OOAD Questions 1-10",

    "total_questions":
        len(QUESTIONS),

    "successful_question_tests":
        passed,

    "failed_question_tests":
        failed,

    "rankfusion_wins":
        rankfusion_wins,

    "standard_rag_wins":
        standard_wins,

    "ties":
        ties,

    "average_rankfusion_improvement":
        average_improvement,
}


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
# FINAL TERMINAL OUTPUT
# ==========================================================

print()
print("=" * 70)

print(
    "OOAD QUESTIONS 1-10 TEST COMPLETED"
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
    "RankFusion-RAG Wins:",
    rankfusion_wins
)


print(
    "Standard RAG Wins:",
    standard_wins
)


print(
    "Ties:",
    ties
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
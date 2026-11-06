import os
import json
import time
from statistics import mean

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException


# ==========================================================
# SETTINGS
# ==========================================================

BASE_URL = "http://localhost:5173"

QUESTIONS_FILE = "kms_21_30_questions.json"

FOLDER_NAME = "kms"

RESULTS_FOLDER = "results/kms_21_30"

ALL_RESULTS_FILE = os.path.join(
    RESULTS_FOLDER,
    "all_results.json"
)

FINAL_SUMMARY_FILE = os.path.join(
    RESULTS_FOLDER,
    "final_summary.json"
)

WAIT_TIME = 30
RESULT_WAIT_TIME = 180


# ==========================================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv()

EMAIL = os.getenv("DOCAI_EMAIL")
PASSWORD = os.getenv("DOCAI_PASSWORD")

if not EMAIL or not PASSWORD:
    raise ValueError(
        "DOCAI_EMAIL or DOCAI_PASSWORD is missing from .env"
    )


# ==========================================================
# CREATE RESULTS FOLDER
# ==========================================================

os.makedirs(RESULTS_FOLDER, exist_ok=True)


# ==========================================================
# LOAD QUESTIONS
# ==========================================================

with open(
    QUESTIONS_FILE,
    "r",
    encoding="utf-8"
) as file:
    questions = json.load(file)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def parse_percentage(value):

    if value is None:
        return 0.0

    try:
        value = str(value).replace("%", "").strip()
        return float(value)
    except:
        return 0.0


def parse_time(value):

    if value is None:
        return 0.0

    try:
        value = str(value).lower()

        value = value.replace("seconds", "")
        value = value.replace("second", "")
        value = value.replace("secs", "")
        value = value.replace("sec", "")
        value = value.replace("s", "")
        value = value.strip()

        return float(value)

    except:
        return 0.0


def safe_text(element):

    try:
        return element.text.strip()
    except:
        return ""


def save_json(path, data):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def dismiss_alert_if_present(driver):

    try:
        alert = driver.switch_to.alert
        message = alert.text

        print(f"Alert detected: {message}")

        alert.accept()

        return message

    except NoAlertPresentException:
        return None

    except:
        return None


def scroll_results(driver):

    try:
        current_position = 0

        total_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        while current_position < total_height:

            current_position += 500

            driver.execute_script(
                f"window.scrollTo(0, {current_position});"
            )

            time.sleep(0.2)

            total_height = driver.execute_script(
                "return document.body.scrollHeight"
            )

    except:
        pass


def clear_chat(driver):

    try:

        clear_button = WebDriverWait(
            driver,
            20
        ).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(normalize-space(.), 'Clear')]"
                )
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            clear_button
        )

        time.sleep(0.5)

        driver.execute_script(
            "arguments[0].click();",
            clear_button
        )

        time.sleep(1)

    except:
        print("Clear button not found - continuing.")


def wait_for_documents(driver):

    print("Waiting for KMS documents to load...")

    WebDriverWait(
        driver,
        120
    ).until(
        lambda d:
        "document(s) loaded" in
        d.find_element(By.TAG_NAME, "body").text.lower()
        or
        "documents loaded" in
        d.find_element(By.TAG_NAME, "body").text.lower()
        or
        "document loaded" in
        d.find_element(By.TAG_NAME, "body").text.lower()
    )

    time.sleep(3)

    print("KMS documents loaded successfully.")


def find_result_section(driver, title):

    heading = WebDriverWait(
        driver,
        RESULT_WAIT_TIME
    ).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                f"//h2[normalize-space()='{title}']"
            )
        )
    )

    section = heading

    for _ in range(6):

        try:
            parent = section.find_element(
                By.XPATH,
                ".."
            )

            parent_text = safe_text(parent)

            if (
                "Project Score" in parent_text
                and
                "Response Time" in parent_text
            ):
                return parent

            section = parent

        except:
            break

    return heading.find_element(
        By.XPATH,
        ".."
    )


def get_answer(section):

    try:

        paragraphs = section.find_elements(
            By.TAG_NAME,
            "p"
        )

        answer_parts = []

        for paragraph in paragraphs:

            text = safe_text(paragraph)

            if not text:
                continue

            lower_text = text.lower()

            skip_words = [
                "confidence",
                "citation",
                "retrieved",
                "response time",
                "project score",
                "best retrieval",
            ]

            if any(
                word in lower_text
                for word in skip_words
            ):
                continue

            answer_parts.append(text)

        return "\n".join(answer_parts)

    except:
        return ""


def get_metric(section, metric_name):

    try:

        elements = section.find_elements(
            By.XPATH,
            f".//*[contains(normalize-space(text()), '{metric_name}')]"
        )

        for element in elements:

            text = safe_text(element)

            if metric_name.lower() not in text.lower():
                continue

            cleaned = text.replace(
                metric_name,
                ""
            ).strip(" :")

            if cleaned:
                return cleaned

            try:

                parent = element.find_element(
                    By.XPATH,
                    ".."
                )

                parent_text = safe_text(parent)

                cleaned_parent = (
                    parent_text
                    .replace(metric_name, "")
                    .strip(" :")
                )

                if cleaned_parent:
                    return cleaned_parent

            except:
                pass

            try:

                sibling = element.find_element(
                    By.XPATH,
                    "following-sibling::*[1]"
                )

                sibling_text = safe_text(sibling)

                if sibling_text:
                    return sibling_text

            except:
                pass

    except:
        pass

    return ""


def extract_metrics_from_comparison(driver):

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

    try:

        heading = WebDriverWait(
            driver,
            RESULT_WAIT_TIME
        ).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//h2[contains(normalize-space(.), "
                    "'Performance Comparison')]"
                )
            )
        )

        table = heading.find_element(
            By.XPATH,
            "following::table[1]"
        )

        rows = table.find_elements(
            By.TAG_NAME,
            "tr"
        )

        for row in rows:

            cells = row.find_elements(
                By.TAG_NAME,
                "td"
            )

            if len(cells) < 3:
                continue

            metric = safe_text(cells[0])
            standard_value = safe_text(cells[1])
            rankfusion_value = safe_text(cells[2])

            for metric_name in metric_names:

                if metric.lower() == metric_name.lower():

                    standard_metrics[
                        metric_name
                    ] = standard_value

                    rankfusion_metrics[
                        metric_name
                    ] = rankfusion_value

                    break

    except Exception as error:

        print(
            "Could not read comparison table:",
            error
        )

    return standard_metrics, rankfusion_metrics


# ==========================================================
# START TEST
# ==========================================================

print("\n" + "=" * 70)
print("KMS SELENIUM TEST - QUESTIONS 21 TO 30")
print("=" * 70)

print(
    f"Total questions: {len(questions)}"
)


options = webdriver.ChromeOptions()

options.add_argument(
    "--start-maximized"
)

driver = webdriver.Chrome(
    options=options
)

wait = WebDriverWait(
    driver,
    WAIT_TIME
)

all_results = []


try:

    # ======================================================
    # OPEN APPLICATION
    # ======================================================

    driver.get(
        BASE_URL
    )

    print("Application opened")


    # ======================================================
    # LOGIN
    # ======================================================

    email_input = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@type='email']"
            )
        )
    )

    password_input = driver.find_element(
        By.XPATH,
        "//input[@type='password']"
    )

    email_input.clear()
    email_input.send_keys(
        EMAIL
    )

    password_input.clear()
    password_input.send_keys(
        PASSWORD
    )

    password_input.send_keys(
        Keys.ENTER
    )

    time.sleep(3)

    print("Login successful")


    # ======================================================
    # ZOOM OUT
    # ======================================================

    driver.execute_script(
        "document.body.style.zoom='50%'"
    )

    time.sleep(1)


    # ======================================================
    # OPEN KMS FOLDER
    # ======================================================

    folder = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                f"//*[normalize-space(text())='{FOLDER_NAME}']"
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        folder
    )

    time.sleep(0.5)

    driver.execute_script(
        "arguments[0].click();",
        folder
    )

    print("kms folder opened")

    time.sleep(2)


    # ======================================================
    # CLICK OPEN CHAT
    # ======================================================

    open_chat_button = WebDriverWait(
        driver,
        30
    ).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(normalize-space(.), 'Open Chat')]"
                " | "
                "//a[contains(normalize-space(.), 'Open Chat')]"
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        open_chat_button
    )

    time.sleep(0.5)

    driver.execute_script(
        "arguments[0].click();",
        open_chat_button
    )

    print("Open Chat clicked")


    # ======================================================
    # WAIT FOR CHAT PAGE
    # ======================================================

    WebDriverWait(
        driver,
        60
    ).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//textarea[@placeholder="
                "'Ask anything about your documents...']"
            )
        )
    )

    print("Chat page opened")


    # ======================================================
    # WAIT FOR DOCUMENTS
    # ======================================================

    wait_for_documents(
        driver
    )


    # ======================================================
    # RUN QUESTIONS
    # ======================================================

    for index, item in enumerate(
        questions,
        start=1
    ):

        question_id = item.get(
            "id",
            index
        )

        question = item.get(
            "question",
            ""
        )

        print("\n" + "=" * 70)

        print(
            f"TEST {index}/{len(questions)}"
        )

        print(
            f"Question {question_id}: {question}"
        )

        print("=" * 70)


        result = {

            "question_id": question_id,

            "question": question,

            "status": "FAIL",

            "standard_rag": {},

            "rankfusion_rag": {},

            "better_result": None,

            "rankfusion_improvement": None,

            "error": None,
        }


        try:

            # ==================================================
            # INPUT QUESTION
            # ==================================================

            textarea = WebDriverWait(
                driver,
                30
            ).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//textarea[@placeholder="
                        "'Ask anything about your documents...']"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                textarea
            )

            textarea.clear()

            textarea.send_keys(
                question
            )

            print("Question entered")


            # ==================================================
            # CLICK COMPARE
            # ==================================================

            compare_button = WebDriverWait(
                driver,
                30
            ).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(normalize-space(.), "
                        "'Compare RAG')]"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].click();",
                compare_button
            )

            print("Compare RAG clicked")


            # ==================================================
            # WAIT FOR START
            # ==================================================

            try:

                WebDriverWait(
                    driver,
                    20
                ).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[contains(normalize-space(.), "
                            "'Comparing RAG pipelines')]"
                        )
                    )
                )

                print(
                    "Comparison running..."
                )

            except:
                pass


            # ==================================================
            # CHECK ALERT
            # ==================================================

            time.sleep(1)

            alert_message = dismiss_alert_if_present(
                driver
            )

            if alert_message:

                raise Exception(
                    f"Application alert: {alert_message}"
                )


            # ==================================================
            # WAIT FOR RESULTS
            # ==================================================

            WebDriverWait(
                driver,
                RESULT_WAIT_TIME
            ).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[normalize-space()='Standard RAG']"
                    )
                )
            )

            WebDriverWait(
                driver,
                RESULT_WAIT_TIME
            ).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[normalize-space()='RankFusion-RAG']"
                    )
                )
            )

            WebDriverWait(
                driver,
                RESULT_WAIT_TIME
            ).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[contains(normalize-space(.), "
                        "'Performance Comparison')]"
                    )
                )
            )

            print(
                "Comparison completed"
            )


            # ==================================================
            # RESULT SECTIONS
            # ==================================================

            standard_section = find_result_section(
                driver,
                "Standard RAG"
            )

            rankfusion_section = find_result_section(
                driver,
                "RankFusion-RAG"
            )


            # ==================================================
            # ANSWERS
            # ==================================================

            standard_answer = get_answer(
                standard_section
            )

            rankfusion_answer = get_answer(
                rankfusion_section
            )


            # ==================================================
            # METRICS
            # ==================================================

            (
                standard_metrics,
                rankfusion_metrics
            ) = extract_metrics_from_comparison(
                driver
            )

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

            for metric_name in metric_names:

                if not standard_metrics.get(
                    metric_name
                ):

                    standard_metrics[
                        metric_name
                    ] = get_metric(
                        standard_section,
                        metric_name
                    )

                if not rankfusion_metrics.get(
                    metric_name
                ):

                    rankfusion_metrics[
                        metric_name
                    ] = get_metric(
                        rankfusion_section,
                        metric_name
                    )


            # ==================================================
            # SCORES
            # ==================================================

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

            standard_time = parse_time(
                standard_metrics.get(
                    "Response Time"
                )
            )

            rankfusion_time = parse_time(
                rankfusion_metrics.get(
                    "Response Time"
                )
            )

            improvement = round(
                rankfusion_score - standard_score,
                2
            )

            if rankfusion_score > standard_score:

                better_result = "RankFusion-RAG"

            elif standard_score > rankfusion_score:

                better_result = "Standard RAG"

            else:

                better_result = "Tie"


            # ==================================================
            # SAVE RESULT
            # ==================================================

            result["status"] = "PASS"

            result["standard_rag"] = {
                "answer": standard_answer,
                "metrics": standard_metrics,
                "project_score": standard_score,
                "response_time": standard_time,
            }

            result["rankfusion_rag"] = {
                "answer": rankfusion_answer,
                "metrics": rankfusion_metrics,
                "project_score": rankfusion_score,
                "response_time": rankfusion_time,
            }

            result["better_result"] = better_result

            result[
                "rankfusion_improvement"
            ] = improvement


            # ==================================================
            # PRINT RESULT
            # ==================================================

            print()

            print(
                f"Standard RAG Project Score: "
                f"{standard_score}%"
            )

            print(
                f"RankFusion-RAG Project Score: "
                f"{rankfusion_score}%"
            )

            print(
                f"Standard Response Time: "
                f"{standard_time} s"
            )

            print(
                f"RankFusion Response Time: "
                f"{rankfusion_time} s"
            )

            print(
                f"Better Result: "
                f"{better_result}"
            )

            print(
                f"RankFusion Score Difference: "
                f"{improvement:+.2f} percentage points"
            )


            scroll_results(
                driver
            )


        except Exception as error:

            result["error"] = str(error)

            print(
                f"\nQuestion {question_id} FAILED"
            )

            print(
                f"Error: {error}"
            )

            screenshot_path = os.path.join(
                RESULTS_FOLDER,
                f"question_{question_id}_failure.png"
            )

            try:

                driver.save_screenshot(
                    screenshot_path
                )

                print(
                    f"Failure screenshot saved: "
                    f"{screenshot_path}"
                )

            except:
                pass

            dismiss_alert_if_present(
                driver
            )


        # ======================================================
        # SAVE EACH QUESTION
        # ======================================================

        individual_file = os.path.join(
            RESULTS_FOLDER,
            f"question_{question_id}_result.json"
        )

        save_json(
            individual_file,
            result
        )

        print(
            f"Result saved to: {individual_file}"
        )

        all_results.append(
            result
        )

        save_json(
            ALL_RESULTS_FILE,
            all_results
        )


        # ======================================================
        # CLEAR BEFORE NEXT QUESTION
        # ======================================================

        if index < len(questions):

            driver.execute_script(
                "window.scrollTo(0, 0);"
            )

            time.sleep(1)

            clear_chat(
                driver
            )

            time.sleep(1)


    # ==========================================================
    # FINAL SUMMARY
    # ==========================================================

    passed_results = [
        result
        for result in all_results
        if result.get("status") == "PASS"
    ]

    failed_results = [
        result
        for result in all_results
        if result.get("status") != "PASS"
    ]

    standard_scores = [
        result["standard_rag"]["project_score"]
        for result in passed_results
    ]

    rankfusion_scores = [
        result["rankfusion_rag"]["project_score"]
        for result in passed_results
    ]

    standard_times = [
        result["standard_rag"]["response_time"]
        for result in passed_results
    ]

    rankfusion_times = [
        result["rankfusion_rag"]["response_time"]
        for result in passed_results
    ]

    standard_wins = sum(
        1
        for result in passed_results
        if result.get("better_result") == "Standard RAG"
    )

    rankfusion_wins = sum(
        1
        for result in passed_results
        if result.get("better_result") == "RankFusion-RAG"
    )

    ties = sum(
        1
        for result in passed_results
        if result.get("better_result") == "Tie"
    )

    improvements = [
        result["rankfusion_improvement"]
        for result in passed_results
    ]


    summary = {

        "batch": "KMS Questions 21-30",

        "documents_in_folder": 3,

        "total_tests": len(all_results),

        "passed": len(passed_results),

        "failed": len(failed_results),

        "standard_rag": {

            "average_project_score": (
                round(mean(standard_scores), 2)
                if standard_scores
                else 0
            ),

            "wins": standard_wins,

            "average_response_time": (
                round(mean(standard_times), 2)
                if standard_times
                else 0
            ),
        },

        "rankfusion_rag": {

            "average_project_score": (
                round(mean(rankfusion_scores), 2)
                if rankfusion_scores
                else 0
            ),

            "wins": rankfusion_wins,

            "average_response_time": (
                round(mean(rankfusion_times), 2)
                if rankfusion_times
                else 0
            ),
        },

        "ties": ties,

        "average_rankfusion_improvement": (
            round(mean(improvements), 2)
            if improvements
            else 0
        ),
    }


    save_json(
        FINAL_SUMMARY_FILE,
        summary
    )


    # ==========================================================
    # PRINT FINAL SUMMARY
    # ==========================================================

    print("\n" + "=" * 70)

    print(
        "KMS QUESTIONS 21-30 - FINAL SUMMARY"
    )

    print("=" * 70)

    print(
        f"Total Tests: {summary['total_tests']}"
    )

    print(
        f"Passed: {summary['passed']}"
    )

    print(
        f"Failed: {summary['failed']}"
    )

    print()

    print(
        "Standard RAG Average Project Score: "
        f"{summary['standard_rag']['average_project_score']}%"
    )

    print(
        "RankFusion-RAG Average Project Score: "
        f"{summary['rankfusion_rag']['average_project_score']}%"
    )

    print()

    print(
        "Standard RAG Wins: "
        f"{summary['standard_rag']['wins']}"
    )

    print(
        "RankFusion-RAG Wins: "
        f"{summary['rankfusion_rag']['wins']}"
    )

    print(
        f"Ties: {summary['ties']}"
    )

    print()

    print(
        "Average RankFusion Score Difference: "
        f"{summary['average_rankfusion_improvement']:+.2f} "
        "percentage points"
    )

    print()

    print(
        "Standard Average Response Time: "
        f"{summary['standard_rag']['average_response_time']} s"
    )

    print(
        "RankFusion Average Response Time: "
        f"{summary['rankfusion_rag']['average_response_time']} s"
    )

    print()

    print(
        f"All results saved to: {ALL_RESULTS_FILE}"
    )

    print(
        f"Final summary saved to: {FINAL_SUMMARY_FILE}"
    )

    print("=" * 70)


finally:

    time.sleep(2)

    driver.quit()

    print("\nBrowser closed.")
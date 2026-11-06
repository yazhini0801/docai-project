import os
import json
import time
from statistics import mean

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_URL = "http://localhost:5173"

QUESTIONS_FILE = "kms_questions_1_50.json"

# IMPORTANT:
# This must exactly match the folder name shown in DocAI.
FOLDER_NAME = "kms"

RESULTS_FOLDER = "results/kms_1_50"

ALL_RESULTS_FILE = os.path.join(
    RESULTS_FOLDER,
    "all_results.json"
)

FINAL_SUMMARY_FILE = os.path.join(
    RESULTS_FOLDER,
    "final_summary.json"
)

WAIT_TIME = 30

# Safety ceiling only.
# Selenium proceeds immediately when the comparison finishes.
RESULT_WAIT_TIME = 300


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()

EMAIL = os.getenv("DOCAI_EMAIL")
PASSWORD = os.getenv("DOCAI_PASSWORD")

if not EMAIL:
    raise ValueError(
        "DOCAI_EMAIL was not found in the .env file."
    )

if not PASSWORD:
    raise ValueError(
        "DOCAI_PASSWORD was not found in the .env file."
    )


# ==========================================================
# CREATE RESULTS FOLDER
# ==========================================================

os.makedirs(
    RESULTS_FOLDER,
    exist_ok=True
)


# ==========================================================
# LOAD QUESTIONS
# ==========================================================

if not os.path.exists(QUESTIONS_FILE):
    raise FileNotFoundError(
        f"Questions file not found: {QUESTIONS_FILE}"
    )

with open(
    QUESTIONS_FILE,
    "r",
    encoding="utf-8"
) as file:
    questions = json.load(file)

print("=" * 70)
print("DOCAI KMS FULL SELENIUM TEST")
print("=" * 70)
print(f"Questions file : {QUESTIONS_FILE}")
print(f"Total questions: {len(questions)}")
print(f"Folder         : {FOLDER_NAME}")
print(f"Results folder : {RESULTS_FOLDER}")
print("=" * 70)


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def parse_percentage(value):
    """
    Convert values such as:
    '63.8%'
    '63.8'
    63.8

    into:
    63.8
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    text = text.replace("%", "")
    text = text.replace(",", "")

    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_time(value):
    """
    Convert values such as:
    '4.25 s'
    '4.25 sec'
    '4.25 seconds'

    into:
    4.25
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).lower().strip()

    replacements = [
        "seconds",
        "second",
        "secs",
        "sec",
        "s",
    ]

    for word in replacements:
        text = text.replace(word, "")

    text = text.strip()

    try:
        return float(text)
    except ValueError:
        return 0.0


def safe_text(element):
    """
    Safely return Selenium element text.
    """

    try:
        return element.text.strip()
    except Exception:
        return ""


def save_json(filepath, data):
    """
    Save JSON safely using UTF-8.
    """

    with open(
        filepath,
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
    """
    Dismiss browser alert if one appears.
    """

    try:
        alert = driver.switch_to.alert

        message = alert.text

        print(
            f"Browser alert detected: {message}"
        )

        alert.accept()

        return message

    except NoAlertPresentException:
        return None

    except Exception:
        return None


def scroll_results(driver):
    """
    Scroll through the comparison page so that
    dynamically rendered result sections become visible.
    """

    try:

        last_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        current_position = 0

        while current_position < last_height:

            current_position += 700

            driver.execute_script(
                f"window.scrollTo(0, {current_position});"
            )

            time.sleep(0.2)

            new_height = driver.execute_script(
                "return document.body.scrollHeight"
            )

            if new_height > last_height:
                last_height = new_height

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

    except Exception:
        pass


def clear_chat(driver, wait):
    """
    Clear the current chat before moving to
    the next question.

    This prevents old comparison results from
    being mistaken for the next result.
    """

    try:

        clear_buttons = driver.find_elements(
            By.XPATH,
            "//button[contains(normalize-space(.), 'Clear Chat')]"
            " | "
            "//button[contains(normalize-space(.), 'Clear chat')]"
        )

        if not clear_buttons:

            print(
                "Clear Chat button not found."
            )

            return

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            clear_buttons[0]
        )

        time.sleep(0.5)

        driver.execute_script(
            "arguments[0].click();",
            clear_buttons[0]
        )

        time.sleep(1)

        # Handle confirmation dialog if present
        try:

            confirm_buttons = driver.find_elements(
                By.XPATH,
                "//button[normalize-space(.)='Clear']"
                " | "
                "//button[contains(normalize-space(.), 'Confirm')]"
                " | "
                "//button[contains(normalize-space(.), 'Yes')]"
            )

            if confirm_buttons:

                driver.execute_script(
                    "arguments[0].click();",
                    confirm_buttons[-1]
                )

                time.sleep(1)

        except Exception:
            pass

        dismiss_alert_if_present(driver)

        # Return to top
        driver.execute_script(
            "window.scrollTo(0, 0);"
        )

        time.sleep(1)

        print(
            "Chat cleared."
        )

    except Exception as error:

        print(
            f"Could not clear chat: {error}"
        )


def wait_for_documents(driver, wait):
    """
    Wait until the chat page reports that
    documents are loaded.
    """

    def documents_loaded(d):

        try:

            body_text = d.find_element(
                By.TAG_NAME,
                "body"
            ).text.lower()

            return (
                "documents loaded" in body_text
                or "document loaded" in body_text
                or "documents are loaded" in body_text
            )

        except Exception:
            return False

    wait.until(documents_loaded)

    print(
        "Documents loaded successfully."
    )


def find_result_section(driver, heading_text):
    """
    Find the container associated with a result heading.

    Example:
        Standard RAG
        RankFusion-RAG
    """

    heading = driver.find_element(
        By.XPATH,
        f"//h2[contains(normalize-space(.), '{heading_text}')]"
    )

    # Try nearest meaningful parent containers.
    possible_xpaths = [
        "./ancestor::div[1]",
        "./ancestor::div[2]",
        "./ancestor::div[3]",
        "./ancestor::section[1]",
    ]

    for xpath in possible_xpaths:

        try:

            container = heading.find_element(
                By.XPATH,
                xpath
            )

            text = safe_text(container)

            if len(text) > len(heading_text):
                return container

        except Exception:
            continue

    return heading


def get_answer(section):
    """
    Attempt to extract the generated answer.

    NOTE:
    The UI structure may include additional text
    inside the result card. Metrics are the primary
    data used for quantitative evaluation.
    """

    possible_xpaths = [

        ".//*[contains(@class,'answer')]",

        ".//*[contains(@class,'response')]",

        ".//*[contains(@class,'prose')]",

        ".//p",
    ]

    for xpath in possible_xpaths:

        try:

            elements = section.find_elements(
                By.XPATH,
                xpath
            )

            texts = []

            for element in elements:

                text = safe_text(element)

                if text:
                    texts.append(text)

            if texts:
                return "\n".join(texts)

        except Exception:
            continue

    return safe_text(section)


def get_metric(section, metric_name):
    """
    Extract a metric from a result section.

    Supports common UI layouts such as:

        Project Score
        63.8%

    or:

        Project Score: 63.8%
    """

    # ------------------------------------------------------
    # METHOD 1:
    # Find exact metric label and inspect nearby elements
    # ------------------------------------------------------

    try:

        labels = section.find_elements(
            By.XPATH,
            f".//*[normalize-space(.)='{metric_name}']"
        )

        for label in labels:

            # Try next sibling
            try:

                sibling = label.find_element(
                    By.XPATH,
                    "./following-sibling::*[1]"
                )

                value = safe_text(sibling)

                if value:
                    return value

            except Exception:
                pass

            # Try parent's next sibling
            try:

                parent_sibling = label.find_element(
                    By.XPATH,
                    "../following-sibling::*[1]"
                )

                value = safe_text(parent_sibling)

                if value:
                    return value

            except Exception:
                pass

            # Try parent text
            try:

                parent = label.find_element(
                    By.XPATH,
                    ".."
                )

                parent_text = safe_text(parent)

                if parent_text:

                    cleaned = parent_text.replace(
                        metric_name,
                        ""
                    ).strip()

                    if cleaned:
                        return cleaned

            except Exception:
                pass

    except Exception:
        pass

    # ------------------------------------------------------
    # METHOD 2:
    # Search text lines
    # ------------------------------------------------------

    try:

        text = safe_text(section)

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for index, line in enumerate(lines):

            if line.lower() == metric_name.lower():

                if index + 1 < len(lines):
                    return lines[index + 1]

            if line.lower().startswith(
                metric_name.lower()
            ):

                cleaned = line[
                    len(metric_name):
                ].strip(" :")

                if cleaned:
                    return cleaned

    except Exception:
        pass

    return None


def extract_metrics_from_comparison(
    comparison_section
):
    """
    Extract Standard RAG and RankFusion-RAG metrics
    from the Performance Comparison table.

    Returns:

    {
        "standard": {...},
        "rankfusion": {...}
    }
    """

    metrics = {
        "standard": {},
        "rankfusion": {}
    }

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

    try:

        rows = comparison_section.find_elements(
            By.XPATH,
            ".//tr"
        )

        for row in rows:

            cells = row.find_elements(
                By.XPATH,
                "./th | ./td"
            )

            cell_texts = [
                safe_text(cell)
                for cell in cells
            ]

            cell_texts = [
                value
                for value in cell_texts
                if value
            ]

            if len(cell_texts) < 3:
                continue

            metric = cell_texts[0]

            matched_metric = None

            for metric_name in metric_names:

                if (
                    metric.lower()
                    == metric_name.lower()
                ):

                    matched_metric = metric_name
                    break

            if not matched_metric:
                continue

            metrics["standard"][
                matched_metric
            ] = cell_texts[1]

            metrics["rankfusion"][
                matched_metric
            ] = cell_texts[2]

    except Exception:
        pass

    return metrics


def get_performance_comparison_section(driver):
    """
    Find the Performance Comparison container.
    """

    heading = driver.find_element(
        By.XPATH,
        "//h2[contains(normalize-space(.), "
        "'Performance Comparison')]"
    )

    possible_xpaths = [
        "./ancestor::div[1]",
        "./ancestor::div[2]",
        "./ancestor::div[3]",
        "./ancestor::section[1]",
    ]

    for xpath in possible_xpaths:

        try:

            section = heading.find_element(
                By.XPATH,
                xpath
            )

            if section.find_elements(
                By.XPATH,
                ".//tr"
            ):
                return section

        except Exception:
            continue

    return heading


# ==========================================================
# START BROWSER
# ==========================================================

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

result_wait = WebDriverWait(
    driver,
    RESULT_WAIT_TIME
)

all_results = []


# ==========================================================
# MAIN TEST
# ==========================================================

try:

    # ======================================================
    # OPEN APPLICATION
    # ======================================================

    print("\nOpening DocAI...")

    driver.get(
        BASE_URL
    )

    # ======================================================
    # LOGIN
    # ======================================================

    print(
        "Logging in..."
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

    email_input.clear()
    email_input.send_keys(
        EMAIL
    )

    password_input.clear()
    password_input.send_keys(
        PASSWORD
    )

    login_buttons = driver.find_elements(
        By.XPATH,
        "//button[@type='submit']"
        " | "
        "//button[contains(normalize-space(.), 'Login')]"
        " | "
        "//button[contains(normalize-space(.), 'Sign In')]"
    )

    if not login_buttons:
        raise Exception(
            "Login button not found."
        )

    login_buttons[0].click()

    time.sleep(2)

    print(
        "Login successful."
    )

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

    print(
        f"Opening folder: {FOLDER_NAME}"
    )

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

    time.sleep(1)

    # ======================================================
    # OPEN CHAT
    # ======================================================

    open_chat = wait.until(
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
        "arguments[0].click();",
        open_chat
    )

    # ======================================================
    # WAIT FOR CHAT TEXTAREA
    # ======================================================

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//textarea[@placeholder="
                "'Ask anything about your documents...']"
            )
        )
    )

    print(
        "KMS chat page opened."
    )

    # ======================================================
    # WAIT FOR DOCUMENTS
    # ======================================================

    wait_for_documents(
        driver,
        wait
    )

    # ======================================================
    # QUESTION LOOP
    # ======================================================

    for index, question_data in enumerate(
        questions,
        start=1
    ):

        question_id = question_data["id"]
        question = question_data["question"]

        print("\n")
        print("=" * 70)
        print(
            f"QUESTION {question_id} / {len(questions)}"
        )
        print("=" * 70)
        print(question)

        question_result = {
            "question_id": question_id,
            "question": question,
            "status": "FAIL",
            "standard_rag": {},
            "rankfusion_rag": {},
            "winner": None,
            "rankfusion_improvement": None,
            "error": None,
        }

        try:

            # ------------------------------------------------
            # FIND TEXTAREA
            # ------------------------------------------------

            textarea = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//textarea[@placeholder="
                        "'Ask anything about your documents...']"
                    )
                )
            )

            textarea.clear()

            textarea.send_keys(
                question
            )

            print(
                "Question entered."
            )

            # ------------------------------------------------
            # CLICK COMPARE RAG
            # ------------------------------------------------

            compare_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(normalize-space(.), "
                        "'Compare RAG')]"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                compare_button
            )

            time.sleep(0.3)

            driver.execute_script(
                "arguments[0].click();",
                compare_button
            )

            print(
                "Compare RAG clicked."
            )

            # ------------------------------------------------
            # OPTIONAL:
            # WAIT FOR COMPARISON START MESSAGE
            # ------------------------------------------------

            try:

                WebDriverWait(
                    driver,
                    10
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
                    "RAG comparison started."
                )

            except TimeoutException:

                # The loading text may disappear too quickly.
                print(
                    "Comparison started."
                )

            # ------------------------------------------------
            # CHECK FOR ALERT
            # ------------------------------------------------

            alert_message = (
                dismiss_alert_if_present(driver)
            )

            if alert_message:

                raise Exception(
                    f"Application alert: {alert_message}"
                )

            print(
                "Waiting for Standard RAG and RankFusion-RAG..."
            )

            # ------------------------------------------------
            # WAIT FOR STANDARD RAG
            # ------------------------------------------------

            result_wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[contains(normalize-space(.), "
                        "'Standard RAG')]"
                    )
                )
            )

            # ------------------------------------------------
            # WAIT FOR RANKFUSION
            # ------------------------------------------------

            result_wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[contains(normalize-space(.), "
                        "'RankFusion-RAG')]"
                    )
                )
            )

            # ------------------------------------------------
            # WAIT FOR PERFORMANCE COMPARISON
            # ------------------------------------------------

            result_wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[contains(normalize-space(.), "
                        "'Performance Comparison')]"
                    )
                )
            )

            # ------------------------------------------------
            # WAIT UNTIL PROJECT SCORE IS ACTUALLY POPULATED
            # ------------------------------------------------

            def comparison_metrics_ready(d):

                try:

                    performance_section = (
                        get_performance_comparison_section(
                            d
                        )
                    )

                    extracted = (
                        extract_metrics_from_comparison(
                            performance_section
                        )
                    )

                    standard_score = (
                        extracted["standard"].get(
                            "Project Score"
                        )
                    )

                    rankfusion_score = (
                        extracted["rankfusion"].get(
                            "Project Score"
                        )
                    )

                    standard_time = (
                        extracted["standard"].get(
                            "Response Time"
                        )
                    )

                    rankfusion_time = (
                        extracted["rankfusion"].get(
                            "Response Time"
                        )
                    )

                    return (
                        standard_score is not None
                        and rankfusion_score is not None
                        and standard_time is not None
                        and rankfusion_time is not None
                    )

                except Exception:
                    return False

            result_wait.until(
                comparison_metrics_ready
            )

            print(
                "Both pipelines completed."
            )

            # ------------------------------------------------
            # SCROLL THROUGH RESULTS
            # ------------------------------------------------

            scroll_results(
                driver
            )

            time.sleep(0.5)

            # ------------------------------------------------
            # FIND RESULT SECTIONS
            # ------------------------------------------------

            standard_section = (
                find_result_section(
                    driver,
                    "Standard RAG"
                )
            )

            rankfusion_section = (
                find_result_section(
                    driver,
                    "RankFusion-RAG"
                )
            )

            performance_section = (
                get_performance_comparison_section(
                    driver
                )
            )

            # ------------------------------------------------
            # EXTRACT ANSWERS
            # ------------------------------------------------

            standard_answer = get_answer(
                standard_section
            )

            rankfusion_answer = get_answer(
                rankfusion_section
            )

            # ------------------------------------------------
            # EXTRACT METRICS FROM COMPARISON TABLE
            # ------------------------------------------------

            comparison_metrics = (
                extract_metrics_from_comparison(
                    performance_section
                )
            )

            standard_metrics = (
                comparison_metrics["standard"]
            )

            rankfusion_metrics = (
                comparison_metrics["rankfusion"]
            )

            # ------------------------------------------------
            # FALLBACK METRIC EXTRACTION
            # ------------------------------------------------

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

                if metric_name not in standard_metrics:

                    value = get_metric(
                        standard_section,
                        metric_name
                    )

                    if value is not None:
                        standard_metrics[
                            metric_name
                        ] = value

                if metric_name not in rankfusion_metrics:

                    value = get_metric(
                        rankfusion_section,
                        metric_name
                    )

                    if value is not None:
                        rankfusion_metrics[
                            metric_name
                        ] = value

            # ------------------------------------------------
            # PROJECT SCORES
            # ------------------------------------------------

            standard_project_score = (
                parse_percentage(
                    standard_metrics.get(
                        "Project Score"
                    )
                )
            )

            rankfusion_project_score = (
                parse_percentage(
                    rankfusion_metrics.get(
                        "Project Score"
                    )
                )
            )

            # ------------------------------------------------
            # RESPONSE TIMES
            # ------------------------------------------------

            standard_response_time = (
                parse_time(
                    standard_metrics.get(
                        "Response Time"
                    )
                )
            )

            rankfusion_response_time = (
                parse_time(
                    rankfusion_metrics.get(
                        "Response Time"
                    )
                )
            )

            # ------------------------------------------------
            # RANKFUSION DIFFERENCE
            # ------------------------------------------------

            rankfusion_improvement = round(
                rankfusion_project_score
                - standard_project_score,
                2
            )

            # ------------------------------------------------
            # WINNER
            # ------------------------------------------------

            if (
                rankfusion_project_score
                > standard_project_score
            ):

                winner = "RankFusion-RAG"

            elif (
                standard_project_score
                > rankfusion_project_score
            ):

                winner = "Standard RAG"

            else:

                winner = "Tie"

            # ------------------------------------------------
            # BUILD RESULT
            # ------------------------------------------------

            question_result[
                "standard_rag"
            ] = {
                "answer": standard_answer,
                "metrics": standard_metrics,
                "project_score": standard_project_score,
                "response_time": standard_response_time,
            }

            question_result[
                "rankfusion_rag"
            ] = {
                "answer": rankfusion_answer,
                "metrics": rankfusion_metrics,
                "project_score": rankfusion_project_score,
                "response_time": rankfusion_response_time,
            }

            question_result[
                "winner"
            ] = winner

            question_result[
                "rankfusion_improvement"
            ] = rankfusion_improvement

            question_result[
                "status"
            ] = "PASS"

            question_result[
                "error"
            ] = None

            # ------------------------------------------------
            # PRINT RESULT
            # ------------------------------------------------

            print("\nRESULTS COLLECTED")
            print("-" * 70)

            print(
                f"Standard Project Score : "
                f"{standard_project_score:.2f}%"
            )

            print(
                f"RankFusion Project Score: "
                f"{rankfusion_project_score:.2f}%"
            )

            print(
                f"Standard Response Time : "
                f"{standard_response_time:.2f} s"
            )

            print(
                f"RankFusion Response Time: "
                f"{rankfusion_response_time:.2f} s"
            )

            print(
                f"Winner                 : "
                f"{winner}"
            )

            print(
                f"RankFusion Difference  : "
                f"{rankfusion_improvement:+.2f} pp"
            )

        # ==================================================
        # QUESTION FAILURE
        # ==================================================

        except Exception as error:

            error_message = str(error)

            question_result[
                "status"
            ] = "FAIL"

            question_result[
                "error"
            ] = error_message

            print(
                f"\nQUESTION {question_id} FAILED"
            )

            print(
                f"Error: {error_message}"
            )

            # Save screenshot
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

            except Exception:
                pass

            dismiss_alert_if_present(
                driver
            )

        # ==================================================
        # SAVE INDIVIDUAL QUESTION IMMEDIATELY
        # ==================================================

        individual_result_file = os.path.join(
            RESULTS_FOLDER,
            f"question_{question_id}_result.json"
        )

        save_json(
            individual_result_file,
            question_result
        )

        print(
            f"Result saved to: "
            f"{individual_result_file}"
        )

        # ==================================================
        # UPDATE ALL RESULTS
        # ==================================================

        all_results.append(
            question_result
        )

        save_json(
            ALL_RESULTS_FILE,
            all_results
        )

        print(
            f"Progress saved: "
            f"{len(all_results)}/{len(questions)}"
        )

        # ==================================================
        # CLEAR CHAT BEFORE NEXT QUESTION
        # ==================================================

        if index < len(questions):

            clear_chat(
                driver,
                wait
            )

            # Make sure textarea returns
            try:

                wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//textarea[@placeholder="
                            "'Ask anything about your documents...']"
                        )
                    )
                )

            except Exception:
                pass


    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    print("\n")
    print("=" * 70)
    print("GENERATING FINAL KMS SUMMARY")
    print("=" * 70)

    passed_results = [
        result
        for result in all_results
        if result["status"] == "PASS"
    ]

    failed_results = [
        result
        for result in all_results
        if result["status"] == "FAIL"
    ]

    # ------------------------------------------------------
    # STANDARD SCORES
    # ------------------------------------------------------

    standard_scores = [
        result["standard_rag"]["project_score"]
        for result in passed_results
    ]

    # ------------------------------------------------------
    # RANKFUSION SCORES
    # ------------------------------------------------------

    rankfusion_scores = [
        result["rankfusion_rag"]["project_score"]
        for result in passed_results
    ]

    # ------------------------------------------------------
    # RESPONSE TIMES
    # ------------------------------------------------------

    standard_times = [
        result["standard_rag"]["response_time"]
        for result in passed_results
    ]

    rankfusion_times = [
        result["rankfusion_rag"]["response_time"]
        for result in passed_results
    ]

    # ------------------------------------------------------
    # IMPROVEMENTS
    # ------------------------------------------------------

    improvements = [
        result["rankfusion_improvement"]
        for result in passed_results
    ]

    # ------------------------------------------------------
    # WINS
    # ------------------------------------------------------

    standard_wins = sum(
        1
        for result in passed_results
        if result["winner"] == "Standard RAG"
    )

    rankfusion_wins = sum(
        1
        for result in passed_results
        if result["winner"] == "RankFusion-RAG"
    )

    ties = sum(
        1
        for result in passed_results
        if result["winner"] == "Tie"
    )

    # ------------------------------------------------------
    # SUMMARY OBJECT
    # ------------------------------------------------------

    summary = {

        "batch": "KMS Questions 1-50",

        "documents_in_folder": 3,

        "total_tests": len(all_results),

        "passed": len(passed_results),

        "failed": len(failed_results),

        "failed_question_ids": [
            result["question_id"]
            for result in failed_results
        ],

        "standard_rag": {

            "average_project_score": (
                round(
                    mean(standard_scores),
                    2
                )
                if standard_scores
                else 0
            ),

            "wins": standard_wins,

            "average_response_time": (
                round(
                    mean(standard_times),
                    2
                )
                if standard_times
                else 0
            )
        },

        "rankfusion_rag": {

            "average_project_score": (
                round(
                    mean(rankfusion_scores),
                    2
                )
                if rankfusion_scores
                else 0
            ),

            "wins": rankfusion_wins,

            "average_response_time": (
                round(
                    mean(rankfusion_times),
                    2
                )
                if rankfusion_times
                else 0
            )
        },

        "ties": ties,

        "average_rankfusion_improvement": (
            round(
                mean(improvements),
                2
            )
            if improvements
            else 0
        )
    }

    # ======================================================
    # SAVE FINAL SUMMARY
    # ======================================================

    save_json(
        FINAL_SUMMARY_FILE,
        summary
    )

    # ======================================================
    # PRINT SUMMARY
    # ======================================================

    print(
        json.dumps(
            summary,
            indent=4
        )
    )

    print("\n")
    print("=" * 70)
    print("KMS TEST COMPLETED")
    print("=" * 70)

    print(
        f"Total questions : {len(all_results)}"
    )

    print(
        f"Passed          : {len(passed_results)}"
    )

    print(
        f"Failed          : {len(failed_results)}"
    )

    if standard_scores:

        print(
            f"Standard Average: "
            f"{mean(standard_scores):.2f}%"
        )

    if rankfusion_scores:

        print(
            f"RankFusion Average: "
            f"{mean(rankfusion_scores):.2f}%"
        )

    print(
        f"Standard Wins   : {standard_wins}"
    )

    print(
        f"RankFusion Wins : {rankfusion_wins}"
    )

    print(
        f"Ties            : {ties}"
    )

    if standard_times:

        print(
            f"Standard Avg Time: "
            f"{mean(standard_times):.2f} s"
        )

    if rankfusion_times:

        print(
            f"RankFusion Avg Time: "
            f"{mean(rankfusion_times):.2f} s"
        )

    if improvements:

        print(
            f"Average RankFusion Difference: "
            f"{mean(improvements):+.2f} pp"
        )

    print(
        f"\nAll results saved to:\n"
        f"{ALL_RESULTS_FILE}"
    )

    print(
        f"\nFinal summary saved to:\n"
        f"{FINAL_SUMMARY_FILE}"
    )


# ==========================================================
# FATAL ERROR
# ==========================================================

except Exception as fatal_error:

    print("\n")
    print("=" * 70)
    print("FATAL TEST ERROR")
    print("=" * 70)

    print(
        str(fatal_error)
    )

    # Preserve whatever completed results exist.
    if all_results:

        save_json(
            ALL_RESULTS_FILE,
            all_results
        )

        print(
            f"Existing results preserved in "
            f"{ALL_RESULTS_FILE}"
        )

    try:

        fatal_screenshot = os.path.join(
            RESULTS_FOLDER,
            "fatal_error.png"
        )

        driver.save_screenshot(
            fatal_screenshot
        )

        print(
            f"Screenshot saved: "
            f"{fatal_screenshot}"
        )

    except Exception:
        pass


# ==========================================================
# CLOSE BROWSER
# ==========================================================

finally:

    print(
        "\nClosing browser..."
    )

    try:
        driver.quit()
    except Exception:
        pass

    print(
        "Browser closed."
    )
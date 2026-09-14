import os
import json
import time

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==========================================================
# SETTINGS
# ==========================================================

BASE_URL = "http://localhost:5173"
QUESTIONS_FILE = "test_questions.json"
FOLDER_NAME = "Cloud computing"

RESULTS_FOLDER = "results"

ALL_RESULTS_FILE = os.path.join(
    RESULTS_FOLDER,
    "all_results.json"
)

FINAL_SUMMARY_FILE = os.path.join(
    RESULTS_FOLDER,
    "final_summary.json"
)


# ==========================================================
# LOAD LOGIN DETAILS
# ==========================================================

load_dotenv()

EMAIL = os.getenv("DOCAI_EMAIL")
PASSWORD = os.getenv("DOCAI_PASSWORD")

if not EMAIL or not PASSWORD:
    raise ValueError(
        "DOCAI_EMAIL or DOCAI_PASSWORD is missing from .env"
    )


# ==========================================================
# LOAD QUESTIONS
# ==========================================================

with open(
    QUESTIONS_FILE,
    "r",
    encoding="utf-8"
) as file:
    questions = json.load(file)

if not questions:
    raise ValueError(
        "No questions found in test_questions.json"
    )


# ==========================================================
# CREATE RESULTS FOLDER
# ==========================================================

os.makedirs(
    RESULTS_FOLDER,
    exist_ok=True
)


# ==========================================================
# START BROWSER
# ==========================================================

driver = webdriver.Chrome()

driver.maximize_window()

wait = WebDriverWait(
    driver,
    30
)

result_wait = WebDriverWait(
    driver,
    180
)


# ==========================================================
# HELPER: GET COMPARISON TABLE METRIC
# ==========================================================

def get_metric(metric_name, column):

    xpath = (
        "//tr[td[1][normalize-space()="
        f"'{metric_name}']]"
        f"/td[{column}]"
    )

    element = driver.find_element(
        By.XPATH,
        xpath
    )

    return element.text.strip()


# ==========================================================
# HELPER: GET ANSWER
# ==========================================================

def get_answer(panel_title):

    panel_heading = driver.find_element(
        By.XPATH,
        f"//h2[normalize-space()='{panel_title}']"
    )

    panel = panel_heading.find_element(
        By.XPATH,
        "./ancestor::div"
        "[.//h3[normalize-space()='Answer']][1]"
    )

    answer_title = panel.find_element(
        By.XPATH,
        ".//h3[normalize-space()='Answer']"
    )

    answer_box = answer_title.find_element(
        By.XPATH,
        "./following-sibling::div[1]"
    )

    return answer_box.text.strip()


# ==========================================================
# HELPER: SCROLL THROUGH RESULTS
# ==========================================================

def scroll_results():

    driver.execute_script(
        "window.scrollTo(0, 0);"
    )

    time.sleep(0.5)

    current_position = 0

    page_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    while current_position < page_height:

        current_position += 700

        driver.execute_script(
            f"window.scrollTo(0, {current_position});"
        )

        time.sleep(0.25)

        page_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )


# ==========================================================
# HELPER: CLEAR CHAT
# ==========================================================

def clear_chat():

    driver.execute_script(
        "window.scrollTo(0, 0);"
    )

    clear_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[normalize-space()='Clear']"
            )
        )
    )

    clear_button.click()

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(text(),'Ready to compare')]"
            )
        )
    )

    time.sleep(0.5)


# ==========================================================
# HELPER: CONVERT PERCENTAGE TO NUMBER
# ==========================================================

def parse_percentage(value):

    if not value:
        return 0.0

    try:
        return float(
            str(value)
            .replace("%", "")
            .strip()
        )

    except ValueError:
        return 0.0


# ==========================================================
# HELPER: CONVERT RESPONSE TIME TO NUMBER
# ==========================================================

def parse_response_time(value):

    if not value:
        return 0.0

    try:
        return float(
            str(value)
            .replace("s", "")
            .strip()
        )

    except ValueError:
        return 0.0


# ==========================================================
# MAIN
# ==========================================================

all_results = []


try:

    print()
    print("=" * 70)
    print("DOCAI FULL SELENIUM TEST")
    print("=" * 70)

    print(
        f"Total questions: {len(questions)}"
    )


    # ======================================================
    # OPEN DOCAI
    # ======================================================

    driver.get(
        BASE_URL
    )


    # ======================================================
    # LOGIN
    # ======================================================

    email_box = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//input[@placeholder='Enter your email']"
            )
        )
    )

    password_box = driver.find_element(
        By.XPATH,
        "//input[@placeholder='Enter your password']"
    )

    login_button = driver.find_element(
        By.XPATH,
        "//button[contains(text(),'Login')]"
    )

    email_box.send_keys(
        EMAIL
    )

    password_box.send_keys(
        PASSWORD
    )

    login_button.click()

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(text(),'Welcome back')]"
            )
        )
    )

    print(
        "Login successful"
    )


    # ======================================================
    # ZOOM 50%
    # ======================================================

    driver.execute_script(
        "document.body.style.zoom='50%'"
    )


    # ======================================================
    # OPEN CLOUD COMPUTING FOLDER
    # ======================================================

    cloud_folder = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                f"//*[normalize-space()='{FOLDER_NAME}']"
            )
        )
    )

    folder_card = cloud_folder.find_element(
        By.XPATH,
        "./ancestor::div"
        "[.//button[contains(text(),'Open Folder')]][1]"
    )

    open_folder_button = folder_card.find_element(
        By.XPATH,
        ".//button[contains(text(),'Open Folder')]"
    )

    open_folder_button.click()

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                f"//h1[contains(text(),'{FOLDER_NAME}')]"
            )
        )
    )

    print(
        "Cloud computing folder opened"
    )

    driver.execute_script(
        "document.body.style.zoom='50%'"
    )


    # ======================================================
    # OPEN CHAT
    # ======================================================

    open_chat_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(text(),'Open Chat')]"
            )
        )
    )

    open_chat_button.click()

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//h1[contains(text(),"
                "'Compare your RAG pipelines')]"
            )
        )
    )

    print(
        "Chat page opened"
    )

    driver.execute_script(
        "document.body.style.zoom='50%'"
    )

    time.sleep(1)


    # ======================================================
    # METRICS TO COLLECT
    # ======================================================

    metrics = [
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


    # ======================================================
    # RUN EVERY QUESTION
    # ======================================================

    for index, question_data in enumerate(
        questions,
        start=1
    ):

        question_id = question_data["id"]

        test_question = question_data[
            "question"
        ]

        print()
        print("=" * 70)

        print(
            f"TEST {index}/{len(questions)}"
        )

        print(
            f"Question {question_id}: "
            f"{test_question}"
        )

        print("=" * 70)


        try:

            # ==================================================
            # QUESTION BOX
            # ==================================================

            question_box = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//textarea[@placeholder="
                        "'Ask anything about your documents...']"
                    )
                )
            )

            question_box.clear()

            question_box.send_keys(
                test_question
            )

            print(
                "Question entered"
            )


            # ==================================================
            # COMPARE
            # ==================================================

            compare_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(),'Compare RAG')]"
                    )
                )
            )

            compare_button.click()

            print(
                "Compare RAG clicked"
            )


            # ==================================================
            # WAIT FOR LOADING
            # ==================================================

            wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(text(),"
                        "'Comparing RAG pipelines')]"
                    )
                )
            )

            print(
                "Comparison running..."
            )


            # ==================================================
            # WAIT FOR RESULTS
            # ==================================================

            result_wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h2[normalize-space()="
                        "'Performance Comparison']"
                    )
                )
            )

            print(
                "Comparison completed"
            )


            # ==================================================
            # ANSWERS
            # ==================================================

            standard_answer = get_answer(
                "Standard RAG"
            )

            docrank_answer = get_answer(
                "DocRank-RAG"
            )


            # ==================================================
            # METRICS
            # ==================================================

            standard_metrics = {}

            docrank_metrics = {}

            for metric in metrics:

                standard_metrics[
                    metric
                ] = get_metric(
                    metric,
                    2
                )

                docrank_metrics[
                    metric
                ] = get_metric(
                    metric,
                    3
                )


            # ==================================================
            # BETTER RESULT
            # ==================================================

            try:

                better_result = driver.find_element(
                    By.XPATH,
                    "//*[normalize-space()='Better Result']"
                    "/following-sibling::h3"
                ).text.strip()

            except Exception:

                # Fallback based on project score

                standard_score = parse_percentage(
                    standard_metrics[
                        "Project Score"
                    ]
                )

                docrank_score = parse_percentage(
                    docrank_metrics[
                        "Project Score"
                    ]
                )

                if docrank_score > standard_score:

                    better_result = "DocRank-RAG"

                elif standard_score > docrank_score:

                    better_result = "Standard RAG"

                else:

                    better_result = "Tie"


            # ==================================================
            # IMPROVEMENT
            # ==================================================

            try:

                improvement_element = driver.find_element(
                    By.XPATH,
                    "//*[contains(text(),"
                    "'DocRank improvement:')]"
                )

                improvement = (
                    improvement_element.text
                    .replace(
                        "DocRank improvement:",
                        ""
                    )
                    .strip()
                )

            except Exception:

                standard_score = parse_percentage(
                    standard_metrics[
                        "Project Score"
                    ]
                )

                docrank_score = parse_percentage(
                    docrank_metrics[
                        "Project Score"
                    ]
                )

                improvement_value = (
                    docrank_score
                    - standard_score
                )

                improvement = (
                    f"{improvement_value:+.1f}%"
                )


            # ==================================================
            # RESULT OBJECT
            # ==================================================

            result = {

                "test_id":
                    question_id,

                "folder":
                    FOLDER_NAME,

                "question":
                    test_question,

                "status":
                    "PASS",

                "standard_rag": {

                    "answer":
                        standard_answer,

                    "metrics":
                        standard_metrics,
                },

                "docrank_rag": {

                    "answer":
                        docrank_answer,

                    "metrics":
                        docrank_metrics,
                },

                "better_result":
                    better_result,

                "docrank_improvement":
                    improvement,
            }


            all_results.append(
                result
            )


            # ==================================================
            # SAVE INDIVIDUAL QUESTION
            # ==================================================

            individual_file = os.path.join(
                RESULTS_FOLDER,
                f"question_{question_id}_result.json"
            )

            with open(
                individual_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    result,
                    file,
                    indent=4,
                    ensure_ascii=False
                )


            # ==================================================
            # PRINT QUESTION RESULT
            # ==================================================

            print()

            print(
                "Standard Project Score:",
                standard_metrics[
                    "Project Score"
                ]
            )

            print(
                "DocRank Project Score:",
                docrank_metrics[
                    "Project Score"
                ]
            )

            print(
                "Standard Response Time:",
                standard_metrics[
                    "Response Time"
                ]
            )

            print(
                "DocRank Response Time:",
                docrank_metrics[
                    "Response Time"
                ]
            )

            print(
                "Winner:",
                better_result
            )

            print(
                "Improvement:",
                improvement
            )


            # ==================================================
            # SCROLL TO END
            # ==================================================

            scroll_results()

            print(
                "Scrolled to bottom"
            )

            time.sleep(1)


            # ==================================================
            # CLEAR BEFORE NEXT QUESTION
            # ==================================================

            if index < len(questions):

                clear_chat()

                print(
                    "Chat cleared for next question"
                )


        # ======================================================
        # QUESTION FAILURE
        # ======================================================

        except Exception as question_error:

            print()
            print(
                f"Question {question_id} FAILED"
            )

            print(
                question_error
            )

            screenshot_file = os.path.join(
                RESULTS_FOLDER,
                f"question_{question_id}_error.png"
            )

            driver.save_screenshot(
                screenshot_file
            )

            failed_result = {

                "test_id":
                    question_id,

                "folder":
                    FOLDER_NAME,

                "question":
                    test_question,

                "status":
                    "FAILED",

                "error":
                    str(question_error),
            }

            all_results.append(
                failed_result
            )


            # ==================================================
            # TRY TO RECOVER
            # ==================================================

            try:

                clear_chat()

            except Exception:

                pass


    # ======================================================
    # SAVE ALL RESULTS
    # ======================================================

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


    # ======================================================
    # FINAL SUMMARY + OVERALL WINNER
    # ======================================================

    passed_results = [
        result
        for result in all_results
        if result.get("status") == "PASS"
    ]

    passed = len(
        passed_results
    )

    failed = (
        len(all_results)
        - passed
    )


    # ======================================================
    # VALUES FOR FINAL CALCULATION
    # ======================================================

    standard_scores = []
    docrank_scores = []

    standard_times = []
    docrank_times = []

    standard_wins = 0
    docrank_wins = 0
    ties = 0


    # ======================================================
    # PROCESS EVERY SUCCESSFUL RESULT
    # ======================================================

    for result in passed_results:

        standard_metrics = (
            result[
                "standard_rag"
            ][
                "metrics"
            ]
        )

        docrank_metrics = (
            result[
                "docrank_rag"
            ][
                "metrics"
            ]
        )

        standard_score = parse_percentage(
            standard_metrics[
                "Project Score"
            ]
        )

        docrank_score = parse_percentage(
            docrank_metrics[
                "Project Score"
            ]
        )

        standard_time = parse_response_time(
            standard_metrics[
                "Response Time"
            ]
        )

        docrank_time = parse_response_time(
            docrank_metrics[
                "Response Time"
            ]
        )


        standard_scores.append(
            standard_score
        )

        docrank_scores.append(
            docrank_score
        )

        standard_times.append(
            standard_time
        )

        docrank_times.append(
            docrank_time
        )


        # ==================================================
        # COUNT WINS
        # ==================================================

        if docrank_score > standard_score:

            docrank_wins += 1

        elif standard_score > docrank_score:

            standard_wins += 1

        else:

            ties += 1


    # ======================================================
    # CALCULATE AVERAGES
    # ======================================================

    if passed > 0:

        standard_average = (
            sum(standard_scores)
            / len(standard_scores)
        )

        docrank_average = (
            sum(docrank_scores)
            / len(docrank_scores)
        )

        standard_time_average = (
            sum(standard_times)
            / len(standard_times)
        )

        docrank_time_average = (
            sum(docrank_times)
            / len(docrank_times)
        )

    else:

        standard_average = 0.0
        docrank_average = 0.0

        standard_time_average = 0.0
        docrank_time_average = 0.0


    # ======================================================
    # CALCULATE OVERALL WINNER
    # ======================================================

    if docrank_average > standard_average:

        overall_winner = "DocRank-RAG"

    elif standard_average > docrank_average:

        overall_winner = "Standard RAG"

    else:

        # If average Project Scores are equal,
        # use the number of wins as tie-breaker.

        if docrank_wins > standard_wins:

            overall_winner = "DocRank-RAG"

        elif standard_wins > docrank_wins:

            overall_winner = "Standard RAG"

        else:

            overall_winner = "Tie"


    # ======================================================
    # DOCRANK AVERAGE IMPROVEMENT
    # ======================================================

    average_improvement = (
        docrank_average
        - standard_average
    )


    # ======================================================
    # FINAL SUMMARY OBJECT
    # ======================================================

    final_summary = {

        "total_tests":
            len(all_results),

        "passed":
            passed,

        "failed":
            failed,

        "standard_rag": {

            "average_project_score":
                round(
                    standard_average,
                    2
                ),

            "wins":
                standard_wins,

            "average_response_time":
                round(
                    standard_time_average,
                    2
                ),
        },

        "docrank_rag": {

            "average_project_score":
                round(
                    docrank_average,
                    2
                ),

            "wins":
                docrank_wins,

            "average_response_time":
                round(
                    docrank_time_average,
                    2
                ),
        },

        "ties":
            ties,

        "average_docrank_improvement":
            round(
                average_improvement,
                2
            ),

        "overall_winner":
            overall_winner,
    }


    # ======================================================
    # SAVE FINAL SUMMARY JSON
    # ======================================================

    with open(
        FINAL_SUMMARY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_summary,
            file,
            indent=4,
            ensure_ascii=False
        )


    # ======================================================
    # PRINT FINAL REPORT
    # ======================================================

    print()
    print("=" * 70)
    print("DOCAI FINAL RAG COMPARISON")
    print("=" * 70)

    print(
        "Total questions:",
        len(all_results)
    )

    print(
        "Passed:",
        passed
    )

    print(
        "Failed:",
        failed
    )

    print()

    print(
        f"Standard RAG Average Project Score : "
        f"{standard_average:.2f}%"
    )

    print(
        f"DocRank-RAG Average Project Score  : "
        f"{docrank_average:.2f}%"
    )

    print()

    print(
        "Standard RAG Wins :",
        standard_wins
    )

    print(
        "DocRank-RAG Wins  :",
        docrank_wins
    )

    print(
        "Ties              :",
        ties
    )

    print()

    print(
        f"Standard RAG Average Response Time : "
        f"{standard_time_average:.2f} s"
    )

    print(
        f"DocRank-RAG Average Response Time  : "
        f"{docrank_time_average:.2f} s"
    )

    print()

    print(
        "DocRank Average Project Score Improvement : "
        f"{average_improvement:+.2f} percentage points"
    )

    print()
    print("-" * 70)

    print(
        "OVERALL BEST RAG SYSTEM:",
        overall_winner
    )

    print("-" * 70)

    print()

    print(
        "All results saved to:",
        ALL_RESULTS_FILE
    )

    print(
        "Final summary saved to:",
        FINAL_SUMMARY_FILE
    )

    print("=" * 70)


    time.sleep(5)


# ==========================================================
# MAJOR FAILURE
# ==========================================================

except Exception as error:

    print()
    print("=" * 70)
    print("TEST SUITE FAILED")
    print("=" * 70)

    print(
        error
    )

    driver.save_screenshot(
        "selenium_suite_error.png"
    )


# ==========================================================
# CLOSE
# ==========================================================

finally:

    driver.quit()
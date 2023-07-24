import os
import time
import click
from bs4 import BeautifulSoup
from color import Colors
from config_setup import (
    save_credentials_to_config,
    load_credentials_from_config,
)
import leetcode
import leetcode.auth
import requests


def print_question_data(question):
    question_id = question.get("frontendQuestionId")
    title = question.get("title")
    difficulty = question.get("difficulty")
    ac_rate = question.get("acRate")
    status = question.get("status")

    # Fix ac_rate position regardless of the length of difficulty
    difficulty_color = ""
    if difficulty == "Easy":
        difficulty_color = Colors.GREEN
    elif difficulty == "Medium":
        difficulty_color = Colors.ORANGE
    elif difficulty == "Hard":
        difficulty_color = Colors.RED

    # Set fixed widths for the title and difficulty columns
    title_width = 50
    difficulty_width = 10
    # Width of the tick button

    # Align and pad the title and difficulty columns
    title_formatted = title.ljust(title_width)[:title_width]
    difficulty_formatted = (
        f"{difficulty_color}{difficulty.ljust(difficulty_width)}{Colors.RESET}"
    )

    # Determine the status symbol and color
    if status == "ac":
        status_symbol = "✔"
        status_color = Colors.GREEN
    else:
        status_symbol = "✘"
        status_color = Colors.RED

    print(
        f"({status_color}{status_symbol.center(2)}{Colors.RESET})"
        f"[{str(question_id).rjust(4)}]  {title_formatted}  {difficulty_formatted}  ({ac_rate:.2f}%)"
    )


def execute_graphql_query(api_instance, data):
    api_url = "https://leetcode.com/graphql/"

    csrf_token, leetcode_session = api_instance

    headers = {
        "Content-Type": "application/json",
        "Cookie": f"csrftoken={csrf_token}; LEETCODE_SESSION={leetcode_session}",
        "Referer": "https://leetcode.com",
    }

    data = {
        "operationName": data.get("operationName"),
        "query": data.get("query"),
        "variables": data.get("variables"),
    }

    response = requests.post(api_url, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"GraphQL query failed with status code {response.status_code}:")
        print(response.text)
        return None


def get_question_data_by_id(api_instance, q):
    csrf_token, leetcode_session = api_instance

    query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
          problemsetQuestionList: questionList(
            categorySlug: $categorySlug
            limit: $limit
            skip: $skip
            filters: $filters
          ) {
            total: totalNum
            questions: data {
              acRate
              difficulty
              freqBar
              questionId
              frontendQuestionId: questionFrontendId
              isFavor
              paidOnly: isPaidOnly
              status
              title
              titleSlug
              topicTags {
                name
                id
                slug
              }
              hasSolution
              hasVideoSolution
            }
          }
        }
    """

    if ":" in q:
        start, end = map(int, q.split(":"))
        skip = start
        print(skip)
        limit = end
        print(limit)
        filters = {}
    else:
        limit = 1
        skip = 0
        filters = {"searchKeywords": str(q)}

    query_variables = {
        "categorySlug": "",
        "skip": skip,
        "limit": limit,
        "filters": filters,
    }

    data = {
        "operationName": "problemsetQuestionList",
        "query": query,
        "variables": query_variables,
    }

    api_response = execute_graphql_query(api_instance, data)

    if (
            api_response
            and "data" in api_response
            and "problemsetQuestionList" in api_response["data"]
    ):
        return api_response["data"]["problemsetQuestionList"]["questions"]
    return None


# --solve
def get_question_detail(api_instance, title_slug):
    csrf_token, leetcode_session = api_instance

    query = """
        query getQuestionDetail($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            boundTopicId
            title
            content
            translatedTitle
            isPaidOnly
            difficulty
            likes
            dislikes
            isLiked
            similarQuestions
            contributors {
              username
              profileUrl
              avatarUrl
              __typename
            }
            langToValidPlayground
            topicTags {
              name
              slug
              translatedName
              __typename
            }
            companyTagStats
            codeSnippets {
              lang
              langSlug
              code
              __typename
            }
            stats
            codeDefinition
            hints
            solution {
              id
              canSeeDetail
              __typename
            }
            status
            sampleTestCase
            enableRunCode
            metaData
            translatedContent
            judgerAvailable
            judgeType
            mysqlSchemas
            enableTestMode
            envInfo
            __typename
          }
        }
    """

    query_variables = {
        "titleSlug": title_slug,
    }

    data = {
        "operationName": "getQuestionDetail",
        "query": query,
        "variables": query_variables,
    }

    api_response = execute_graphql_query(api_instance, data)

    if api_response and "data" in api_response and "question" in api_response["data"]:
        return api_response["data"]["question"]
    return None


LANG_EXTENSIONS = {
    "cpp": "cpp",
    "java": "java",
    "python": "py",
    "python3": "py",
    "c": "c",
    "csharp": "cs",
    "javascript": "js",
    "ruby": "rb",
    "swift": "swift",
    "golang": "go",
    "scala": "scala",
    "kotlin": "kt",
    "rust": "rs",
    "php": "php",
    "typescript": "ts",
    "racket": "rkt",
    "erlang": "erl",
    "elixir": "ex",
    "dart": "dart",
}


def get_code_snippets(question_detail_data, lang_slug):
    code_snippets = question_detail_data.get("codeSnippets", [])
    return next(
        (
            snippet["code"]
            for snippet in code_snippets
            if snippet["langSlug"] == lang_slug
        ),
        None,
    )


def write_code_snippet_to_file(question_detail_data, lang, title_slug):
    code = get_code_snippets(question_detail_data, lang)
    if code:
        lang_extension = LANG_EXTENSIONS.get(lang)
        if lang_extension:
            file_path = os.path.join(
                "code_editor",
                f"{question_detail_data['questionFrontendId']}_{title_slug}.{lang_extension}",
            )
            with open(file_path, "w") as file:
                file.write(code)
            print(f"Code snippet for {lang} has been written to {file_path}.")
        else:
            print(f"Language extension for {lang} is not available.")
    else:
        print(f"Code snippet for {lang} is not available for this question.")


def display_available_languages(question_detail_data):
    code_snippets = question_detail_data.get("codeSnippets", [])
    if code_snippets:
        print("Available Languages:")
        for index, snippet in enumerate(code_snippets):
            lang_slug = snippet.get("langSlug")
            lang_name = snippet.get("text") or lang_slug
            print(f"{index + 1}. {lang_name} ({lang_slug})")
    else:
        print("No code snippets available.")


def display_question_detail(api_instance, title_slug):
    question_detail_data = get_question_detail(api_instance, title_slug)
    if question_detail_data:
        question_url = f"https://leetcode.com/problems/{title_slug}/"
        print("Question URL:", question_url)

        content_html = question_detail_data.get("content")
        content_text = BeautifulSoup(content_html, "html.parser").get_text()
        print("Question Content:\n", content_text)

        display_available_languages(question_detail_data)

        lang_input = (
            input("Enter the index of the language you want to code: ").strip().lower()
        )
        try:
            lang_index = int(lang_input)
            if 1 <= lang_index <= len(question_detail_data.get("codeSnippets", [])):
                selected_lang = question_detail_data["codeSnippets"][lang_index - 1][
                    "langSlug"
                ]
                write_code_snippet_to_file(
                    question_detail_data, selected_lang, title_slug
                )
            else:
                print("Invalid index. Please enter a valid index.")
        except ValueError:
            print("Invalid input. Please enter a valid index.")


def non_lib_configuration():  # had to change name becasue of python-leetcode lib
    leetcode_session, csrf_token = load_credentials_from_config()
    if not leetcode_session or not csrf_token:
        leetcode_session = click.prompt("Enter your LeetCode session", type=str)
        csrf_token = click.prompt("Enter your CSRF token", type=str)
        save_credentials_to_config(leetcode_session, csrf_token)
    return leetcode_session, csrf_token


def get_title_slug_from_filename(filepath):
    base_name = os.path.basename(filepath)
    title_slug, _ = os.path.splitext(base_name)
    parts = title_slug.split("_")
    return "_".join(parts[1:])


# --test


def interpret_solution(
        title_slug, payload, api_instance
):  # used python-leetocde library
    test_submission = leetcode.TestSubmission(
        data_input=payload["data_input"],
        typed_code=payload["typed_code"],
        question_id=payload["question_id"],
        test_mode=False,
        lang="python3",  #change this
    )
    interpretation_id = api_instance.problems_problem_interpret_solution_post(
        problem=title_slug, body=test_submission
    )

    # print("Test has been queued. Result:")
    # print(interpretation_id)

    time.sleep(3)

    test_submission_result = api_instance.submissions_detail_id_check_get(
        id=interpretation_id.interpret_id
    )

    print("Got test result:")
    # print(leetcode.TestSubmissionResult(**test_submission_result))
    print_test_result(test_submission_result, payload["data_input"])


def print_test_result(test_data, data_input):
    status_msg = test_data.get("status_msg")
    status_runtime = test_data.get("status_runtime")
    code_answer = test_data.get("code_answer")
    expected_code_answer = test_data.get("expected_code_answer")
    status_color = Colors.GREEN if status_msg == "Accepted" else Colors.RED

    print("".center(40, "="))
    print(f"{status_color}{status_msg}{Colors.RESET}     ({status_runtime})")
    print("".center(40, "="))
    print("input".center(40, "-"))
    print(data_input)
    print("your code output".center(40, "-"))
    print(code_answer)
    print("expected output".center(40, "-"))
    print(expected_code_answer)
    print("".center(40, "="))


# --submit
def submit_solution(
        api_instance, title_slug, code, question_id
):  # used python-leetocde library
    # Prepare the submission data
    submission = leetcode.Submission(
        judge_type="large",
        typed_code=code,
        question_id=question_id,
        test_mode=False,
        lang="python3", #change this
    )

    # Submit the code and get the submission ID
    submission_id = api_instance.problems_problem_submit_post(
        problem=title_slug, body=submission
    )
    print("Submission has been queued. Result:")
    print(submission_id)

    # Wait for a few seconds for the submission to be processed
    time.sleep(3)  # FIXME: should probably be a busy-waiting loop

    # Get the submission result
    submission_result = api_instance.submissions_detail_id_check_get(
        id=submission_id.submission_id
    )
    print("Got submission result:")
    # print(leetcode.SubmissionResult(**submission_result))
    print_submission_data(submission_result)


def print_submission_data(submission):  # used python-leetocde library
    run_success = submission.get("run_success")
    status_msg = submission.get("status_msg")

    if run_success and status_msg == "Accepted":
        runtime_percentile = submission.get("runtime_percentile")
        status_runtime = submission.get("status_runtime")
        status_memory = submission.get("status_memory")
        # submission_id = submission.get("submission_id")
        # question_id = submission.get("question_id")

        # Determine the status color and symbol
        status_symbol = "✔"
        status_color = Colors.GREEN

        # Format the runtime percentile and status runtime
        runtime_percentile_str = (
            f"{runtime_percentile:.2f}%" if runtime_percentile else "N/A"
        )
        status_runtime_str = status_runtime.split()[0] if status_runtime else "N/A"

        # Format the status memory
        status_memory_str = status_memory.split()[0] if status_memory else "N/A"

        print("".center(40, "="))
        print(f"{status_color}{status_msg}{Colors.RESET}")
        print("Runtime".center(40, "-"))
        print(f"{status_runtime_str}ms")
        print(f"Beats {runtime_percentile_str} of users with Python3")
        print("Memory".center(40, "-"))
        print(f"{status_memory_str}mb")
        print(
            f"Beats {submission.get('memory_percentile', 0.0):.2f}% of users with Python3"
        )
        print("".center(40, "="))

    elif run_success and status_msg == "Wrong Answer":
        last_testcase = submission.get("last_testcase", "")
        expected_output = submission.get("expected_output", "")
        status_color = Colors.RED

        print("".center(40, "="))
        print(f"{status_color}{status_msg}{Colors.RESET}")
        print("".center(40, "="))
        print("last testcase".center(40, "-"))
        print(last_testcase)
        print("expected output".center(40, "-"))
        print(expected_output)
        print("your output".center(40, "-"))
        print(submission.get("code_output", ""))
        print("".center(40, "="))

    elif not run_success:
        runtime_error = submission.get("runtime_error", "")
        full_runtime_error = submission.get("full_runtime_error", "")
        last_testcase = submission.get("last_testcase", "")
        status_color = Colors.RED

        runtime_error_text = BeautifulSoup(runtime_error, "html.parser")
        full_runtime_error_text = BeautifulSoup(full_runtime_error, "html.parser")

        print("".center(40, "="))
        print(f"{status_color}{status_msg}{Colors.RESET}")
        print("".center(40, "="))
        print("error".center(40, "-"))
        print(runtime_error_text)
        print(full_runtime_error_text)
        print("last test case".center(40, "-"))
        print(f"{Colors.RED}{last_testcase}{Colors.RESET}")
        print("".center(40, "="))


def initialize_leetcode_api_instance(leetcode_session):  # used python-leetocde library
    configuration = leetcode.Configuration()
    csrf_token = leetcode.auth.get_csrf_cookie(leetcode_session)

    configuration.api_key["x-csrftoken"] = csrf_token
    configuration.api_key["csrftoken"] = csrf_token
    configuration.api_key["LEETCODE_SESSION"] = leetcode_session
    configuration.api_key["Referer"] = "https://leetcode.com"
    configuration.debug = False

    api_instance = leetcode.DefaultApi(leetcode.ApiClient(configuration))
    return api_instance


@click.command()
@click.option("--config", is_flag=True, help="Enter credentials and save to config")
@click.option(
    "--question",
    "-q",
    type=str,
    default="",
    help="Specify the question ID, title, or range (e.g., 10:20)",
)
@click.option(
    "--solve",
    "-s",
    type=str,
    default="",
    help="Specify the question title slug to solve (e.g., add-two-numbers)",
)
@click.option(
    "--test",
    "-t",
    type=str,
    default="",
    help="Specify the filename containing the code and input for testing",
)
@click.option(
    "--submit",
    "-sb",
    type=str,
    default="",
    help="Specify the filename containing the code to be submitted",
)
@click.option(
    "--help", "-h",
    type=str,
    help="Specify the filename containing the code to be submitted",
)
def main(config, question, solve, test, submit, help):
    if config:
        leetcode_session, csrf_token = non_lib_configuration()
    else:
        leetcode_session, csrf_token = load_credentials_from_config()

    leetcode_api_instance = initialize_leetcode_api_instance(
        leetcode_session
    )  # here using python-leetcode

    api_instance = (csrf_token, leetcode_session)

    if solve:
        title_slug = get_question_data_by_id(api_instance, solve)[0].get("titleSlug")
        display_question_detail(api_instance, title_slug)
    elif question:
        question_data = get_question_data_by_id(api_instance, question)
        if question_data:
            sorted_question_data = sorted(
                question_data, key=lambda x: int(x["frontendQuestionId"])
            )
            for question_item in sorted_question_data:
                print_question_data(question_item)
        else:
            print(f"Question with ID or title '{question}' not found.")

    elif test:
        # print(f"Test file: {test}")
        title_slug = get_title_slug_from_filename(test)
        # print(f"Title slug: {title_slug}")
        question_detail_data = get_question_detail(api_instance, title_slug)
        if question_detail_data:
            question_id = question_detail_data.get("questionId")
            # print(f"Question ID: {question_id}")
            sample_test_case = question_detail_data.get("sampleTestCase")
            # print(f"Sample Test Case: {sample_test_case}")

            with open(test, "r") as file:
                code = file.read()

            payload = {
                "lang": "python3", #change htis
                "question_id": question_id,
                "typed_code": code,
                "data_input": sample_test_case,
            }

            interpret_solution(title_slug, payload, leetcode_api_instance)  # used here
        else:
            print(f"Question with title slug '{title_slug}' not found.")

    elif submit:
        with open(submit, "r") as file:
            code = file.read()

        title_slug = get_title_slug_from_filename(submit)
        print(f"Title slug: {title_slug}")
        question_detail_data = get_question_detail(api_instance, title_slug)
        if question_detail_data:
            question_id = question_detail_data.get("questionId")
            print(f"Question ID: {question_id}")
            submit_solution(leetcode_api_instance, title_slug, code, question_id)

    elif help:
        print("enter --question,-q for question details")
        print("enter --solve,-s for solving question")
        print("enter --test,-t for testing question")
        print("enter --submit,-sb for submitting question")
    else:
        print("enter --help for usage information")


if __name__ == "__main__":
    main() #tesr

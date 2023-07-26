import time
import click
from bs4 import BeautifulSoup
from color import Colors
from config_setup import (
    save_credentials_to_config,
    load_credentials_from_config, load_user_data_from_config, save_user_data_to_config,
)
import leetcode
import leetcode.auth
import requests
import os
import shutil
import glob


def non_lib_configuration():  # had to change name becasue of python-leetcode lib
    leetcode_session, csrf_token = load_credentials_from_config()
    if not leetcode_session or not csrf_token:
        leetcode_session = click.prompt("Enter your LeetCode session", type=str)
        csrf_token = click.prompt("Enter your CSRF token", type=str)
        save_credentials_to_config(leetcode_session, csrf_token)
    return leetcode_session, csrf_token


# print


def print_question_data(question):
    question_id = question.get("frontendQuestionId")
    title = question.get("title")
    difficulty = question.get("difficulty")
    ac_rate = question.get("acRate")
    status = question.get("status")
    is_paid = question.get("paidOnly")
    difficulty_color = ""
    if difficulty == "Easy":
        difficulty_color = Colors.GREEN
    elif difficulty == "Medium":
        difficulty_color = Colors.ORANGE
    elif difficulty == "Hard":
        difficulty_color = Colors.RED
    title_width = 50
    difficulty_width = 10
    title_formatted = title.ljust(title_width)[:title_width]
    difficulty_formatted = (
        f"{difficulty_color}{difficulty.ljust(difficulty_width)}{Colors.RESET}"
    )

    paid_indicator = "$$$" if is_paid else ""

    if status == "ac":
        status_symbol = "✔"
        status_color = Colors.GREEN
    else:
        status_symbol = "✘"
        status_color = Colors.RED
    print(
        f"({status_color}{status_symbol.center(2)}{Colors.RESET})"
        f"[{str(question_id).rjust(4)}]  {title_formatted}  {difficulty_formatted}  ({ac_rate:.2f}%)    {paid_indicator}"
    )


def print_test_result(test_data, data_input):
    status_msg = test_data.get("status_msg")

    if status_msg == "Accepted":
        status_runtime = test_data.get("status_runtime")
        code_answer = test_data.get("code_answer")
        expected_code_answer = test_data.get("expected_code_answer")
        status_color = Colors.GREEN

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
    else:
        runtime_error = test_data.get("runtime_error")
        full_runtime_error = test_data.get("full_runtime_error")
        status_color = Colors.RED

        # Use BeautifulSoup to convert the runtime error message from HTML to plain text
        soup = BeautifulSoup(full_runtime_error, "html.parser")
        plain_runtime_error = soup.get_text()

        print("".center(40, "="))
        print(f"{status_color}{status_msg}{Colors.RESET}")
        print("".center(40, "="))
        print("input".center(40, "-"))
        print(data_input)
        print("runtime error".center(40, "-"))
        print(runtime_error)
        print("full runtime error".center(40, "-"))
        print(plain_runtime_error)
        print("".center(40, "="))


def print_submission_result(submission):  # used python-leetocde library
    run_success = submission.get("run_success")
    status_msg = submission.get("status_msg")
    if run_success and status_msg == "Accepted":
        runtime_percentile = submission.get("runtime_percentile")
        status_runtime = submission.get("status_runtime")
        status_memory = submission.get("status_memory")
        status_symbol = "✔"
        status_color = Colors.GREEN
        runtime_percentile_str = (
            f"{runtime_percentile:.2f}%" if runtime_percentile else "N/A"
        )
        status_runtime_str = status_runtime.split()[0] if status_runtime else "N/A"
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


# leetcode-lib


def initialize_leetcode_api_instance(
        leetcode_session, leetcode_csrf_token
):  # used python-leetocde library
    configuration = leetcode.Configuration()
    csrf_token = leetcode_csrf_token
    configuration.api_key["x-csrftoken"] = csrf_token
    configuration.api_key["csrftoken"] = csrf_token
    configuration.api_key["LEETCODE_SESSION"] = leetcode_session
    configuration.api_key["Referer"] = "https://.com"
    configuration.debug = False

    api_instance = .DefaultApi(.ApiClient(configuration))
    return api_instance


def interpret_solution(title_slug, payload, api_instance):
    test_submission = leetcode.TestSubmission(
        data_input=payload["data_input"],
        typed_code=payload["typed_code"],
        question_id=payload["question_id"],
        test_mode=False,
        lang=payload["lang"],  # change this
    )
    interpretation_id = api_instance.problems_problem_interpret_solution_post(
        problem=title_slug, body=test_submission
    )
    time.sleep(3)
    test_submission_result = api_instance.submissions_detail_id_check_get(
        id=interpretation_id.interpret_id
    )
    print_test_result(test_submission_result, payload["data_input"])


# --submit
def submit_solution(
        api_instance, title_slug, code, question_id, lang_name
):  # used python-leetocde library
    submission = leetcode.Submission(
        judge_type="large",
        typed_code=code,
        question_id=question_id,
        test_mode=False,
        lang=lang_name,  # change this
    )
    submission_id = api_instance.problems_problem_submit_post(
        problem=title_slug, body=submission
    )
    print("Submission has been queued. Result:")
    time.sleep(3)
    submission_result = api_instance.submissions_detail_id_check_get(
        id=submission_id.submission_id
    )
    print_submission_result(submission_result)


def process_test_file(leetcode_api_instance, api_instance, test):
    title_slug, lang_name = title_and_file_extension(test)
    question_detail_data = get_question_detail(api_instance, title_slug)
    if question_detail_data:
        question_id = question_detail_data.get("questionId")
        sample_test_case = question_detail_data.get("sampleTestCase")
        with open(test, "r") as file:
            code = file.read()
        payload = {
            "lang": lang_name,
            "question_id": question_id,
            "typed_code": code,
            "data_input": sample_test_case,
        }
        interpret_solution(title_slug, payload, leetcode_api_instance)
    else:
        print(f"Question with title slug '{title_slug}' not found.")


def process_submit_file(leetcode_api_instance, api_instance, submit_file):
    with open(submit_file, "r") as file:
        code = file.read()
    title_slug, lang_name = title_and_file_extension(submit_file)
    print(f"Title slug: {title_slug}")
    question_detail_data = get_question_detail(api_instance, title_slug)
    if question_detail_data:
        question_id = question_detail_data.get("questionId")
        print(f"Question ID: {question_id}")
        submit_solution(leetcode_api_instance, title_slug, code, question_id, lang_name)
    else:
        print(f"Question with title slug '{title_slug}' not found.")


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
        limit = end
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


# --solve

LANG_EXTENSIONS = {
    "cpp": "cpp",
    "java": "java",
    # "python": "py",
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


def get_available_languages_and_code_snippets(question_detail_data):
    code_snippets = question_detail_data.get("codeSnippets", [])
    available_languages = []
    for snippet in code_snippets:
        lang_slug = snippet.get("langSlug")
        lang_name = snippet.get("text") or lang_slug
        if lang_slug.lower() not in ["python"]:
            available_languages.append((lang_slug, lang_name))
    return available_languages


def display_question_detail(api_instance, title_slug):
    question_detail_data = get_question_detail(api_instance, title_slug)
    if question_detail_data:
        question_url = f"https://leetcode.com/problems/{title_slug}/"
        print("Question URL:", question_url)

        content_html = question_detail_data.get("content")
        content_text = BeautifulSoup(content_html, "html.parser").get_text()
        print("Question Content:\n", content_text)

        user_lang = load_user_data_from_config()  # Load the USER_LANG from config
        if user_lang:
            write_code_snippet_to_file(question_detail_data, user_lang, title_slug)
        else:
            available_languages = get_available_languages_and_code_snippets(question_detail_data)
            if not available_languages:
                print("No code snippets available.")
                return
            print("Available Languages:")
            for index, (lang_slug, lang_name) in enumerate(available_languages, 1):
                print(f"{index}. {lang_slug}")
            lang_input = input("Enter the displayed index of the language you want to code: ").strip().lower()
            try:
                lang_index = int(lang_input)
                if 1 <= lang_index <= len(available_languages):
                    selected_lang = available_languages[lang_index - 1][0]
                    print(selected_lang)
                    write_code_snippet_to_file(question_detail_data, selected_lang, title_slug)
                else:
                    print("Invalid index. Please enter a valid index.")
            except ValueError:
                print("Invalid input. Please enter a valid index.")


def write_code_snippet_to_file(question_detail_data, lang, title_slug):
    code_snippets = question_detail_data.get("codeSnippets", [])
    code = next((snippet["code"] for snippet in code_snippets if snippet["langSlug"] == lang), None)
    if code:
        lang_extension = LANG_EXTENSIONS.get(lang)
        if lang_extension:
            if not os.path.exists("code_editor"):
                os.makedirs("code_editor")
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


# def display_question_detail(api_instance, title_slug):
#     question_detail_data = get_question_detail(api_instance, title_slug)
#     if question_detail_data:
#         question_url = f"https://leetcode.com/problems/{title_slug}/"
#         print("Question URL:", question_url)
#
#         content_html = question_detail_data.get("content")
#         content_text = BeautifulSoup(content_html, "html.parser").get_text()
#         print("Question Content:\n", content_text)
#
#         display_available_languages(question_detail_data)
#
#         lang_input = (
#             input("Enter the index of the language you want to code: ").strip().lower()
#         )
#         try:
#             lang_index = int(lang_input)
#             if 1 <= lang_index <= len(question_detail_data.get("codeSnippets", [])):
#                 selected_lang = question_detail_data["codeSnippets"][lang_index - 1][
#                     "langSlug"
#                 ]
#                 print(selected_lang)
#                 write_code_snippet_to_file(
#                     question_detail_data, selected_lang, title_slug
#                 )
#             else:
#                 print("Invalid index. Please enter a valid index.")
#         except ValueError:
#             print("Invalid input. Please enter a valid index.")


def get_title_slug_from_filename(filepath):
    base_name = os.path.basename(filepath)
    title_slug, _ = os.path.splitext(base_name)
    parts = title_slug.split("_")
    return "_".join(parts[1:])


def title_and_file_extension(file):
    title_slug = get_title_slug_from_filename(file)
    file_extension = file.split(".")[-1].lower()
    lang_name = list(LANG_EXTENSIONS.keys())[
        list(LANG_EXTENSIONS.values()).index(file_extension)
    ]

    return title_slug, lang_name


def print_help_usage():
    help_message = """
    IMPORTANT: python lc.py --lib
    
    Usage:
        python lc.py --config
        python lc.py --config --user-lang <language>
        python lc.py --question/-q <question_id_or_title>
        python lc.py --solve <question_id_or_title>
        python lc.py --test/-t <filename>
        python lc.py --submit/-sb <filename>

    Examples:
        python lc.py --config --user-lang=python3
        python lc.py --question 1
        python lc.py --question add-two-numbers
        python lc.py --question 10:20
        python lc.py --solve/-s add-two-numbers
        python lc.py --solve 1
        python lc.py --test test_file.py
        python lc.py --submit submit_file.py

    For any issues or feature requests, please visit:
    https://github.com/hrdkmishra/leetcode.py
    """
    print(help_message)


def replace_files():
    source_dir = "custom_lib_file/"
    destination_dir = "venv/Lib/site-packages/leetcode/models/"
    file_paths = glob.glob(os.path.join(source_dir, "*"))

    if not file_paths:
        print(f"No files found in the source directory '{source_dir}'.")
        return

    for src_path in file_paths:
        filename = os.path.basename(src_path)
        dest_path = os.path.join(destination_dir, filename)

        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
                shutil.copy(src_path, dest_path)
                print(f"File '{src_path}' replaced successfully.")
            except Exception as e:
                print(f"An error occurred while replacing the file: {e}")
        else:
            print(f"Destination path '{dest_path}' does not exist.")


@click.command()
@click.option("--config", is_flag=True, help="Enter credentials and save to config")
@click.option(
    "--user-lang",
    type=str,
    default="",
    help="Set user preferred language (e.g., python3)",
)
@click.option(
    "--lib", is_flag=True, default=False, help="Show usage information"
)
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
    "--help", "-h", is_flag=True, default=False, help="Show usage information"
)
def main(config, user_lang, question, solve, test, submit, help, lib):
    if lib:
        replace_files()
        exit()
    if config:
        leetcode_session, csrf_token = non_lib_configuration()
        # If the --user-lang option is provided, save it to config
        if user_lang:
            save_user_data_to_config(user_lang)
            exit()
    else:
        leetcode_session, csrf_token = load_credentials_from_config()

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
        leetcode_api_instance = initialize_leetcode_api_instance(
            leetcode_session, csrf_token
        )
        process_test_file(leetcode_api_instance, api_instance, test)
    elif submit:
        leetcode_api_instance = initialize_leetcode_api_instance(
            leetcode_session, csrf_token
        )
        process_submit_file(leetcode_api_instance, api_instance, submit)
    elif help:
        print_help_usage()
    else:
        print(
            "Please provide valid command line options. Use --help for usage information."
        )


if __name__ == "__main__":
    main()

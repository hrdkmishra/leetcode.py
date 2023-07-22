import json
import os
import time
import click
from bs4 import BeautifulSoup

from color import Colors
from config_setup import (
    save_credentials_to_config,
    load_credentials_from_config,
)

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
        "Referer": "https://leetcode.com"
    }

    data = {
        "operationName": data.get("operationName"),
        "query": data.get("query"),
        "variables": data.get("variables")
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
        "filters": filters
    }

    data = {
        "operationName": "problemsetQuestionList",
        "query": query,
        "variables": query_variables
    }

    api_response = execute_graphql_query(api_instance, data)

    if api_response and "data" in api_response and "problemsetQuestionList" in api_response["data"]:
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
        "variables": query_variables
    }

    api_response = execute_graphql_query(api_instance, data)

    if api_response and "data" in api_response and "question" in api_response["data"]:
        return api_response["data"]["question"]
    return None


LANG_EXTENSIONS = {
    'cpp': 'cpp',
    'java': 'java',
    'python': 'py',
    'python3': 'py',
    'c': 'c',
    'csharp': 'cs',
    'javascript': 'js',
    'ruby': 'rb',
    'swift': 'swift',
    'golang': 'go',
    'scala': 'scala',
    'kotlin': 'kt',
    'rust': 'rs',
    'php': 'php',
    'typescript': 'ts',
    'racket': 'rkt',
    'erlang': 'erl',
    'elixir': 'ex',
    'dart': 'dart'
}


def get_code_snippets(question_detail_data, lang_slug):
    code_snippets = question_detail_data.get("codeSnippets", [])
    return next((snippet['code'] for snippet in code_snippets if snippet['langSlug'] == lang_slug), None)


def write_code_snippet_to_file(question_detail_data, lang, title_slug):
    code = get_code_snippets(question_detail_data, lang)
    if code:
        lang_extension = LANG_EXTENSIONS.get(lang)
        if lang_extension:
            file_path = os.path.join("code_editor",
                                     f"{question_detail_data['questionFrontendId']}_{title_slug}.{lang_extension}")
            with open(file_path, "w") as file:
                file.write(code)
            print(f"Code snippet for {lang} has been written to {file_path}.")
        else:
            print(f"Language extension for {lang} is not available.")
    else:
        print(f"Code snippet for {lang} is not available for this question.")


def display_available_languages(question_detail_data):
    code_snippets = question_detail_data.get('codeSnippets', [])
    if code_snippets:
        print("Available Languages:")
        for index, snippet in enumerate(code_snippets):
            lang_slug = snippet.get('langSlug')
            lang_name = snippet.get('text') or lang_slug
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

        lang_input = input("Enter the index of the language you want to code: ").strip().lower()
        try:
            lang_index = int(lang_input)
            if 1 <= lang_index <= len(question_detail_data.get('codeSnippets', [])):
                selected_lang = question_detail_data['codeSnippets'][lang_index - 1]['langSlug']
                write_code_snippet_to_file(question_detail_data, selected_lang, title_slug)
            else:
                print("Invalid index. Please enter a valid index.")
        except ValueError:
            print("Invalid input. Please enter a valid index.")


def configuration():
    leetcode_session, csrf_token = load_credentials_from_config()
    if not leetcode_session or not csrf_token:
        leetcode_session = click.prompt("Enter your LeetCode session", type=str)
        csrf_token = click.prompt("Enter your CSRF token", type=str)
        save_credentials_to_config(leetcode_session, csrf_token)
    return leetcode_session, csrf_token


def get_title_slug_from_filename(filepath):
    base_name = os.path.basename(filepath)
    title_slug, _ = os.path.splitext(base_name)
    parts = title_slug.split('_')
    return "_".join(parts[1:])


def interpret_solution(api_instance, title_slug, payload):
    csrf_token, leetcode_session = api_instance

    api_url = f"https://leetcode.com/problems/{title_slug}/interpret_solution/"

    headers = {
        "User-Agent": "curl/8.0.1",
        "Host": "leetcode.com",
        "Accept": "*/*",
        "content-type": "application/json",
        "Origin": "https://leetcode.com",
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/problems/{title_slug}/",
        "x-csrftoken": csrf_token,
        "Cookie": f"LEETCODE_SESSION={leetcode_session};csrftoken={csrf_token};"
    }

    response = requests.post(api_url, json=payload, headers=headers)

    time.sleep(10)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Interpret solution request failed with status code {response.status_code}:")
        print(response.text)
        return None


@click.command()
@click.option("--config", is_flag=True, help="Enter credentials and save to config")
@click.option(
    "--question",
    "-q",
    type=str,
    default="",
    help="Specify the question ID, title, or range (e.g., 10:20)",
)
@click.option("--solve", "-s", type=str, default="",
              help="Specify the question title slug to solve (e.g., add-two-numbers)")
@click.option("--test", "-t", type=str, default="",
              help="Specify the filename containing the code and input for testing")
def main(config, question, solve, test):
    if config:
        leetcode_session, csrf_token = configuration()
    else:
        leetcode_session, csrf_token = load_credentials_from_config()

    api_instance = (csrf_token, leetcode_session)

    if solve:
        title_slug = get_question_data_by_id(api_instance, solve)[0].get("titleSlug")
        display_question_detail(api_instance, title_slug)
    elif question:
        question_data = get_question_data_by_id(api_instance, question)
        if question_data:
            sorted_question_data = sorted(question_data, key=lambda x: int(x["frontendQuestionId"]))
            for question_item in sorted_question_data:
                print_question_data(question_item)
        else:
            print(f"Question with ID or title '{question}' not found.")
    elif test:
        print(f"Test file: {test}")
        title_slug = get_title_slug_from_filename(test)
        print(f"Title slug: {title_slug}")
        question_detail_data = get_question_detail(api_instance, title_slug)
        if question_detail_data:
            question_id = question_detail_data.get("questionId")
            print(f"Question ID: {question_id}")
            sample_test_case = question_detail_data.get("sampleTestCase")
            print(f"Sample Test Case: {sample_test_case}")

            with open(test, "r") as file:
                code = file.read()

            payload = {
                "lang": "python3",
                "question_id": question_id,
                "typed_code": code,
                "data_input": sample_test_case
            }

            json_payload = json.dumps(payload, indent=4)  # Convert payload to JSON string
            print(json_payload)

            result = interpret_solution(api_instance, title_slug, json_payload)
            if result and "interpret_id" in result:
                interpret_id = result["interpret_id"]
                print(f"Interpret ID: {interpret_id}")
            else:
                print("Interpret solution failed.")
        else:
            print(f"Question with title slug '{title_slug}' not found.")


if __name__ == "__main__":
    main() #tesr

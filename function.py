import json
import leetcode
from bs4 import BeautifulSoup

from color import Colors


# configuration
def configure_api_instance(csrf_token, leetcode_session):
    configuration = leetcode.Configuration()
    configuration.api_key["x-csrftoken"] = csrf_token
    configuration.api_key["csrftoken"] = csrf_token
    configuration.api_key["LEETCODE_SESSION"] = leetcode_session
    configuration.api_key["Referer"] = "https://leetcode.com"
    configuration.debug = False

    api_instance = leetcode.DefaultApi(leetcode.ApiClient(configuration))
    return api_instance


def process_api_response(api_response):
    if api_response.data:
        pass
    else:
        print("No data found in the API response.")


def read_json_file(file_path):
    with open(file_path, "r") as json_file:
        return json.load(json_file)


# for get question data by question id
def get_question_data_by_id(json_data, q):
    questions = (
        json_data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
    )

    for question in questions:
        if q == question.get("frontendQuestionId"):
            return question
    return None


# for graphql excution
def execute_graphql_query(api_instance, graphql_query, query_variables):
    graphql_request = leetcode.GraphqlQuery(query=graphql_query, variables=query_variables)
    api_response = api_instance.graphql_post(body=graphql_request)
    return api_response


# this is for print the question list in order
def print_question_data(question):
    question_id = question.get("frontendQuestionId")
    title = question.get("title")
    difficulty = question.get("difficulty")
    ac_rate = question.get("acRate")

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

    # Align and pad the title and difficulty columns
    title_formatted = title.ljust(title_width)[:title_width]
    difficulty_formatted = (
        f"{difficulty_color}{difficulty.ljust(difficulty_width)}{Colors.RESET}"
    )

    print(
        f"[{str(question_id).rjust(3)}]  {title_formatted}  {difficulty_formatted}  ({ac_rate:.2f}%)"
    )


# for --solve
def get_question_content(api_instance, title_slug):
    graphql_query = "query questionContent($titleSlug: String!) { question(titleSlug: $titleSlug) { content } }"
    query_variables = {"titleSlug": title_slug}
    api_response = execute_graphql_query(api_instance, graphql_query, query_variables)
    content = api_response.data.question.content
    return content


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text()
    return plain_text


def fetch_code_content(api_instance, title_slug):
    graphql_query = """
    query questionEditorData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        codeSnippets {
          lang
          langSlug
          code
        }
      }
    }
    """

    query_variables = {
        "titleSlug": title_slug
    }

    api_response = execute_graphql_query(api_instance, graphql_query, query_variables)

    # if api_response and api_response.data and api_response.data.question:
    #     question_data = api_response.data.question
    #
    #     if question_data.code_snippets:
    #         code_snippets = question_data.code_snippets
    #         python3_snippet = next(
    #             (snippet for snippet in code_snippets if snippet.lang_slug == "python3"),
    #             None
    #         )
    #
    #         if python3_snippet:
    #             return python3_snippet

    python3_snippet = next(
                (snippet for snippet in api_response.data.question.code_snippets if snippet.lang_slug == "python3"),
                None
            )
    if python3_snippet:
        return python3_snippet

    return None
